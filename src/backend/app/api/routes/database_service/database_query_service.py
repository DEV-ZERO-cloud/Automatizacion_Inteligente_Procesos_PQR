import re

from fastapi import APIRouter, HTTPException, Query
from psycopg2 import sql

from app.core.postgres import pg_cursor, public_pg_config
from app.core.responses import ok_response

router = APIRouter(prefix="/db", tags=["Database Diagnostics"])

TABLE_NAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


def _public_tables() -> list[str]:
    with pg_cursor() as cur:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
            ORDER BY table_name
            """
        )
        rows = cur.fetchall()
    return [row["table_name"] for row in rows]


@router.get("/health")
def db_health():
    try:
        with pg_cursor() as cur:
            cur.execute(
                """
                SELECT
                    NOW() AS server_time,
                    current_database() AS database_name,
                    current_user AS current_user
                """
            )
            row = cur.fetchone()

        return ok_response(
            data={
                "status": "ok",
                "connection": row,
                "config": public_pg_config(),
            },
            message="Conexión a PostgreSQL verificada",
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail="PostgreSQL no disponible")


@router.get("/tables")
def db_tables():
    try:
        table_names = _public_tables()

        stats = []
        with pg_cursor() as cur:
            for table_name in table_names:
                cur.execute(
                    sql.SQL("SELECT COUNT(*) AS total FROM {}")
                    .format(sql.Identifier(table_name))
                )
                count_row = cur.fetchone()
                stats.append({"table": table_name, "rows": int(count_row["total"])})

        return ok_response(data=stats, message="Tablas consultadas")
    except Exception as exc:
        raise HTTPException(status_code=500, detail="No se pudo consultar tablas")


@router.get("/tables/{table_name}")
def db_table_rows(
    table_name: str,
    limit: int = Query(default=20, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    if not TABLE_NAME_PATTERN.match(table_name):
        raise HTTPException(status_code=400, detail="Nombre de tabla inválido")

    allowed_tables = set(_public_tables())
    if table_name not in allowed_tables:
        raise HTTPException(status_code=404, detail="Tabla no encontrada")

    try:
        with pg_cursor() as cur:
            cur.execute(
                sql.SQL("SELECT * FROM {} LIMIT %s OFFSET %s")
                .format(sql.Identifier(table_name)),
                (limit, offset),
            )
            rows = cur.fetchall()

            cur.execute(
                sql.SQL("SELECT COUNT(*) AS total FROM {}")
                .format(sql.Identifier(table_name))
            )
            total_row = cur.fetchone()

        return ok_response(
            data={
                "table": table_name,
                "total": int(total_row["total"]),
                "limit": limit,
                "offset": offset,
                "rows": rows,
            },
            message="Filas de tabla consultadas",
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail="No se pudo consultar la tabla")


@router.get("/config")
def db_config():
    return ok_response(data=public_pg_config(), message="Configuración pública de DB")
