"""Postgres connection helpers for Hydra."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row


DEFAULT_DATABASE_URL = "postgresql://hydra:hydra@localhost:5432/hydra"
DATABASE_URL = os.environ.get("HYDRA_DATABASE_URL", os.environ.get("DATABASE_URL", DEFAULT_DATABASE_URL))


@contextmanager
def get_conn() -> Iterator[psycopg.Connection]:
    """Yield a Postgres connection with dict row mapping."""
    conn = psycopg.connect(DATABASE_URL, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()
