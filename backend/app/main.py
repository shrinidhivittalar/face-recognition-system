from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import enroll, health, identify, identities
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from ml.preprocessing import InvalidImageError
from ml.model_adapter import NoFaceDetectedError, MultipleFacesDetectedError

settings = get_settings()
configure_logging(settings.log_level)
logger = get_logger(__name__)

app = FastAPI(title="Face Recognition Identification System", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(enroll.router)
app.include_router(identify.router)
app.include_router(identities.router)


# Edge-case contract (blueprint section 11): actionable, safe messages only.
# No stack traces, SQL errors, or internal details ever reach the client.

_INVALID_IMAGE_MESSAGES = {
    "empty_file": "No image was received. Please try again.",
    "file_too_large": "The image file is too large.",
    "unsupported_or_corrupt_image": "Unsupported or corrupt image. Please upload a valid photo.",
    "image_too_small": "The image is too small. Please upload a higher-resolution photo.",
    "image_too_large": "The image dimensions are too large.",
}


@app.exception_handler(NoFaceDetectedError)
async def handle_no_face(request: Request, exc: NoFaceDetectedError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": "no_face", "message": "No face detected. Adjust your position and try again."},
    )


@app.exception_handler(MultipleFacesDetectedError)
async def handle_multiple_faces(request: Request, exc: MultipleFacesDetectedError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={"error": "multiple_faces", "message": "Please ensure only one face is visible."},
    )


@app.exception_handler(InvalidImageError)
async def handle_invalid_image(request: Request, exc: InvalidImageError) -> JSONResponse:
    reason = str(exc)
    message = _INVALID_IMAGE_MESSAGES.get(reason, "Invalid image. Please try again.")
    return JSONResponse(status_code=400, content={"error": reason, "message": message})


@app.exception_handler(Exception)
async def handle_unexpected(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unhandled_exception path=%s type=%s", request.url.path, type(exc).__name__)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_error", "message": "Something went wrong. Please try again later."},
    )
