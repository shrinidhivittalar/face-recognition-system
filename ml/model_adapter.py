"""Single entry point for the detection -> exactly-one-face -> embedding pipeline.

Isolating this adapter means the API/service layer never talks to YuNet/SFace
directly, so the underlying model could be swapped without touching callers
(blueprint section 5).
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import numpy as np

from ml.detector import FaceDetector
from ml.embedding import FaceEmbedder, normalize

DEFAULT_MODELS_DIR = Path(__file__).resolve().parent.parent / "models"
DEFAULT_YUNET_PATH = DEFAULT_MODELS_DIR / "face_detection_yunet_2023mar.onnx"
DEFAULT_SFACE_PATH = DEFAULT_MODELS_DIR / "face_recognition_sface_2021dec.onnx"


class NoFaceDetectedError(Exception):
    """Raised when zero faces are detected (face-count policy, blueprint section 7)."""


class MultipleFacesDetectedError(Exception):
    """Raised when two or more faces are detected (face-count policy, blueprint section 7)."""


@dataclass
class FaceProcessingResult:
    embedding: np.ndarray
    detection_score: float
    face_box: np.ndarray  # [x, y, w, h]


class FaceRecognitionPipeline:
    """Enforces the exactly-one-face policy and produces a normalized embedding."""

    def __init__(
        self,
        detector_model_path: str | Path = DEFAULT_YUNET_PATH,
        embedder_model_path: str | Path = DEFAULT_SFACE_PATH,
    ):
        self._detector = FaceDetector(str(detector_model_path))
        self._embedder = FaceEmbedder(str(embedder_model_path))

    def process(self, image: np.ndarray) -> FaceProcessingResult:
        """Run detection + exactly-one-face check + embedding on a decoded BGR image.

        Raises NoFaceDetectedError or MultipleFacesDetectedError per the frozen
        face-count policy. Never silently selects a face from a multi-face image.
        """
        faces = self._detector.detect(image)

        if faces.shape[0] == 0:
            raise NoFaceDetectedError()
        if faces.shape[0] > 1:
            raise MultipleFacesDetectedError()

        face_row = faces[0]
        raw_embedding = self._embedder.embed(image, face_row)
        embedding = normalize(raw_embedding)

        return FaceProcessingResult(
            embedding=embedding,
            detection_score=float(face_row[14]),
            face_box=face_row[:4].astype(np.float32),
        )
