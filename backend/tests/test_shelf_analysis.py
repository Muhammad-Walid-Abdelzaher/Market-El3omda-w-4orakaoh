import cv2
import numpy as np
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app as fastapi_app
from app.routers import vision as vision_router
from app import models
from app.cv.shelf_analysis import annotate_image, decode_image


def test_annotation_draws_only_model_object_boxes():
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    detections = [
        {"bbox": [10, 10, 30, 50], "label": "object", "confidence": 0.9},
    ]

    annotated = annotate_image(image, detections)

    assert annotated[10, 10].tolist() == [80, 220, 130]
    assert annotated[70, 100].tolist() == [0, 0, 0]


def test_empty_detection_list_does_not_add_shelf_or_gap_annotations():
    image = np.zeros((100, 200, 3), dtype=np.uint8)

    annotated = annotate_image(image, [])

    assert np.array_equal(annotated, image)


def test_decode_image_rejects_empty_or_invalid_image():
    for data in (b"", b"not an image"):
        try:
            decode_image(data)
        except ValueError:
            pass
        else:
            raise AssertionError("Invalid image data should be rejected.")


def test_analyze_endpoint_saves_only_model_detections_without_stock_alerts(
    tmp_path,
    monkeypatch,
):
    engine = create_engine(
        f"sqlite:///{tmp_path / 'vision-test.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def override_db():
        session = session_factory()
        try:
            yield session
        finally:
            session.close()

    monkeypatch.setattr(vision_router, "UPLOAD_PATH", tmp_path / "uploads")
    monkeypatch.setattr(
        vision_router,
        "detect_products",
        lambda image, confidence: (
            [{"bbox": [20, 10, 60, 40], "label": "object", "class_id": 0, "confidence": 0.9}],
            "test-model.pt",
        ),
    )
    previous_overrides = fastapi_app.dependency_overrides.copy()
    fastapi_app.dependency_overrides[get_db] = override_db
    image = np.zeros((100, 200, 3), dtype=np.uint8)
    encoded, image_bytes = cv2.imencode(".jpg", image)
    assert encoded

    try:
        with TestClient(fastapi_app) as client:
            response = client.post(
                "/api/vision/analyze",
                files={"file": ("shelf.jpg", image_bytes.tobytes(), "image/jpeg")},
                data={"shelf_location": "Aisle 1", "confidence": "0.3"},
            )
            assert response.status_code == 201, response.text
            result = response.json()
            assert result["detection_mode"] == "objects_only"
            assert result["total_detections"] == 1
            assert result["detections"][0]["label"] == "object"
            assert "regions" not in result
            assert "gaps" not in result
            assert result["inventory_effect"].startswith("Observation only")
            assert (tmp_path / "uploads" / "shelf-analysis").exists()
            history = client.get("/api/vision/analyses").json()
            assert len(history) == 1
            assert history[0]["detection_mode"] == "objects_only"
            assert client.get("/api/dashboard/summary").json()["active_alerts"] == 0
            assert client.get("/api/products").json() == []
            assert client.post(
                "/api/vision/analyze",
                files={"file": ("not-an-image.jpg", b"invalid", "image/jpeg")},
            ).status_code == 400
    finally:
        fastapi_app.dependency_overrides.clear()
        fastapi_app.dependency_overrides.update(previous_overrides)
        Base.metadata.drop_all(engine)
        engine.dispose()
