import cv2
import numpy as np
import pytest

from computer_vision import decode_image
from computer_vision.exceptions import ImageDecodeError


def test_decode_image_round_trip():
    image = np.zeros((20, 30, 3), dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok
    decoded = decode_image(encoded.tobytes())
    assert decoded.shape == image.shape


@pytest.mark.parametrize("payload", [b"", b"not an image"])
def test_decode_image_rejects_invalid_data(payload):
    with pytest.raises(ImageDecodeError):
        decode_image(payload)


def test_validate_image_enforces_pixel_limit():
    from computer_vision.image_utils import validate_image

    image = np.zeros((100, 100, 3), dtype=np.uint8)
    with pytest.raises(ImageDecodeError, match="too large"):
        validate_image(image, max_pixels=99)
