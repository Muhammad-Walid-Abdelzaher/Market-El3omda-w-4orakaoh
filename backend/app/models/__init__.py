"""
StockVision AI - Models Package

Imports all SQLAlchemy models so they are registered with Base.metadata
when `import app.models` is called (e.g., during database initialization).
"""

from app.models.product import Category, Product
from app.models.inventory import Inventory, StockMovement
from app.models.sales import Sale, SaleItem
from app.models.vision import ShelfObservation, Detection
from app.models.operations import Alert, RestockingTask
from app.models.ai import AIConversation

__all__ = [
    "Category",
    "Product",
    "Inventory",
    "StockMovement",
    "Sale",
    "SaleItem",
    "ShelfObservation",
    "Detection",
    "Alert",
    "RestockingTask",
    "AIConversation",
]
