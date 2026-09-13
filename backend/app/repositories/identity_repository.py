"""Repository boundary for identity/embedding persistence.

Services depend on this interface, not on SQLAlchemy directly, so storage can
be replaced without rewriting the API/service layer (blueprint section 9).
"""
from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass

import numpy as np
from sqlalchemy.orm import Session

from app.models.orm import FaceEmbedding, Identity


@dataclass
class EnrolledSample:
    identity_id: str
    embedding: np.ndarray


class IdentityRepository(ABC):
    @abstractmethod
    def create_identity(self, display_name: str) -> Identity: ...

    @abstractmethod
    def get_identity(self, identity_id: uuid.UUID) -> Identity | None: ...

    @abstractmethod
    def list_identities(self) -> list[Identity]: ...

    @abstractmethod
    def add_embedding(self, identity_id: uuid.UUID, embedding: np.ndarray, model_version: str) -> FaceEmbedding: ...

    @abstractmethod
    def get_all_samples(self) -> list[EnrolledSample]: ...

    @abstractmethod
    def delete_identity(self, identity_id: uuid.UUID) -> bool: ...


class SqlAlchemyIdentityRepository(IdentityRepository):
    def __init__(self, db: Session):
        self._db = db

    def create_identity(self, display_name: str) -> Identity:
        identity = Identity(display_name=display_name)
        self._db.add(identity)
        self._db.commit()
        self._db.refresh(identity)
        return identity

    def get_identity(self, identity_id: uuid.UUID) -> Identity | None:
        return self._db.get(Identity, identity_id)

    def list_identities(self) -> list[Identity]:
        return list(self._db.query(Identity).order_by(Identity.created_at).all())

    def add_embedding(self, identity_id: uuid.UUID, embedding: np.ndarray, model_version: str) -> FaceEmbedding:
        record = FaceEmbedding(
            identity_id=identity_id,
            embedding_vector=embedding.astype(np.float32).tobytes(),
            model_version=model_version,
        )
        self._db.add(record)
        self._db.commit()
        self._db.refresh(record)
        return record

    def get_all_samples(self) -> list[EnrolledSample]:
        rows = self._db.query(FaceEmbedding).all()
        return [
            EnrolledSample(
                identity_id=str(row.identity_id),
                embedding=np.frombuffer(row.embedding_vector, dtype=np.float32),
            )
            for row in rows
        ]

    def delete_identity(self, identity_id: uuid.UUID) -> bool:
        identity = self.get_identity(identity_id)
        if identity is None:
            return False
        self._db.delete(identity)
        self._db.commit()
        return True
