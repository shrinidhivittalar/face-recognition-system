"""Process-wide singleton for the ML pipeline (model loading is expensive)."""
from __future__ import annotations

from functools import lru_cache

from ml.model_adapter import FaceRecognitionPipeline
from app.core.config import get_settings

MODEL_VERSION = "yunet_2023mar+sface_2021dec"


@lru_cache
def get_pipeline() -> FaceRecognitionPipeline:
    settings = get_settings()
    return FaceRecognitionPipeline(
        detector_model_path=settings.yunet_model_path,
        embedder_model_path=settings.sface_model_path,
    )
