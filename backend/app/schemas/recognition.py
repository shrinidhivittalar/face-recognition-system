"""Pydantic response/request schemas for the recognition API."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class IdentityOut(BaseModel):
    id: UUID
    display_name: str
    created_at: datetime
    sample_count: int

    model_config = {"from_attributes": True}


class EnrollResponse(BaseModel):
    identity_id: UUID
    display_name: str
    detection_score: float


class SampleAddedResponse(BaseModel):
    identity_id: UUID
    sample_id: UUID
    detection_score: float


class IdentifyResponse(BaseModel):
    outcome: str  # "known" or "unknown"
    identity_id: UUID | None = None
    display_name: str | None = None


class ErrorResponse(BaseModel):
    error: str
    message: str


class HealthResponse(BaseModel):
    status: str
    database: str
    model: str
