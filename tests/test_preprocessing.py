import cv2
import numpy as np
import pytest

from ml.preprocessing import decode_image, InvalidImageError, MAX_IMAGE_BYTES


def _encode_jpeg(image: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".jpg", image)
    assert ok
    return buf.tobytes()


def test_decode_valid_image():
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    decoded = decode_image(_encode_jpeg(image))
    assert decoded.shape[0] == 100
    assert decoded.shape[1] == 100


def test_decode_empty_bytes_raises():
    with pytest.raises(InvalidImageError):
        decode_image(b"")


def test_decode_corrupt_bytes_raises():
    with pytest.raises(InvalidImageError):
        decode_image(b"not a real image")


def test_decode_too_small_image_raises():
    image = np.zeros((10, 10, 3), dtype=np.uint8)
    with pytest.raises(InvalidImageError):
        decode_image(_encode_jpeg(image))


def test_decode_oversized_file_raises():
    oversized = b"\xff" * (MAX_IMAGE_BYTES + 1)
    with pytest.raises(InvalidImageError):
        decode_image(oversized)
