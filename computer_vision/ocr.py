from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Sequence

import cv2
import numpy as np

from .exceptions import ModelInferenceError

_ocr_lock = threading.Lock()
_ocr_model: Any | None = None
_ocr_model_key: tuple[str, int, str, str, str] | None = None
_PACKAGE_ROOT = Path(__file__).resolve().parent


def resolve_ocr_path(path: str | Path) -> Path:
    resolved = Path(path).expanduser()
    if resolved.is_absolute():
        return resolved.resolve()
    package_relative = (_PACKAGE_ROOT / resolved).resolve()
    if package_relative.exists():
        return package_relative
    return resolved.resolve()


def get_ocr_model(
    device: str = "cpu",
    limit_side_len: int = 384,
    ocr_model_dir: str | Path = "models/ocr",
    det_model_path: str | Path = "models/ocr/PP-OCRv6_det_small.onnx",
    rec_model_path: str | Path = "models/ocr/PP-OCRv6_rec_small.onnx",
    cls_model_path: str | Path = "models/ocr/ch_ppocr_mobile_v2.0_cls_mobile.onnx",
) -> Any:
    global _ocr_model, _ocr_model_key
    det_path = resolve_ocr_path(det_model_path)
    rec_path = resolve_ocr_path(rec_model_path)
    cls_path = resolve_ocr_path(cls_model_path)
    model_dir = resolve_ocr_path(ocr_model_dir)
    key = (
        device.lower(),
        limit_side_len,
        str(det_path),
        str(rec_path),
        str(cls_path),
    )
    with _ocr_lock:
        if _ocr_model is None or _ocr_model_key != key:
            try:
                import onnxruntime as ort
                from rapidocr import RapidOCR
            except ImportError as error:
                raise ModelInferenceError(
                    "rapidocr and onnxruntime are required for OCR."
                ) from error
            providers = ort.get_available_providers()
            use_cuda = (
                device.lower() in {"cuda", "gpu"}
                and "CUDAExecutionProvider" in providers
            )
            if device.lower() in {"cuda", "gpu"} and not use_cuda:
                raise ModelInferenceError(
                    "CUDA was requested for RapidOCR, but ONNX Runtime CUDA "
                    "ExecutionProvider is unavailable."
                )
            missing = [
                str(path)
                for path in (det_path, rec_path, cls_path)
                if not path.is_file()
            ]
            if missing:
                raise ModelInferenceError(
                    "Missing bundled RapidOCR model assets: " + ", ".join(missing)
                )
            params = {
                "Global.use_cls": True,
                "Global.model_root_dir": str(model_dir),
                "Det.limit_side_len": limit_side_len,
                "Det.limit_type": "max",
                "Det.model_path": str(det_path),
                "Det.use_cuda": use_cuda,
                "Cls.model_path": str(cls_path),
                "Cls.use_cuda": use_cuda,
                "Rec.model_path": str(rec_path),
                "Rec.use_cuda": use_cuda,
                "EngineConfig.onnxruntime.use_cuda": use_cuda,
                "EngineConfig.onnxruntime.intra_op_num_threads": 2,
            }
            _ocr_model = RapidOCR(params=params)
            _ocr_model_key = key
    return _ocr_model


def _read_crop_text(
    crop: np.ndarray,
    ocr_confidence: float = 0.5,
    device: str = "cpu",
    limit_side_len: int = 384,
    ocr_model_dir: str | Path = "models/ocr",
    det_model_path: str | Path = "models/ocr/PP-OCRv6_det_small.onnx",
    rec_model_path: str | Path = "models/ocr/PP-OCRv6_rec_small.onnx",
    cls_model_path: str | Path = "models/ocr/ch_ppocr_mobile_v2.0_cls_mobile.onnx",
) -> tuple[list[str], list[float]]:
    try:
        output = get_ocr_model(
            device,
            limit_side_len,
            ocr_model_dir,
            det_model_path,
            rec_model_path,
            cls_model_path,
        )(crop)
    except Exception as error:
        raise ModelInferenceError(f"OCR inference failed: {error}") from error
    if output is None:
        return [], []
    if hasattr(output, "txts") and hasattr(output, "scores"):
        pairs = zip(output.txts or [], output.scores or [])
    else:
        items = output[0] if isinstance(output, tuple) else output
        pairs = (
            (item[1], item[2])
            for item in (items or [])
            if len(item) >= 3
        )
    texts: list[str] = []
    scores: list[float] = []
    for text, score in pairs:
        cleaned = str(text).strip()
        confidence = float(score)
        if cleaned and confidence >= ocr_confidence:
            texts.append(cleaned)
            scores.append(round(confidence, 4))
    return texts, scores


def enrich_detections_with_ocr(
    image: np.ndarray,
    detections: list[dict[str, Any]],
    catalog: list[dict[str, Any]] | None = None,
    ocr_confidence: float = 0.5,
    device: str = "cpu",
    limit_side_len: int = 384,
    ocr_model_dir: str | Path = "models/ocr",
    det_model_path: str | Path = "models/ocr/PP-OCRv6_det_small.onnx",
    rec_model_path: str | Path = "models/ocr/PP-OCRv6_rec_small.onnx",
    cls_model_path: str | Path = "models/ocr/ch_ppocr_mobile_v2.0_cls_mobile.onnx",
) -> list[dict[str, Any]]:
    from .product_matcher import match_product

    enriched: list[dict[str, Any]] = []
    ocr_tasks: list[tuple[int, np.ndarray]] = []
    for index, detection in enumerate(detections):
        item = {
            **detection,
            "label": "Unknown",
            "model_label": detection["label"],
            "classification_status": "unknown",
            "texts": [],
            "ocr_conf": [],
            "mean_ocr_conf": None,
            "matched_product": None,
            "product_match_score": None,
        }
        enriched.append(item)
        box = detection.get("bbox")
        if not isinstance(box, (list, tuple, np.ndarray)) or len(box) != 4:
            continue
        try:
            values = [float(value) for value in box]
        except (TypeError, ValueError):
            continue
        if not all(np.isfinite(value) for value in values):
            continue
        x1, y1, x2, y2 = [int(round(value)) for value in values]
        if x2 <= x1 or y2 <= y1:
            continue
        width, height = x2 - x1, y2 - y1
        if width < 24 or height < 24:
            continue
        pad_x, pad_y = round(width * 0.08), round(height * 0.08)
        crop = image[
            max(0, y1 - pad_y):min(image.shape[0], y2 + pad_y),
            max(0, x1 - pad_x):min(image.shape[1], x2 + pad_x),
        ]
        if crop.size == 0:
            continue
        min_side = min(crop.shape[:2])
        if min_side < 80:
            scale = 112 / min_side
            crop = cv2.resize(
                crop,
                (max(1, round(crop.shape[1] * scale)),
                 max(1, round(crop.shape[0] * scale))),
                interpolation=cv2.INTER_CUBIC,
            )
        ocr_tasks.append((index, np.ascontiguousarray(crop)))

    if ocr_tasks:
        worker_count = min(4, os.cpu_count() or 1, len(ocr_tasks))
        with ThreadPoolExecutor(max_workers=worker_count) as executor:
            ocr_results = list(
                executor.map(
                    lambda crop: _read_crop_text(
                        crop,
                        ocr_confidence,
                        device,
                        limit_side_len,
                        ocr_model_dir,
                        det_model_path,
                        rec_model_path,
                        cls_model_path,
                    ),
                    (crop for _, crop in ocr_tasks),
                )
            )
        for (index, _), (texts, scores) in zip(ocr_tasks, ocr_results):
            item = enriched[index]
            item["texts"] = texts
            item["ocr_conf"] = scores
            if texts:
                item["label"] = " | ".join(texts)
            if scores:
                item["mean_ocr_conf"] = round(sum(scores) / len(scores), 4)
            matched_product, match_score = match_product(texts, catalog)
            if matched_product is not None:
                item["matched_product"] = matched_product
                item["product_match_score"] = match_score
                item["classification_status"] = "matched"
                item["label"] = str(matched_product["name"])
    return enriched
