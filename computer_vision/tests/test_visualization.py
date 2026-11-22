import numpy as np

from computer_vision.visualization import annotate_image


def test_empty_detections_returns_equal_image():
    image = np.zeros((50, 50, 3), dtype=np.uint8)
    annotated = annotate_image(image, [])
    assert np.array_equal(image, annotated)
