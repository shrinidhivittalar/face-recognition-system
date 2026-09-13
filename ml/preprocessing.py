"""Image decoding and validation helpers shared by enrollment and identification."""
from __future__ import annotations

import numpy as np
import cv2

MAX_IMAGE_BYTES = 8 * 1024 * 1024  # 8 MB
MIN_DIMENSION = 64
MAX_DIMENSION = 4096


class InvalidImageError(Exception):
    """Raised when an uploaded image fails validation or cannot be decoded."""


def decode_image(raw_bytes: bytes) -> np.ndarray:
    """Decode raw image bytes into a BGR numpy array, validating size/dimensions.

    Raises InvalidImageError for empty, oversized, corrupt, or out-of-range images.
    """
    if not raw_bytes:
        raise InvalidImageError("empty_file")

    if len(raw_bytes) > MAX_IMAGE_BYTES:
        raise InvalidImageError("file_too_large")

    buffer = np.frombuffer(raw_bytes, dtype=np.uint8)
    image = cv2.imdecode(buffer, cv2.IMREAD_COLOR)

    if image is None:
        raise InvalidImageError("unsupported_or_corrupt_image")

    height, width = image.shape[:2]
    if height < MIN_DIMENSION or width < MIN_DIMENSION:
        raise InvalidImageError("image_too_small")
    if height > MAX_DIMENSION or width > MAX_DIMENSION:
        raise InvalidImageError("image_too_large")

    return image
