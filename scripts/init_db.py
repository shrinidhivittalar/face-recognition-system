"""Creates all tables in the configured PostgreSQL database.

Usage: python scripts/init_db.py
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.models.database import Base, get_engine
from app.models import orm  # noqa: F401  (registers models on Base.metadata)


def main() -> None:
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("Database schema created.")


if __name__ == "__main__":
    main()
