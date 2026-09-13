"""SFace-based face embedding generation (ADR-002)."""
from __future__ import annotations

import numpy as np
import cv2


class FaceEmbedder:
    """Thin wrapper around cv2.FaceRecognizerSF."""

    def __init__(self, model_path: str):
        self._model_path = model_path
        self._recognizer = cv2.FaceRecognizerSF.create(model_path, "")

    def align_and_crop(self, image: np.ndarray, face_row: np.ndarray) -> np.ndarray:
        """Align and crop the detected face using YuNet's landmark output."""
        return self._recognizer.alignCrop(image, face_row)

    def embed(self, image: np.ndarray, face_row: np.ndarray) -> np.ndarray:
        """Produce a raw (unnormalized) embedding for the detected face."""
        aligned = self.align_and_crop(image, face_row)
        feature = self._recognizer.feature(aligned)
        return feature.flatten().astype(np.float32)


def normalize(embedding: np.ndarray) -> np.ndarray:
    """L2-normalize an embedding vector so cosine similarity reduces to a dot product."""
    norm = np.linalg.norm(embedding)
    if norm == 0:
        return embedding
    return embedding / norm
