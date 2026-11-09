import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated

import cv2
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import UPLOAD_PATH, settings
from app.cv.shelf_analysis import (
    annotate_image,
    decode_image,
    detect_products,
)
from app.database import get_db
from app.models.vision import Detection, ShelfObservation

logger = logging.getLogger(__name__)
router = APIRouter()

MAX_UPLOAD_BYTES = 15 * 1024 * 1024


@router.get("/analyses")
def list_shelf_analyses(db: Session = Depends(get_db)):
    observations = (
        db.query(ShelfObservation)
        .order_by(ShelfObservation.captured_at.desc())
        .limit(20)
        .all()
    )
    return [
        {
            "id": observation.id,
            "shelf_location": observation.shelf_location,
            "status": observation.status,
            "captured_at": observation.captured_at.isoformat(),
            **_observation_notes(observation),
        }
        for observation in observations
    ]


@router.post("/analyze", status_code=201)
def analyze_shelf(
    file: Annotated[UploadFile, File(...)],
    shelf_location: Annotated[str | None, Form(max_length=100)] = None,
    confidence: Annotated[float, Form(ge=0.01, le=1.0)] = 0.25,
    db: Session = Depends(get_db),
):
    image_bytes = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image is too large. Maximum upload size is 15 MB.")
    try:
        image = decode_image(image_bytes)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    try:
        detections, _ = detect_products(image, confidence)
    except (FileNotFoundError, ImportError) as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    except Exception as error:
        logger.exception("Shelf vision model inference failed")
        raise HTTPException(status_code=500, detail="Shelf image analysis failed.") from error

    annotated = annotate_image(image, detections)
    success, encoded_annotated = cv2.imencode(".jpg", annotated)
    success_original, encoded_original = cv2.imencode(".jpg", image)
    if not success or not success_original:
        raise HTTPException(status_code=500, detail="Could not encode the analyzed image.")

    analysis_id = uuid.uuid4().hex
    image_directory = UPLOAD_PATH / "shelf-analysis"
    image_directory.mkdir(parents=True, exist_ok=True)
    original_name = f"{analysis_id}_original.jpg"
    annotated_name = f"{analysis_id}_annotated.jpg"
    original_path = image_directory / original_name
    annotated_path = image_directory / annotated_name
    original_path.write_bytes(encoded_original.tobytes())
    annotated_path.write_bytes(encoded_annotated.tobytes())

    analysis = _build_response(
        detections=detections,
        model_name=Path(settings.YOLO_MODEL_PATH).name,
        image_url=f"/uploads/shelf-analysis/{original_name}",
        annotated_image_url=f"/uploads/shelf-analysis/{annotated_name}",
        image_width=image.shape[1],
        image_height=image.shape[0],
    )
    observation = ShelfObservation(
        image_path=analysis["annotated_image_url"],
        shelf_location=shelf_location.strip() if shelf_location and shelf_location.strip() else None,
        status="COMPLETED",
        notes=json.dumps(analysis),
        captured_at=datetime.now(timezone.utc),
        processed_at=datetime.now(timezone.utc),
    )

    try:
        db.add(observation)
        db.flush()
        for detection in detections:
            x1, y1, x2, y2 = detection["bbox"]
            db.add(
                Detection(
                    observation_id=observation.id,
                    label=detection["label"],
                    confidence=detection["confidence"],
                    bbox_x=x1 / image.shape[1],
                    bbox_y=y1 / image.shape[0],
                    bbox_width=(x2 - x1) / image.shape[1],
                    bbox_height=(y2 - y1) / image.shape[0],
                    status="PENDING",
                )
            )
        db.commit()
    except Exception:
        db.rollback()
        original_path.unlink(missing_ok=True)
        annotated_path.unlink(missing_ok=True)
        logger.exception("Could not persist shelf analysis")
        raise HTTPException(status_code=500, detail="Shelf analysis could not be saved.") from None

    analysis["analysis_id"] = observation.id
    analysis["shelf_location"] = observation.shelf_location
    analysis["captured_at"] = observation.captured_at.isoformat()
    return analysis


def _build_response(
    detections: list[dict],
    model_name: str,
    image_url: str,
    annotated_image_url: str,
    image_width: int,
    image_height: int,
) -> dict:
    return {
        "image_url": image_url,
        "annotated_image_url": annotated_image_url,
        "image_width": image_width,
        "image_height": image_height,
        "model": model_name,
        "detection_mode": "objects_only",
        "model_semantics": "Detection classes are model labels, not verified product SKUs.",
        "inventory_effect": "Observation only. No inventory quantity is changed by image analysis.",
        "total_detections": len(detections),
        "detections": detections,
    }


def _observation_notes(observation: ShelfObservation) -> dict:
    if not observation.notes:
        return {}
    try:
        notes = json.loads(observation.notes)
    except json.JSONDecodeError:
        logger.warning("Invalid saved shelf-analysis notes for observation %s", observation.id)
        return {}
    return {
        "detection_mode": notes.get("detection_mode"),
        "total_detections": notes.get("total_detections", 0),
        "annotated_image_url": (
            notes.get("annotated_image_url")
            if notes.get("detection_mode") == "objects_only"
            else None
        ),
    }
