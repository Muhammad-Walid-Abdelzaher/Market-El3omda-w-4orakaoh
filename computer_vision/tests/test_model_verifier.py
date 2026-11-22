from computer_vision.model_verifier import verify_models


def test_bundled_models_are_detected():
    report = verify_models()
    assert "yolo" in report["paths"]
    assert "ocr_detection" in report["paths"]
    assert "ocr_recognition" in report["paths"]
    assert "ocr_classification" in report["paths"]
    assert report["missing"] == []
    assert report["unreadable"] == []
    assert report["load_errors"] == []
