"""Application configuration loaded from environment variables (.env)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"), env_file_encoding="utf-8", extra="ignore"
    )

    database_url: str = "postgresql+psycopg2://face_reco:face_reco@localhost:5432/face_reco"

    # Empirically calibrated via scripts/run_evaluation.py on LFW verification
    # pairs (far_ceiling method, target FAR <= 1%); see docs/EVALUATION.md and
    # data/evaluation_results.json for full provenance. Held-out test: FAR 0.86%,
    # FRR 0.54%, accuracy 99.30%.
    similarity_threshold: float = 0.2975

    # Separate, stricter gate for "is this new enrollment already an enrolled
    # person?". Deliberately NOT the identification threshold: there, a false
    # accept mislabels someone; here it BLOCKS a legitimate new user from
    # enrolling at all. Calibrated by scripts/run_duplicate_threshold_experiment.py
    # as the lowest threshold with zero false blocks on the calibration split.
    # Held-out: 0.215% wrongly blocked (2/931) vs 0.859% (8/931) at 0.2975,
    # while still catching 99.25% of true duplicates.
    # Evidence: data/duplicate_threshold_results.json
    duplicate_threshold: float = 0.3426

    cors_allowed_origins: list[str] = ["http://localhost:5173", "http://localhost:3000"]

    rate_limit_identify_per_minute: int = 20
    rate_limit_enroll_per_minute: int = 10

    max_upload_bytes: int = 8 * 1024 * 1024

    yunet_model_path: str = str(REPO_ROOT / "models" / "face_detection_yunet_2023mar.onnx")
    sface_model_path: str = str(REPO_ROOT / "models" / "face_recognition_sface_2021dec.onnx")

    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    return Settings()
