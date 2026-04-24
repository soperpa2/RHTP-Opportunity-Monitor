from __future__ import annotations
from contextlib import contextmanager
from typing import Any, Iterable
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool
from .config import get_settings

_pool: ConnectionPool | None = None

def get_pool() -> ConnectionPool:
    global _pool
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured.")
    if _pool is None:
        _pool = ConnectionPool(settings.database_url, kwargs={"row_factory": dict_row}, min_size=1, max_size=5)
    return _pool

@contextmanager
def get_conn():
    with get_pool().connection() as conn:
        yield conn

def fetch_all(sql: str, params: Iterable[Any] | None = None) -> list[dict[str, Any]]:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return list(cur.fetchall())

def fetch_one(sql: str, params: Iterable[Any] | None = None) -> dict[str, Any] | None:
    rows = fetch_all(sql, params)
    return rows[0] if rows else None

def execute(sql: str, params: Iterable[Any] | None = None) -> None:
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
        conn.commit()

def init_schema(schema_path: str = "sql/schema.sql") -> None:
    with open(schema_path, "r", encoding="utf-8") as f:
        sql = f.read()
    with get_conn() as conn:
        conn.execute(sql)
        conn.commit()
