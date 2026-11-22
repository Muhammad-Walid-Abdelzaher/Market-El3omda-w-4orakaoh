from __future__ import annotations

import cv2
import numpy as np

from .exceptions import ImageDecodeError


def decode_image(image_bytes: bytes, max_pixels: int = 20_000_000) -> np.ndarray:
    if not image_bytes:
        raise ImageDecodeError("The uploaded file is empty.")
    if not isinstance(image_bytes, (bytes, bytearray, memoryview)):
        raise ImageDecodeError("Image input must be bytes.")
    encoded = np.frombuffer(bytes(image_bytes), dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise ImageDecodeError("The uploaded file is not a readable image.")
    height, width = image.shape[:2]
    if height * width > max_pixels:
        raise ImageDecodeError(
            f"Image dimensions are too large. Maximum is {max_pixels:,} pixels."
        )
    return image


def validate_image(image: np.ndarray, max_pixels: int = 20_000_000) -> np.ndarray:
    if not isinstance(image, np.ndarray) or image.ndim != 3:
        raise ImageDecodeError("Image must be a NumPy array with shape (height, width, 3).")
    if image.shape[0] < 1 or image.shape[1] < 1:
        raise ImageDecodeError("Image dimensions must be positive.")
    if int(image.shape[0]) * int(image.shape[1]) > max_pixels:
        raise ImageDecodeError(
            f"Image dimensions are too large. Maximum is {max_pixels:,} pixels."
        )
    return image
