"""
StockVision AI - Operations Models (Alerts & Restocking Tasks)
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Alert(Base):
    """
    System-generated notification for conditions that need attention.

    alert_type values:
        LOW_STOCK      - Product below minimum stock level
        OUT_OF_STOCK   - Product has zero inventory
        EXPIRY_WARNING - Product approaching expiry date
        DISCREPANCY    - Shelf observation doesn't match recorded inventory
        EMPTY_SHELF    - CV detected an empty shelf section

    severity values: LOW, MEDIUM, HIGH, CRITICAL
    """

    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=True, index=True
    )
    alert_type: Mapped[str] = mapped_column(String(30), nullable=False)
    severity: Mapped[str] = mapped_column(
        String(10), nullable=False, default="MEDIUM"
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_resolved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    product: Mapped["Product | None"] = relationship(
        "Product", back_populates="alerts"
    )

    def __repr__(self) -> str:
        return (
            f"<Alert(id={self.id}, type='{self.alert_type}', "
            f"severity='{self.severity}', resolved={self.is_resolved})>"
        )


class RestockingTask(Base):
    """
    Actionable restocking task generated from alerts, AI recommendations,
    or manual creation.

    status values: PENDING, IN_PROGRESS, COMPLETED, CANCELLED
    priority values: LOW, MEDIUM, HIGH, URGENT
    source values: MANUAL, LOW_STOCK_ALERT, CV_OBSERVATION, AI_RECOMMENDATION
    """

    __tablename__ = "restocking_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False
    )
    quantity_needed: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[str] = mapped_column(
        String(10), nullable=False, default="MEDIUM"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING"
    )
    source: Mapped[str] = mapped_column(String(30), nullable=False)
    assigned_to: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # Relationships
    product: Mapped["Product"] = relationship(
        "Product", back_populates="restocking_tasks"
    )

    def __repr__(self) -> str:
        return (
            f"<RestockingTask(id={self.id}, product_id={self.product_id}, "
            f"qty={self.quantity_needed}, status='{self.status}')>"
        )


# Resolve forward reference
from app.models.product import Product  # noqa: E402, F401
