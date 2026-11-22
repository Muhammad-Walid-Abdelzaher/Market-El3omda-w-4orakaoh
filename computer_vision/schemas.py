from typing import Any, TypedDict


class CatalogProduct(TypedDict, total=False):
    id: Any
    name: str
    brand: str
    sku: str
    barcode: str


class Detection(TypedDict, total=False):
    bbox: list[float]
    label: str
    model_label: str
    class_id: int
    confidence: float
    texts: list[str]
    ocr_conf: list[float]
    mean_ocr_conf: float | None
    matched_product: CatalogProduct | None
    product_match_score: float | None
    classification_status: str
