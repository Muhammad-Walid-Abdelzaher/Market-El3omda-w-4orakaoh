from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ComputerVisionConfig:
    yolo_model_path: str | Path = "models/yolo/best.pt"
    ocr_model_dir: str | Path = "models/ocr"
    ocr_det_model_path: str | Path = "models/ocr/PP-OCRv6_det_small.onnx"
    ocr_rec_model_path: str | Path = "models/ocr/PP-OCRv6_rec_small.onnx"
    ocr_cls_model_path: str | Path = "models/ocr/ch_ppocr_mobile_v2.0_cls_mobile.onnx"
    confidence: float = 0.25
    max_detections: int = 1000
    ocr_confidence: float = 0.5
    max_pixels: int = 20_000_000
    device: str = "cpu"
    ocr_device: str = "cpu"
    ocr_limit_side_len: int = 384
    temporal_match_cost_threshold: float = 0.62
    temporal_unmatched_cost: float = 0.68
    temporal_max_normalized_distance: float = 0.35
    temporal_min_spatial_iou: float = 0.01
    homography_ransac_threshold: float = 5.0
    homography_min_matches: int = 8
    homography_max_match_inliers_ratio: float = 0.20

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        if not 0.0 <= self.ocr_confidence <= 1.0:
            raise ValueError("ocr_confidence must be between 0 and 1")
        if self.max_detections < 1:
            raise ValueError("max_detections must be at least 1")
        if self.max_pixels < 1:
            raise ValueError("max_pixels must be at least 1")
        if self.device.lower() not in {"cpu", "cuda", "gpu"}:
            raise ValueError("device must be 'cpu', 'cuda', or 'gpu'")
        if self.ocr_device.lower() not in {"cpu", "cuda", "gpu"}:
            raise ValueError("ocr_device must be 'cpu', 'cuda', or 'gpu'")
        if not 0.0 <= self.temporal_match_cost_threshold <= 1.0:
            raise ValueError("temporal_match_cost_threshold must be between 0 and 1")
        if not 0.0 <= self.temporal_unmatched_cost <= 1.0:
            raise ValueError("temporal_unmatched_cost must be between 0 and 1")
