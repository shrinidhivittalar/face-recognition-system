"""Enrollment business logic: validation -> detection -> exactly-one-face -> embedding -> persist."""
from __future__ import annotations

import uuid

from ml.matching import best_match
from ml.preprocessing import decode_image
from app.core.config import get_settings
from app.repositories.identity_repository import IdentityRepository
from app.services.ml_pipeline import get_pipeline, MODEL_VERSION


class DuplicateIdentityError(Exception):
    """Raised when a new enrollment matches someone already enrolled.

    Carries no identifying detail on purpose. There is no authorization layer
    on enrollment, so naming the existing identity would let an anonymous
    caller confirm whether a given person is enrolled by submitting a photo —
    the same disclosure the Unknown path already refuses to make.
    """


class EnrollmentService:
    def __init__(self, repository: IdentityRepository):
        self._repository = repository

    def enroll(self, display_name: str, image_bytes: bytes):
        image = decode_image(image_bytes)
        pipeline = get_pipeline()
        result = pipeline.process(image)

        # Reject before creating anything, so a refused enrollment leaves no
        # partial identity behind. Uses the stricter duplicate threshold, not
        # the identification one.
        existing = [(s.identity_id, s.embedding) for s in self._repository.get_all_samples()]
        duplicate = best_match(
            result.embedding, existing, threshold=get_settings().duplicate_threshold
        )
        if duplicate.outcome == "known":
            raise DuplicateIdentityError()

        identity = self._repository.create_identity(display_name=display_name)
        self._repository.add_embedding(identity.id, result.embedding, MODEL_VERSION)

        return identity, result.detection_score

    def add_sample(self, identity_id: uuid.UUID, image_bytes: bytes):
        identity = self._repository.get_identity(identity_id)
        if identity is None:
            return None, None

        image = decode_image(image_bytes)
        pipeline = get_pipeline()
        result = pipeline.process(image)

        sample = self._repository.add_embedding(identity_id, result.embedding, MODEL_VERSION)
        return sample, result.detection_score
