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
def _reset_rate_limiters():
    """Clear per-IP rate-limit state between tests.

    The limiters are module-level and every test shares one client address, so
    without this the suite trips the 10-enrollments-per-minute limit partway
    through and later tests fail with 429 rather than what they assert.
    """
    from app.api.routes import enroll as enroll_routes
    from app.api.routes import identify as identify_routes

    enroll_routes._limiter._hits.clear()
    identify_routes._limiter._hits.clear()
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
