import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.main import app
from app.models.database import Base, get_engine
from app.models import orm  # noqa: F401


@pytest.fixture(scope="session", autouse=True)
def _create_schema():
    engine = get_engine()
    Base.metadata.create_all(engine)
    yield


@pytest.fixture(autouse=True)
def _clean_tables():
    """Truncate all tables between tests so each test starts from an empty DB."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE recognition_events, face_embeddings, identities CASCADE"))
    yield


@pytest.fixture
def client():
    return TestClient(app)
