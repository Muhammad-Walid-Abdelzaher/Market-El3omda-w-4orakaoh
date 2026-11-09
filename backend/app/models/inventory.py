"""
StockVision AI - Inventory & Stock Movement Models
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Inventory(Base):
    """
    Current inventory level for a product.

    One-to-one relationship with Product. This table changes frequently
    (every sale, delivery, adjustment) while the Product table stays stable.

    Important distinction:
    - quantity_in_stock: official recorded inventory (shelf + storage)
    - quantity_on_shelf: last verified count from shelf observation (CV + human review)
    """

    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), unique=True, nullable=False
    )
    quantity_in_stock: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    quantity_on_shelf: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_counted_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    product: Mapped["Product"] = relationship(
        "Product", back_populates="inventory"
    )

    def __repr__(self) -> str:
        return (
            f"<Inventory(product_id={self.product_id}, "
            f"in_stock={self.quantity_in_stock}, on_shelf={self.quantity_on_shelf})>"
        )


class StockMovement(Base):
    """
    Audit log of every inventory change.

    This is an append-only table — rows are never updated or deleted.
    Every sale, delivery, waste event, or manual adjustment creates a new row.

    The receiving and checkout flows record RECEIVE and SALE movements.
    """

    __tablename__ = "stock_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    movement_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    batch_number: Mapped[str | None] = mapped_column(String(100), nullable=True)
    employee: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    product: Mapped["Product"] = relationship(
        "Product", back_populates="stock_movements"
    )

    def __repr__(self) -> str:
        return (
            f"<StockMovement(product_id={self.product_id}, "
            f"type='{self.movement_type}', qty={self.quantity})>"
        )


# Resolve forward reference
from app.models.product import Product  # noqa: E402, F401
