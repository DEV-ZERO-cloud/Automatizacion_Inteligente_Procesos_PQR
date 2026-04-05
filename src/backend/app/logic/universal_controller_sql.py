import logging
import os
from typing import Any, List, Optional

import psycopg2

from app.core.config import settings

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class UniversalController:
    """
    Controlador universal para operaciones CRUD sobre PostgreSQL.
    Sigue el patrón Repository: tablas con __entity_name__.
    """

    def __init__(self):
        try:
            password = os.getenv("PASSWORD", settings.PASSWORD)
            if not password:
                raise ValueError("La variable PASSWORD no está definida en el entorno.")

            self.conn = psycopg2.connect(**settings.db_config)
            self.conn.autocommit = False
            self.cursor = self.conn.cursor()
            logger.info("Conexión a PostgreSQL establecida correctamente.")
        except psycopg2.Error as exc:
            raise ConnectionError(f"Error de conexión a la base de datos: {exc}") from exc

    # ── Utilidades internas ────────────────────────────────────────────────────

    def _get_table_name(self, obj: Any) -> str:
        """Obtiene el nombre de la tabla desde __entity_name__."""
        if hasattr(obj, "__entity_name__"):
            return obj.__entity_name__
        if hasattr(obj.__class__, "__entity_name__"):
            return obj.__class__.__entity_name__
        raise ValueError("El objeto no tiene definido '__entity_name__'.")

    def _row_to_dict(self, row) -> dict:
        """Convierte una fila de cursor en diccionario."""
        return dict(zip([col[0] for col in self.cursor.description], row))

    # ── CRUD genérico ──────────────────────────────────────────────────────────

    def get_all(self, cls: Any) -> List[Any]:
        """Retorna todos los registros de la tabla asociada a cls."""
        table = cls.__entity_name__
        try:
            self.cursor.execute(f"SELECT * FROM {table}")
            rows = self.cursor.fetchall()
            return [cls.from_dict(self._row_to_dict(r)) for r in rows]
        except Exception as exc:
            logger.error("Error en get_all(%s): %s", table, exc)
            raise

    def get_by_id(self, cls: Any, record_id: int) -> Optional[Any]:
        """Retorna un registro por su ID."""
        table = cls.__entity_name__
        try:
            self.cursor.execute(f"SELECT * FROM {table} WHERE ID = %s", (record_id,))
            row = self.cursor.fetchone()
            return cls.from_dict(self._row_to_dict(row)) if row else None
        except Exception as exc:
            logger.error("Error en get_by_id(%s, %s): %s", table, record_id, exc)
            raise

    def get_by_column(self, cls: Any, column: str, value: Any) -> Optional[Any]:
        """Retorna el primer registro que coincida con column=value."""
        table = cls.__entity_name__
        try:
            self.cursor.execute(f"SELECT * FROM {table} WHERE {column} = %s", (value,))
            row = self.cursor.fetchone()
            return cls.from_dict(self._row_to_dict(row)) if row else None
        except Exception as exc:
            logger.error("Error en get_by_column(%s.%s=%s): %s", table, column, value, exc)
            raise

    def add(self, obj: Any) -> Any:
        """Inserta un nuevo registro en la tabla."""
        table = self._get_table_name(obj)
        data = obj.to_dict()

        # Eliminar ID si es None (autoincremental)
        if "ID" in data and data["ID"] is None:
            del data["ID"]

        columns = ", ".join(data.keys())
        placeholders = ", ".join(["%s" for _ in data])
        sql = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"

        try:
            self.cursor.execute(sql, tuple(data.values()))
            self.conn.commit()
            logger.info("Registro insertado en %s.", table)
            return obj
        except Exception as exc:
            self.conn.rollback()
            logger.error("Error en add(%s): %s", table, exc)
            raise

    def update(self, obj: Any) -> Any:
        """Actualiza un registro existente identificado por ID."""
        table = self._get_table_name(obj)
        data = obj.to_dict()

        if "ID" not in data or data["ID"] is None:
            raise ValueError("El objeto debe tener un campo 'ID' válido para ser actualizado.")

        set_clause = ", ".join(f"{k} = %s" for k in data if k != "ID")
        sql = f"UPDATE {table} SET {set_clause} WHERE ID = %s"
        values = [v for k, v in data.items() if k != "ID"] + [data["ID"]]

        try:
            self.cursor.execute(sql, values)
            self.conn.commit()
            logger.info("Registro ID=%s actualizado en %s.", data["ID"], table)
            return obj
        except Exception as exc:
            self.conn.rollback()
            logger.error("Error en update(%s): %s", table, exc)
            raise

    def delete(self, obj: Any) -> bool:
        """Elimina un registro por su ID."""
        table = self._get_table_name(obj)
        data = obj.to_dict()

        if "ID" not in data or data["ID"] is None:
            raise ValueError("El objeto debe tener un campo 'ID' válido para ser eliminado.")

        try:
            self.cursor.execute(f"DELETE FROM {table} WHERE ID = %s", (data["ID"],))
            self.conn.commit()
            logger.info("Registro ID=%s eliminado de %s.", data["ID"], table)
            return True
        except Exception as exc:
            self.conn.rollback()
            logger.error("Error en delete(%s): %s", table, exc)
            raise

    # ── Consultas de reportes ──────────────────────────────────────────────────

    def get_dashboard_summary(self) -> dict:
        """Retorna totales de PQR: total, pendientes y resueltas."""
        try:
            self.cursor.execute("""
                SELECT
                    COUNT(*) AS total_pqrs,
                    SUM(CASE WHEN estado = 'pendiente' THEN 1 ELSE 0 END) AS pendientes,
                    SUM(CASE WHEN estado = 'resuelta'  THEN 1 ELSE 0 END) AS resueltas
                FROM pqrs
            """)
            row = self.cursor.fetchone()
            return {
                "total_pqrs": row[0] or 0,
                "pendientes": row[1] or 0,
                "resueltas": row[2] or 0,
            }
        except Exception as exc:
            logger.error("Error en get_dashboard_summary: %s", exc)
            raise

    def get_pqrs_by_category(self) -> List[dict]:
        """Retorna cantidad de PQR agrupadas por categoría."""
        try:
            self.cursor.execute("""
                SELECT categoria, COUNT(*) AS cantidad
                FROM pqrs
                GROUP BY categoria
                ORDER BY cantidad DESC
            """)
            rows = self.cursor.fetchall()
            return [{"categoria": r[0], "cantidad": r[1]} for r in rows]
        except Exception as exc:
            logger.error("Error en get_pqrs_by_category: %s", exc)
            raise

    def get_pqrs_by_priority(self) -> List[dict]:
        """Retorna cantidad de PQR agrupadas por prioridad."""
        try:
            self.cursor.execute("""
                SELECT prioridad, COUNT(*) AS cantidad
                FROM pqrs
                GROUP BY prioridad
                ORDER BY cantidad DESC
            """)
            rows = self.cursor.fetchall()
            return [{"prioridad": r[0], "cantidad": r[1]} for r in rows]
        except Exception as exc:
            logger.error("Error en get_pqrs_by_priority: %s", exc)
            raise

    def get_pqrs_by_area(self) -> List[dict]:
        """Retorna cantidad de PQR agrupadas por área organizacional."""
        try:
            self.cursor.execute("""
                SELECT a.nombre AS area, COUNT(p.id) AS cantidad
                FROM pqrs p
                JOIN areas a ON p.area_id = a.id
                GROUP BY a.nombre
                ORDER BY cantidad DESC
            """)
            rows = self.cursor.fetchall()
            return [{"area": r[0], "cantidad": r[1]} for r in rows]
        except Exception as exc:
            logger.error("Error en get_pqrs_by_area: %s", exc)
            raise
