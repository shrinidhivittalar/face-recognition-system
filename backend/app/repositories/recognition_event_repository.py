"""Repository for operational/audit recognition events (no raw images stored)."""
from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models.orm import RecognitionEvent


class RecognitionEventRepository:
    def __init__(self, db: Session):
        self._db = db

    def log_event(
        self,
        request_id: uuid.UUID,
        outcome: str,
        candidate_identity_id: uuid.UUID | None = None,
        score: float | None = None,
    ) -> RecognitionEvent:
        event = RecognitionEvent(
            request_id=request_id,
            outcome=outcome,
            candidate_identity_id=candidate_identity_id,
            score=score,
        )
        self._db.add(event)
        self._db.commit()
        self._db.refresh(event)
        return event
