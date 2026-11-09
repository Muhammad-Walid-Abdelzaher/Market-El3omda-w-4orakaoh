# Object detection

The shelf-vision endpoint runs the configured Ultralytics YOLO checkpoint and returns only its object detections: bounding boxes, class labels, and confidence scores. The current `best.pt` checkpoint has the single class `{0: "object"}`, so it does not identify product SKUs, brands, or package variants.

The app does not infer empty shelves, gaps, occupancy, or stock status. Annotated images draw only bounding boxes returned by the detector. An image with no model detections is returned unchanged. Vision observations are saved for review and never change inventory.

## API

`POST /api/vision/analyze` accepts multipart form data:

- `file` (required): image up to 15 MB and 20 megapixels.
- `shelf_location` (optional): human-readable aisle or shelf identifier.
- `confidence` (optional, default `0.25`): minimum YOLO detection confidence from `0.01` to `1.0`.

The response contains the model name, image dimensions, object detections, and URLs for the original and object-annotated images. `GET /api/vision/analyses` lists recent saved analyses. Historical analyses created before object-only mode may include old empty-gap annotations; they are not shown as object-only thumbnails in the current UI.

## Model path

The default is `YOLO_MODEL_PATH=models/best.pt` in `backend/.env`. The backend also checks the workspace root for a file with the configured model filename.

Run the backend from the project virtual environment:

```powershell
cd .\backend
..\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Run tests:

```powershell
cd .\backend
..\.venv\Scripts\python.exe -m pytest tests -q
```
