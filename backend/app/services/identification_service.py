"""Identification business logic: validation -> detection -> embedding -> matching -> threshold gate."""
from __future__ import annotations

import uuid
from dataclasses import dataclass

from ml.preprocessing import decode_image
from ml.matching import best_match
from app.repositories.identity_repository import IdentityRepository
from app.repositories.recognition_event_repository import RecognitionEventRepository
from app.services.ml_pipeline import get_pipeline
from app.core.config import get_settings


@dataclass
class IdentificationResult:
    outcome: str  # "known" or "unknown"
    identity_id: uuid.UUID | None = None
    display_name: str | None = None


class IdentificationService:
    def __init__(self, repository: IdentityRepository, event_repository: RecognitionEventRepository):
        self._repository = repository
        self._event_repository = event_repository

    def identify(self, image_bytes: bytes) -> IdentificationResult:
        settings = get_settings()
        image = decode_image(image_bytes)
        pipeline = get_pipeline()
        result = pipeline.process(image)

        samples = self._repository.get_all_samples()
        enrolled = [(s.identity_id, s.embedding) for s in samples]

        match = best_match(result.embedding, enrolled, threshold=settings.similarity_threshold)
        candidate_uuid = uuid.UUID(match.identity_id) if match.identity_id else None

        self._event_repository.log_event(
            request_id=uuid.uuid4(),
            outcome=match.outcome,
            candidate_identity_id=candidate_uuid,
            score=match.score,
        )

        if match.outcome == "unknown":
            return IdentificationResult(outcome="unknown")

        identity = self._repository.get_identity(candidate_uuid)
        return IdentificationResult(
            outcome="known",
            identity_id=identity.id,
            display_name=identity.display_name,
        )
