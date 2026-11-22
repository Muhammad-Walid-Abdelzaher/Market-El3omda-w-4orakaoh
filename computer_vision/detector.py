from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import numpy as np

from .exceptions import ModelInferenceError, ModelNotFoundError

_model_lock = threading.Lock()
_model_cache: dict[str, Any] = {}
_PACKAGE_ROOT = Path(__file__).resolve().parent


def resolve_model_path(model_path: str | Path) -> Path:
    path = Path(model_path).expanduser()
    if path.is_absolute():
        return path.resolve()
    package_relative = (_PACKAGE_ROOT / path).resolve()
    if package_relative.exists():
        return package_relative
    return path.resolve()


def get_yolo_model(model_path: str | Path) -> Any:
    path = resolve_model_path(model_path)
    if not path.is_file():
        raise ModelNotFoundError(
            f"YOLO weights were not found at '{path}'. "
            "Pass model_path to ComputerVisionService or place weights at this location."
        )
    with _model_lock:
        if str(path) not in _model_cache:
            try:
                from ultralytics import YOLO
            except ImportError as error:
                raise ModelInferenceError(
                    "ultralytics is required for YOLO detection."
                ) from error
            _model_cache[str(path)] = YOLO(str(path))
    return _model_cache[str(path)]


def detect_products(
    image: np.ndarray,
    confidence: float = 0.25,
    max_detections: int = 1000,
    model_path: str | Path = "models/yolo/best.pt",
    device: str = "cpu",
) -> dict[str, Any]:
    if not isinstance(image, np.ndarray) or image.ndim != 3:
        raise ValueError("image must be a NumPy array with shape (height, width, 3)")
    model = get_yolo_model(model_path)
    try:
        with _model_lock:
            result = model.predict(
                source=image,
                conf=confidence,
                max_det=max_detections,
                device=device,
                verbose=False,
            )[0]
    except Exception as error:
        raise ModelInferenceError(f"YOLO inference failed: {error}") from error

    detections: list[dict[str, Any]] = []
    if result.boxes is not None:
        boxes = result.boxes
        xyxy_values = boxes.xyxy.cpu().numpy()
        class_values = boxes.cls.cpu().numpy().astype(int)
        confidence_values = boxes.conf.cpu().numpy()
        names = result.names
        for xyxy, class_id, score in zip(xyxy_values, class_values, confidence_values):
            if isinstance(names, dict):
                label = names.get(int(class_id), str(class_id))
            else:
                label = names[int(class_id)]
            detections.append(
                {
                    "bbox": [float(value) for value in xyxy],
                    "label": str(label),
                    "class_id": int(class_id),
                    "confidence": float(score),
                }
            )
    return {"detections": detections, "model_name": Path(model_path).name}
