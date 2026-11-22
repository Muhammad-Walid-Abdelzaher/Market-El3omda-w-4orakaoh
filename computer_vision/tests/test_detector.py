import numpy as np
import pytest

from computer_vision.detector import detect_products
from computer_vision.exceptions import ModelNotFoundError
from computer_vision.temporal import calculate_iou


def test_calculate_iou_and_invalid_box():
    assert calculate_iou([0, 0, 10, 10], [0, 0, 10, 10]) == 1.0
    assert calculate_iou([0, 0, 10, 10], [20, 20, 30, 30]) == 0.0
    assert calculate_iou([], [0, 0, 10, 10]) == 0.0


def test_missing_model_raises_clear_error(tmp_path):
    missing = tmp_path / "missing.pt"
    with pytest.raises(ModelNotFoundError, match="YOLO weights were not found"):
        detect_products(
            np.zeros((20, 20, 3), dtype=np.uint8),
            model_path=missing,
        )
