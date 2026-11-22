from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import numpy as np

from .config import ComputerVisionConfig
from .detector import resolve_model_path
from .ocr import resolve_ocr_path


def verify_models(
    config: ComputerVisionConfig | None = None,
    device: str = "cpu",
    load_models: bool = False,
) -> dict[str, Any]:
    """Verify required model assets, libraries, and selected device availability."""
    config = config or ComputerVisionConfig()
    yolo_path = resolve_model_path(config.yolo_model_path)
    det_path = resolve_ocr_path(config.ocr_det_model_path)
    rec_path = resolve_ocr_path(config.ocr_rec_model_path)
    cls_path = resolve_ocr_path(config.ocr_cls_model_path)

    assets = {
        "yolo": yolo_path,
        "ocr_detection": det_path,
        "ocr_recognition": rec_path,
        "ocr_classification": cls_path,
    }
    missing: list[str] = []
    unreadable: list[str] = []
    for name, path in assets.items():
        if not path.is_file():
            missing.append(name)
            continue
        try:
            with path.open("rb") as handle:
                if handle.read(1) == b"":
                    unreadable.append(name)
        except OSError:
            unreadable.append(name)

    missing_libraries: list[str] = []
    for name in ("cv2", "numpy", "ultralytics", "rapidocr", "onnxruntime", "scipy"):
        if importlib.util.find_spec(name) is None:
            missing_libraries.append(name)

    cuda_available = False
    if importlib.util.find_spec("onnxruntime") is not None:
        try:
            import onnxruntime as ort
            cuda_available = "CUDAExecutionProvider" in ort.get_available_providers()
        except Exception:
            cuda_available = False

    selected_device = device.lower()
    device_available = selected_device in {"cpu", "gpu", "cuda"} and (
        selected_device == "cpu" or cuda_available
    )

    load_errors: list[str] = []
    if load_models and not missing and not unreadable and not missing_libraries:
        try:
            from .detector import get_yolo_model
            get_yolo_model(yolo_path)
        except Exception as error:
            load_errors.append(f"yolo_load_failed: {error}")
        try:
            from .ocr import get_ocr_model
            get_ocr_model(
                device=selected_device,
                limit_side_len=config.ocr_limit_side_len,
                ocr_model_dir=config.ocr_model_dir,
                det_model_path=config.ocr_det_model_path,
                rec_model_path=config.ocr_rec_model_path,
                cls_model_path=config.ocr_cls_model_path,
            )
        except Exception as error:
            load_errors.append(f"rapidocr_load_failed: {error}")

    return {
        "valid": (
            not missing
            and not unreadable
            and not missing_libraries
            and device_available
            and not load_errors
        ),
        "missing": missing,
        "unreadable": unreadable,
        "missing_libraries": missing_libraries,
        "load_errors": load_errors,
        "device": selected_device,
        "device_available": device_available,
        "cuda_available": cuda_available,
        "paths": {name: str(path) for name, path in assets.items()},
    }
