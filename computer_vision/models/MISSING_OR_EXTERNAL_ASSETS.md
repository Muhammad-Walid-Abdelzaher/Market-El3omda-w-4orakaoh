# Model extraction report

## Present assets

- YOLO: `computer_vision/models/yolo/best.pt`
- RapidOCR detection: `computer_vision/models/ocr/PP-OCRv6_det_small.onnx`
- RapidOCR recognition: `computer_vision/models/ocr/PP-OCRv6_rec_small.onnx`
- RapidOCR classification: `computer_vision/models/ocr/ch_ppocr_mobile_v2.0_cls_mobile.onnx`

The YOLO and ONNX files were copied from the prototype's active model locations:

- Prototype YOLO: `backend/models/best.pt`
- Prototype RapidOCR package: `backend/.venv/Lib/site-packages/rapidocr/models/`

The RapidOCR recognition ONNX contains its character metadata for this ONNX runtime
configuration. No separate recognizer dictionary file was present in the prototype
RapidOCR 3.10.0 installation.

## Asset hashes

| Asset | SHA-256 |
|---|---|
| `yolo/best.pt` | `7F31A6ACB53A2EC3BB8286C2F04257BF6C6D5EC4CFDE230A907D8700517B25E8` |
| `ocr/PP-OCRv6_det_small.onnx` | `090F04ABCD9D9A7498BC4EBF677E4CB9BDCE1FE4197DDB7E529F1EF44E1FF94F` |
| `ocr/PP-OCRv6_rec_small.onnx` | `6F327246B50388F3C176AE304BD95767EA6DC0C9AE92153EF8CBE210B3C14884` |
| `ocr/ch_ppocr_mobile_v2.0_cls_mobile.onnx` | `E47ACEDF663230F8863FF1AB0E64DD2D82B838FCEB5957146DAB185A89D6215C` |

## No fabricated assets

No generic replacement YOLO weights or OCR replacements were substituted.

## Offline status

The copied assets are sufficient for model-file availability. The recipient must also
install the Python dependencies listed in `computer_vision/requirements.txt`.
Neither the YOLO nor RapidOCR model loader should download replacement model files
when these explicit paths are present.
