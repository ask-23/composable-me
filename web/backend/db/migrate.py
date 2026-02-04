"""Lightweight SQL migration runner for Hydra."""

from __future__ import annotations

from pathlib import Path

from web.backend.db.connection import get_conn


MIGRATIONS_DIR = Path(__file__).parent / "migrations"


def _ensure_schema_table(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            id SERIAL PRIMARY KEY,
            filename TEXT NOT NULL UNIQUE,
            applied_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )
        """
    )


def _list_migrations() -> list[Path]:
    return sorted(p for p in MIGRATIONS_DIR.glob("*.sql") if p.is_file())


def apply_migrations() -> None:
    """Apply any pending SQL migrations in order."""
    migrations = _list_migrations()
    if not migrations:
        return

    with get_conn() as conn:
        _ensure_schema_table(conn)
        conn.commit()
        applied = {row["filename"] for row in conn.execute("SELECT filename FROM schema_migrations")}

        for migration in migrations:
            if migration.name in applied:
                continue

            sql = migration.read_text()
            with conn.transaction():
                conn.execute(sql)
                conn.execute(
                    "INSERT INTO schema_migrations (filename) VALUES (%s)",
                    (migration.name,),
                )


def main() -> None:
    apply_migrations()


if __name__ == "__main__":
    main()
