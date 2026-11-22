# StockVision standalone Computer Vision package

`computer_vision` is a framework-independent package extracted from StockVision AI.
It contains image decoding, YOLO detection, RapidOCR enrichment, dictionary-based
catalog matching, temporal shelf comparison, and annotation. It does not contain
SQLAlchemy, HTTP routes, authentication, inventory, sales, or application settings.

## Installation

Copy the `computer_vision/` directory into the receiving project and install dependencies:

```powershell
py -m pip install -r computer_vision/requirements.txt
```

For test-only dependencies:

```powershell
py -m pip install -r computer_vision/requirements-test.txt
```

The package already contains the prototype's exact weights under
`computer_vision/models/yolo/best.pt` and RapidOCR ONNX assets under
`computer_vision/models/ocr/`. See `models/MISSING_OR_EXTERNAL_ASSETS.md` for the
extraction report.

For ONNX Runtime GPU support, install the appropriate `onnxruntime-gpu` build for
your CUDA version instead of `onnxruntime`. RapidOCR GPU usage is controlled by
`OCR device="cuda"` and remains unavailable if CUDA is not exposed by ONNX Runtime.

```powershell
py -m pip install -r computer_vision/requirements-gpu.txt
```

## Architecture

- `config.py`: standalone configuration.
- `image_utils.py`: decoding and validation.
- `detector.py`: lazy/cached YOLO loading and result parsing.
- `ocr.py`: lazy RapidOCR loading and crop OCR.
- `product_matcher.py`: exact and fuzzy dictionary catalog matching.
- `temporal.py`: homography, Hungarian/global assignment, and temporal results.
- `visualization.py`: bounding-box rendering.
- `service.py`: reusable `ComputerVisionService`.
- `exceptions.py`: package-specific errors.

## Catalog contract

Pass plain dictionaries retrieved by the calling application:

```python
catalog = [
    {
        "id": 101,
        "name": "Coca-Cola 330ml",
        "brand": "Coca-Cola",
        "sku": "CC330",
        "barcode": "123456789",
    }
]
```

Only `name`, `brand`, `sku`, `barcode`, and `id` are read. The package does not
store or retrieve catalog data. If `catalog=None` or `[]`, OCR still runs but
classification remains unknown.

## Public API

```python
from computer_vision import (
    ComputerVisionService,
    decode_image,
    detect_products,
    enrich_detections_with_ocr,
    compare_shelf_images,
    annotate_image,
)
```

### Model verification

```python
from computer_vision import verify_models

report = verify_models(device="cpu")
if not report["valid"]:
    raise RuntimeError(report)
```

To load both model implementations as part of verification:

```python
report = verify_models(device="cpu", load_models=True)
```

The report identifies missing assets, unreadable assets, missing Python libraries,
CUDA availability, and selected-device availability.

### Decode and analyze

```python
cv_service = ComputerVisionService(model_path="models/yolo/best.pt")

image = decode_image(upload_bytes)
catalog = load_catalog_from_your_application()
result = cv_service.analyze_image(image=image, catalog=catalog)

detections = result["detections"]
annotated = cv_service.annotate_image(image, detections)
```

The service loads YOLO and RapidOCR lazily and caches model instances.

### Detection-only and OCR-only usage

```python
with open("models/yolo/best.pt", "rb"):
    pass

detection_result = detect_products(
    image,
    confidence=0.25,
    max_detections=1000,
    model_path="models/yolo/best.pt",
)
detections = enrich_detections_with_ocr(
    image,
    detection_result["detections"],
    catalog=catalog,
)
```

### Temporal comparison

```python
temporal = compare_shelf_images(
    previous_image,
    current_image,
    previous_detections,
    current_detections,
)
```

The temporal result separates `unchanged`, `disappeared`, `newly_visible`, and
`uncertain`. `disappeared` means absence in the current set of detections; it
does not prove that a product was sold or is physically absent.

## Detection output

```json
{
  "bbox": [10.0, 20.0, 100.0, 200.0],
  "label": "Coca-Cola 330ml",
  "model_label": "object",
  "class_id": 0,
  "confidence": 0.94,
  "texts": ["Coca-Cola"],
  "ocr_conf": [0.91],
  "mean_ocr_conf": 0.91,
  "matched_product": {
    "id": 101,
    "name": "Coca-Cola 330ml",
    "brand": "Coca-Cola",
    "sku": "CC330",
    "barcode": "123456789"
  },
  "product_match_score": 100.0,
  "classification_status": "matched"
}
```

## Web-framework integration

The receiving application owns upload limits, storage, database access, and HTTP
responses. A FastAPI endpoint should call `decode_image(await file.read())`,
retrieve the catalog, call `ComputerVisionService.analyze_image(...)`, optionally
encode the annotated NumPy image, and store its own results.

Example error handling:

```python
from computer_vision import (
    ComputerVisionError,
    ImageDecodeError,
    ModelNotFoundError,
)

try:
    image = decode_image(payload)
except ImageDecodeError as error:
    raise ValueError(str(error))

try:
    result = cv_service.analyze_image(image, catalog)
except ModelNotFoundError as error:
    raise RuntimeError(str(error))
except ComputerVisionError as error:
    raise RuntimeError(str(error))
```

## Configuration

```python
from computer_vision import ComputerVisionConfig, ComputerVisionService

config = ComputerVisionConfig(
    yolo_model_path="models/yolo/best.pt",
    confidence=0.25,
    max_detections=1000,
    ocr_confidence=0.5,
    max_pixels=20_000_000,
    device="cpu",
    ocr_device="cpu",
)
service = ComputerVisionService(model_path="models/yolo/best.pt", config=config)
```

Temporal settings include `temporal_match_cost_threshold`,
`temporal_unmatched_cost`, `temporal_max_normalized_distance`,
`temporal_min_spatial_iou`, `homography_ransac_threshold`,
`homography_min_matches`, and `homography_max_match_inliers_ratio`.

The default model settings are:

```python
yolo_model_path="models/yolo/best.pt"
ocr_model_dir="models/ocr"
ocr_det_model_path="models/ocr/PP-OCRv6_det_small.onnx"
ocr_rec_model_path="models/ocr/PP-OCRv6_rec_small.onnx"
ocr_cls_model_path="models/ocr/ch_ppocr_mobile_v2.0_cls_mobile.onnx"
```

## Known limitations

- Temporal matching uses catalog identity only as compatibility evidence, not as
  sole physical identity evidence.
- Shelf alignment can fail or be uncertain; unmatched and uncertain detections
  remain separate.
- Identical products near distant locations are not automatically considered the
  same physical object.
- SciPy provides Hungarian assignment; a greedy fallback is used only if SciPy
  is unavailable.

## Offline execution

The package performs no silent download of replacement YOLO or RapidOCR weights.
Keep the files listed in `models/` beside the Python package and install the runtime
dependencies before starting the process.

CPU dependencies use ONNX Runtime's CPU provider. For CUDA, install a compatible
`onnxruntime-gpu` build and enable CUDA for YOLO and RapidOCR; YOLO is configured
through `ComputerVisionConfig.device`, while RapidOCR is configured through
`ocr_device`.
