import os
from contextlib import contextmanager

import psycopg2
from psycopg2.extras import RealDictCursor


def _pg_config() -> dict:
    return {
        "host": os.getenv("PG_HOST", "postgres"),
        "port": int(os.getenv("PG_PORT", "5432")),
        "dbname": os.getenv("PG_DB", "pqr_db"),
        "user": os.getenv("PG_USER", "pqr_user"),
        "password": os.getenv("PG_PASSWORD", "pqr_password"),
    }


def public_pg_config() -> dict:
    config = _pg_config()
    return {
        "host": config["host"],
        "port": config["port"],
        "database": config["dbname"],
        "user": config["user"],
    }


@contextmanager
def pg_connection():
    conn = psycopg2.connect(**_pg_config())
    try:
        yield conn
    finally:
        conn.close()


@contextmanager
def pg_cursor(dict_rows: bool = True):
    with pg_connection() as conn:
        cursor_factory = RealDictCursor if dict_rows else None
        cur = conn.cursor(cursor_factory=cursor_factory)
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()
