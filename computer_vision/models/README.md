# Bundled model assets

This directory contains the exact model assets used by the prototype, copied rather than
replaced or converted.

```text
models/
  yolo/best.pt
  ocr/PP-OCRv6_det_small.onnx
  ocr/PP-OCRv6_rec_small.onnx
  ocr/ch_ppocr_mobile_v2.0_cls_mobile.onnx
```

The package resolves relative model paths from the `computer_vision` directory, so the
default service works without a development-machine absolute path.

```python
cv_service = ComputerVisionService(
    model_path="models/yolo/best.pt"
)
```

The package raises `ModelNotFoundError` for missing YOLO weights and
`ModelInferenceError` for missing RapidOCR assets.
