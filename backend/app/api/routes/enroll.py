from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from app.api.dependencies import get_enrollment_service
from app.core.config import get_settings
from app.core.rate_limit import RateLimiter, client_key
from app.schemas.recognition import EnrollResponse, SampleAddedResponse
from app.services.enrollment_service import EnrollmentService

router = APIRouter(prefix="/api/v1", tags=["enrollment"])

_limiter = RateLimiter(max_requests=get_settings().rate_limit_enroll_per_minute)


@router.post("/enroll", response_model=EnrollResponse)
async def enroll(
    request: Request,
    display_name: str = Form(..., min_length=1, max_length=255),
    image: UploadFile = File(...),
    service: EnrollmentService = Depends(get_enrollment_service),
) -> EnrollResponse:
    _limiter.check(client_key(request))

    image_bytes = await image.read()
    identity, detection_score = service.enroll(display_name=display_name.strip(), image_bytes=image_bytes)

    return EnrollResponse(
        identity_id=identity.id,
        display_name=identity.display_name,
        detection_score=detection_score,
    )


@router.post("/identities/{identity_id}/samples", response_model=SampleAddedResponse)
async def add_sample(
    identity_id: uuid.UUID,
    request: Request,
    image: UploadFile = File(...),
    service: EnrollmentService = Depends(get_enrollment_service),
) -> SampleAddedResponse:
    _limiter.check(client_key(request))

    image_bytes = await image.read()
    sample, detection_score = service.add_sample(identity_id, image_bytes)

    if sample is None:
        raise HTTPException(status_code=404, detail="Identity not found.")

    return SampleAddedResponse(
        identity_id=identity_id,
        sample_id=sample.id,
        detection_score=detection_score,
    )
