import importlib


def test_database_url_can_be_overridden_by_env(monkeypatch):
    """Database URL should be configurable via environment."""
    import web.backend.db.connection as connection

    original_url = connection.DATABASE_URL

    monkeypatch.setenv("HYDRA_DATABASE_URL", "postgresql://override:override@localhost:5432/override")
    importlib.reload(connection)

    assert connection.DATABASE_URL == "postgresql://override:override@localhost:5432/override"

    # Restore original URL to prevent pollution of subsequent tests
    monkeypatch.setenv("HYDRA_DATABASE_URL", original_url)
    importlib.reload(connection)
