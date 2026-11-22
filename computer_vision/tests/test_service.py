import numpy as np

from computer_vision.config import ComputerVisionConfig
from computer_vision.exceptions import ImageDecodeError
from computer_vision.service import ComputerVisionService


def test_service_enforces_configured_pixel_limit():
    config = ComputerVisionConfig(max_pixels=99)
    service = ComputerVisionService(config=config)
    image = np.zeros((100, 100, 3), dtype=np.uint8)

    try:
        service.analyze_image(image)
    except ImageDecodeError as error:
        assert "too large" in str(error)
    else:
        raise AssertionError("Expected configured pixel limit to be enforced")
