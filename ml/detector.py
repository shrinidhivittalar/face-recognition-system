"""YuNet-based face detection (ADR-002)."""
from __future__ import annotations

import numpy as np
import cv2


class FaceDetector:
    """Thin wrapper around cv2.FaceDetectorYN.

    YuNet requires the input size to be set to match each image, so detect()
    re-configures the detector per call.
    """

    def __init__(
        self,
        model_path: str,
        score_threshold: float = 0.9,
        nms_threshold: float = 0.3,
        top_k: int = 5000,
    ):
        self._model_path = model_path
        self._detector = cv2.FaceDetectorYN.create(
            model_path,
            "",
            (320, 320),
            score_threshold,
            nms_threshold,
            top_k,
        )

    def detect(self, image: np.ndarray) -> np.ndarray:
        """Run detection on a BGR image.

        Returns an (N, 15) array: [x, y, w, h, 5x(landmark_x, landmark_y), score].
        Returns an empty (0, 15) array when no face is found.
        """
        height, width = image.shape[:2]
        self._detector.setInputSize((width, height))
        _, faces = self._detector.detect(image)
        if faces is None:
            return np.empty((0, 15), dtype=np.float32)
        return faces
