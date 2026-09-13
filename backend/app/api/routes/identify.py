from __future__ import annotations

from fastapi import APIRouter, Depends, File, Request, UploadFile

from app.api.dependencies import get_identification_service
from app.core.config import get_settings
from app.core.rate_limit import RateLimiter, client_key
from app.schemas.recognition import IdentifyResponse
from app.services.identification_service import IdentificationService

router = APIRouter(prefix="/api/v1", tags=["identification"])

_limiter = RateLimiter(max_requests=get_settings().rate_limit_identify_per_minute)


@router.post("/identify", response_model=IdentifyResponse)
async def identify(
    request: Request,
    image: UploadFile = File(...),
    service: IdentificationService = Depends(get_identification_service),
) -> IdentifyResponse:
    _limiter.check(client_key(request))

    image_bytes = await image.read()
    result = service.identify(image_bytes)

    return IdentifyResponse(
        outcome=result.outcome,
        identity_id=result.identity_id,
        display_name=result.display_name,
    )
