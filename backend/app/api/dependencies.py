from __future__ import annotations

from fastapi import Depends
from sqlalchemy.orm import Session

from app.models.database import get_db
from app.repositories.identity_repository import IdentityRepository, SqlAlchemyIdentityRepository
from app.repositories.recognition_event_repository import RecognitionEventRepository
from app.services.enrollment_service import EnrollmentService
from app.services.identification_service import IdentificationService


def get_identity_repository(db: Session = Depends(get_db)) -> IdentityRepository:
    return SqlAlchemyIdentityRepository(db)


def get_event_repository(db: Session = Depends(get_db)) -> RecognitionEventRepository:
    return RecognitionEventRepository(db)


def get_enrollment_service(
    repository: IdentityRepository = Depends(get_identity_repository),
) -> EnrollmentService:
    return EnrollmentService(repository)


def get_identification_service(
    repository: IdentityRepository = Depends(get_identity_repository),
    event_repository: RecognitionEventRepository = Depends(get_event_repository),
) -> IdentificationService:
    return IdentificationService(repository, event_repository)
