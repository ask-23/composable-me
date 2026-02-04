import importlib


def test_database_url_can_be_overridden_by_env(monkeypatch):
    """Database URL should be configurable via environment."""
    monkeypatch.setenv("HYDRA_DATABASE_URL", "postgresql://override:override@localhost:5432/override")
    import web.backend.db.connection as connection

    importlib.reload(connection)

    assert connection.DATABASE_URL == "postgresql://override:override@localhost:5432/override"
