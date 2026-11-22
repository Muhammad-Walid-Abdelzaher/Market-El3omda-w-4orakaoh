from __future__ import annotations

from typing import Any

import numpy as np

from .config import ComputerVisionConfig
from .detector import detect_products as _detect_products
from .image_utils import validate_image
from .ocr import enrich_detections_with_ocr as _enrich
from .temporal import compare_shelf_images as _compare
from .visualization import annotate_image as _annotate


class ComputerVisionService:
    def __init__(
        self,
        model_path: str = "models/yolo/best.pt",
        config: ComputerVisionConfig | None = None,
    ) -> None:
        self.config = config or ComputerVisionConfig(yolo_model_path=model_path)
        if config is not None:
            self.model_path = str(config.yolo_model_path)
        else:
            self.model_path = str(model_path)

    def analyze_image(
        self,
        image: np.ndarray,
        catalog: list[dict[str, Any]] | None = None,
        confidence: float | None = None,
    ) -> dict[str, Any]:
        image = validate_image(image, max_pixels=self.config.max_pixels)
        detection_result = _detect_products(
            image=image,
            confidence=self.config.confidence if confidence is None else confidence,
            max_detections=self.config.max_detections,
            model_path=self.model_path,
            device=self.config.device,
        )
        detections = _enrich(
            image=image,
            detections=detection_result["detections"],
            catalog=catalog,
            ocr_confidence=self.config.ocr_confidence,
            device=self.config.ocr_device,
            limit_side_len=self.config.ocr_limit_side_len,
            ocr_model_dir=self.config.ocr_model_dir,
            det_model_path=self.config.ocr_det_model_path,
            rec_model_path=self.config.ocr_rec_model_path,
            cls_model_path=self.config.ocr_cls_model_path,
        )
        return {
            "detections": detections,
            "model_name": detection_result["model_name"],
            "image_width": int(image.shape[1]),
            "image_height": int(image.shape[0]),
        }

    def compare_shelf_images(
        self,
        previous_image: np.ndarray,
        current_image: np.ndarray,
        previous_detections: list[dict[str, Any]],
        current_detections: list[dict[str, Any]],
    ) -> dict[str, Any]:
        return _compare(
            previous_image,
            current_image,
            previous_detections,
            current_detections,
            self.config,
        )

    def annotate_image(
        self,
        image: np.ndarray,
        detections: list[dict[str, Any]],
    ) -> np.ndarray:
        return _annotate(image, detections)
