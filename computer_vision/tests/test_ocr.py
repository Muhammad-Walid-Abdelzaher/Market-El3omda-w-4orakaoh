from types import SimpleNamespace

import numpy as np

import computer_vision.ocr as ocr_module


def test_read_crop_text_filters_low_confidence(monkeypatch):
    monkeypatch.setattr(
        ocr_module,
        "get_ocr_model",
        lambda *_args: lambda _crop: SimpleNamespace(
            txts=["Keep", "Drop"], scores=[0.90, 0.49]
        ),
    )
    texts, scores = ocr_module._read_crop_text(
        np.zeros((40, 40, 3), dtype=np.uint8), ocr_confidence=0.5
    )
    assert texts == ["Keep"]
    assert scores == [0.9]


def test_invalid_bbox_and_empty_catalog_are_safe(monkeypatch):
    monkeypatch.setattr(
        ocr_module,
        "get_ocr_model",
        lambda *_args: lambda _crop: SimpleNamespace(
            txts=["Visible text"], scores=[0.95]
        ),
    )
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    detections = [
        {"bbox": [10, 10, 50, 50], "label": "object", "confidence": 0.9},
        {"bbox": [30, 30, 20, 40], "label": "object", "confidence": 0.8},
        {"bbox": [float("nan"), 1, 20, 20], "label": "object", "confidence": 0.7},
    ]
    result = ocr_module.enrich_detections_with_ocr(
        image, detections, catalog=None
    )
    assert result[0]["classification_status"] == "unknown"
    assert result[1]["texts"] == []
    assert result[2]["texts"] == []
