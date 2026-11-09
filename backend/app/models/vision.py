"""
StockVision AI - Computer Vision Models
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ShelfObservation(Base):
    """
    A single shelf image capture event.

    When an employee photographs a shelf, one observation record is created.
    The CV pipeline processes the image and creates Detection records.

    status values:
        PENDING     - Image uploaded, waiting for CV processing
        PROCESSING  - CV pipeline is currently analyzing the image
        COMPLETED   - Analysis finished, detections are available
        FAILED      - CV processing failed (bad image, model error, etc.)
    """

    __tablename__ = "shelf_observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    image_path: Mapped[str] = mapped_column(String(500), nullable=False)
    shelf_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    captured_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    processed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    detections: Mapped[list["Detection"]] = relationship(
        "Detection", back_populates="observation", lazy="selectin",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<ShelfObservation(id={self.id}, location='{self.shelf_location}', "
            f"status='{self.status}')>"
        )


class Detection(Base):
    """
    A single product detection within a shelf observation.

    One shelf image can contain many detections. Each detection represents
    one bounding box identified by the YOLO model.

    Bounding box coordinates are NORMALIZED (0.0 to 1.0 relative to image size).
    To convert to pixels: pixel_x = bbox_x * image_width

    status values:
        PENDING   - Detection awaiting employee review
        CONFIRMED - Employee confirmed the detection is correct
        CORRECTED - Employee corrected the detection (wrong product or count)
        REJECTED  - Employee rejected the detection (false positive)

    product_id is NULLABLE because the model might detect an object
    it cannot match to any known product in the database.
    """

    __tablename__ = "detections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    observation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("shelf_observations.id"), nullable=False, index=True
    )
    product_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=True, index=True
    )
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_x: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_y: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_width: Mapped[float] = mapped_column(Float, nullable=False)
    bbox_height: Mapped[float] = mapped_column(Float, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING"
    )
    verified_quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    employee_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    observation: Mapped["ShelfObservation"] = relationship(
        "ShelfObservation", back_populates="detections"
    )
    product: Mapped["Product | None"] = relationship(
        "Product", back_populates="detections"
    )

    def __repr__(self) -> str:
        return (
            f"<Detection(id={self.id}, label='{self.label}', "
            f"confidence={self.confidence:.2f}, status='{self.status}')>"
        )


# Resolve forward reference
from app.models.product import Product  # noqa: E402, F401
