"""YOLO object detection for uploaded shelf images."""

from __future__ import annotations

import threading
from functools import lru_cache
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from app.config import BASE_DIR, settings

_model_lock = threading.Lock()


@lru_cache(maxsize=1)
def get_yolo_model():
    """Load the configured model once; use the workspace-root checkpoint if present."""
    from ultralytics import YOLO

    configured_path = Path(settings.YOLO_MODEL_PATH)
    candidates = (
        configured_path if configured_path.is_absolute() else BASE_DIR / configured_path,
        BASE_DIR.parent / configured_path.name,
        BASE_DIR.parent.parent / configured_path.name,
    )
    model_path = next((path for path in candidates if path.is_file()), candidates[0])
    if not model_path.is_file():
        raise FileNotFoundError(
            f"YOLO weights were not found. Set YOLO_MODEL_PATH or place weights at {model_path}."
        )
    return YOLO(str(model_path))


def decode_image(image_bytes: bytes, max_pixels: int = 20_000_000) -> np.ndarray:
    """Decode upload bytes and reject invalid or unreasonably large images."""
    if not image_bytes:
        raise ValueError("The uploaded file is empty.")
    encoded = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("The uploaded file is not a readable image.")
    height, width = image.shape[:2]
    if height * width > max_pixels:
        raise ValueError("Image dimensions are too large. Maximum is 20 megapixels.")
    return image


def detect_products(
    image: np.ndarray,
    confidence: float,
    max_detections: int = 1000,
) -> tuple[list[dict[str, Any]], str]:
    """Return only the object boxes predicted by the configured YOLO model."""
    with _model_lock:
        model = get_yolo_model()
        result = model.predict(
            source=image,
            conf=confidence,
            max_det=max_detections,
            verbose=False,
        )[0]

    detections = []
    if result.boxes is not None:
        boxes = result.boxes
        xyxy_values = boxes.xyxy.cpu().numpy()
        class_values = boxes.cls.cpu().numpy().astype(int)
        confidence_values = boxes.conf.cpu().numpy()
        names = result.names
        for xyxy, class_id, score in zip(xyxy_values, class_values, confidence_values):
            label = names.get(int(class_id), str(class_id)) if isinstance(names, dict) else names[int(class_id)]
            detections.append(
                {
                    "bbox": [float(value) for value in xyxy],
                    "label": str(label),
                    "class_id": int(class_id),
                    "confidence": float(score),
                }
            )
    return detections, Path(settings.YOLO_MODEL_PATH).name


def annotate_image(image: np.ndarray, detections: list[dict[str, Any]]) -> np.ndarray:
    """Draw only the object detections produced by the model."""
    annotated = image.copy()
    for detection in detections:
        x1, y1, x2, y2 = [int(round(value)) for value in detection["bbox"]]
        color = (80, 220, 130)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
        _draw_label(
            annotated,
            f'{detection["label"]} {detection["confidence"]:.2f}',
            (x1, max(18, y1 - 5)),
            color,
        )
    return annotated


def _draw_label(image: np.ndarray, text: str, origin: tuple[int, int], color: tuple[int, int, int]) -> None:
    font = cv2.FONT_HERSHEY_SIMPLEX
    scale = 0.48
    thickness = 1
    (text_width, text_height), baseline = cv2.getTextSize(text, font, scale, thickness)
    x, y = origin
    x = max(0, min(x, image.shape[1] - text_width - 8))
    y = max(text_height + 8, min(y, image.shape[0] - baseline - 1))
    cv2.rectangle(image, (x, y - text_height - 7), (x + text_width + 8, y + baseline), color, cv2.FILLED)
    cv2.putText(image, text, (x + 4, y - 3), font, scale, (15, 20, 30), thickness, cv2.LINE_AA)
