"""Enrollment business logic: validation -> detection -> exactly-one-face -> embedding -> persist."""
from __future__ import annotations

import uuid

from ml.preprocessing import decode_image
from app.repositories.identity_repository import IdentityRepository
from app.services.ml_pipeline import get_pipeline, MODEL_VERSION


class EnrollmentService:
    def __init__(self, repository: IdentityRepository):
        self._repository = repository

    def enroll(self, display_name: str, image_bytes: bytes):
        image = decode_image(image_bytes)
        pipeline = get_pipeline()
        result = pipeline.process(image)

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
