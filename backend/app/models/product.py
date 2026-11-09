"""
StockVision AI - Product & Category Models
"""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Category(Base):
    """Product category (e.g., Beverages, Snacks, Dairy)."""

    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    products: Mapped[list["Product"]] = relationship(
        "Product", back_populates="category", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Category(id={self.id}, name='{self.name}')>"


class Product(Base):
    """
    Core product catalog entry.

    Represents a specific product the store sells (e.g., Coca-Cola 330ml).
    This is the central table — almost every other table references it.
    """

    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sku: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    purchase_price: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    size: Mapped[str | None] = mapped_column(String(100), nullable=True)
    category_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id"), nullable=True
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    min_stock_level: Mapped[int] = mapped_column(
        Integer, nullable=False, default=10
    )
    shelf_location: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    category: Mapped["Category | None"] = relationship(
        "Category", back_populates="products"
    )
    inventory: Mapped["Inventory"] = relationship(
        "Inventory", back_populates="product", uselist=False, lazy="selectin"
    )
    stock_movements: Mapped[list["StockMovement"]] = relationship(
        "StockMovement", back_populates="product", lazy="dynamic"
    )
    sale_items: Mapped[list["SaleItem"]] = relationship(
        "SaleItem", back_populates="product", lazy="dynamic"
    )
    detections: Mapped[list["Detection"]] = relationship(
        "Detection", back_populates="product", lazy="dynamic"
    )
    alerts: Mapped[list["Alert"]] = relationship(
        "Alert", back_populates="product", lazy="dynamic"
    )
    restocking_tasks: Mapped[list["RestockingTask"]] = relationship(
        "RestockingTask", back_populates="product", lazy="dynamic"
    )

    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name='{self.name}', sku='{self.sku}')>"


# Import related models so relationship strings resolve
from app.models.inventory import Inventory, StockMovement  # noqa: E402, F401
from app.models.sales import SaleItem  # noqa: E402, F401
from app.models.vision import Detection  # noqa: E402, F401
from app.models.operations import Alert, RestockingTask  # noqa: E402, F401
