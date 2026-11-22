from .config import ComputerVisionConfig
from .detector import detect_products
from .exceptions import (
    ComputerVisionError,
    ImageDecodeError,
    ModelInferenceError,
    ModelNotFoundError,
)
from .image_utils import decode_image
from .ocr import enrich_detections_with_ocr, get_ocr_model
from .product_matcher import match_product, normalize_match_text
from .detector import get_yolo_model
from .model_verifier import verify_models
from .service import ComputerVisionService
from .temporal import (
    calculate_appearance_similarity,
    calculate_iou,
    calculate_text_similarity,
    compare_shelf_images,
)
from .visualization import annotate_image

__all__ = [
    "ComputerVisionConfig",
    "ComputerVisionService",
    "ComputerVisionError",
    "ImageDecodeError",
    "ModelInferenceError",
    "ModelNotFoundError",
    "decode_image",
    "detect_products",
    "get_yolo_model",
    "get_ocr_model",
    "enrich_detections_with_ocr",
    "match_product",
    "normalize_match_text",
    "verify_models",
    "analyze_image",
    "compare_shelf_images",
    "annotate_image",
    "calculate_iou",
    "calculate_text_similarity",
    "calculate_appearance_similarity",
]


def analyze_image(
    image,
    catalog=None,
    confidence=0.25,
    model_path="models/yolo/best.pt",
) -> dict:
    """Convenience function using a service instance."""
    config = ComputerVisionConfig(
        yolo_model_path=model_path,
        confidence=confidence,
    )
    service = ComputerVisionService(model_path=model_path, config=config)
    return service.analyze_image(image=image, catalog=catalog, confidence=confidence)
