import os
import importlib.util
from pathlib import Path


def test_job_queue_db_path_can_be_overridden_by_env(tmp_path, monkeypatch):
    """
    Regression: allow overriding the SQLite DB path so real-input runs don't
    persist sensitive data into the repo by default.

    This test loads a fresh copy of the module under a temporary name so it
    doesn't interfere with the already-imported job_queue module used elsewhere.
    """

    db_path = tmp_path / "hydra-jobs.db"
    monkeypatch.setenv("HYDRA_DB_PATH", str(db_path))

    module_path = Path(__file__).resolve().parents[3] / "web" / "backend" / "services" / "job_queue.py"
    spec = importlib.util.spec_from_file_location("job_queue_env_test", module_path)
    assert spec and spec.loader

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]

    assert Path(module.DB_PATH) == db_path
    assert db_path.exists()

