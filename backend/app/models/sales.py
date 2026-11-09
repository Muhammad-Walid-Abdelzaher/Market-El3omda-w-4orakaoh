"""
StockVision AI - Sales Models
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Sale(Base):
    """
    A sale transaction (receipt header).

    One sale can contain multiple sale items (line items).
    Sales can be entered manually or imported from CSV files.
    """

    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sale_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    source: Mapped[str] = mapped_column(
        String(20), nullable=False, default="MANUAL"
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    items: Mapped[list["SaleItem"]] = relationship(
        "SaleItem", back_populates="sale", lazy="selectin",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return (
            f"<Sale(id={self.id}, date='{self.sale_date}', "
            f"total={self.total_amount})>"
        )


class SaleItem(Base):
    """
    Individual product line within a sale.

    unit_price is captured at the time of sale (snapshot), not referenced
    from the product's current price. This preserves historical accuracy.
    """

    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sale_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("sales.id"), nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id"), nullable=False, index=True
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    subtotal: Mapped[float] = mapped_column(Float, nullable=False)

    # Relationships
    sale: Mapped["Sale"] = relationship("Sale", back_populates="items")
    product: Mapped["Product"] = relationship("Product", back_populates="sale_items")

    def __repr__(self) -> str:
        return (
            f"<SaleItem(sale_id={self.sale_id}, product_id={self.product_id}, "
            f"qty={self.quantity}, subtotal={self.subtotal})>"
        )


# Resolve forward reference
from app.models.product import Product  # noqa: E402, F401
