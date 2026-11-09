"""
StockVision AI - Dashboard API Router

Provides aggregated data for the frontend dashboard.
"""

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, case, desc
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.product import Category, Product
from app.models.inventory import Inventory, StockMovement
from app.models.sales import Sale, SaleItem
from app.models.vision import ShelfObservation, Detection
from app.models.operations import Alert, RestockingTask

router = APIRouter()


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    """
    Returns high-level KPIs for the dashboard header cards.
    """
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = now - timedelta(days=7)
    thirty_days_ago = now - timedelta(days=30)

    # Total products
    total_products = db.query(func.count(Product.id)).filter(Product.is_active == True).scalar() or 0

    # Total inventory value
    inventory_value = (
        db.query(func.sum(Product.price * Inventory.quantity_in_stock))
        .join(Inventory, Product.id == Inventory.product_id)
        .filter(Product.is_active == True)
        .scalar()
    ) or 0.0

    # Low stock products (quantity_in_stock <= min_stock_level)
    low_stock_count = (
        db.query(func.count(Product.id))
        .join(Inventory, Product.id == Inventory.product_id)
        .filter(
            Product.is_active == True,
            Inventory.quantity_in_stock <= Product.min_stock_level,
            Inventory.quantity_in_stock > 0,
        )
        .scalar()
    ) or 0

    # Out of stock products
    out_of_stock_count = (
        db.query(func.count(Product.id))
        .join(Inventory, Product.id == Inventory.product_id)
        .filter(Product.is_active == True, Inventory.quantity_in_stock == 0)
        .scalar()
    ) or 0

    # Sales today
    sales_today = (
        db.query(func.sum(Sale.total_amount))
        .filter(Sale.sale_date >= today_start)
        .scalar()
    ) or 0.0

    # Sales last 7 days
    sales_7d = (
        db.query(func.sum(Sale.total_amount))
        .filter(Sale.sale_date >= seven_days_ago)
        .scalar()
    ) or 0.0

    # Sales last 30 days
    sales_30d = (
        db.query(func.sum(Sale.total_amount))
        .filter(Sale.sale_date >= thirty_days_ago)
        .scalar()
    ) or 0.0

    # Active alerts
    active_alerts = (
        db.query(func.count(Alert.id))
        .filter(Alert.is_resolved == False)
        .scalar()
    ) or 0

    # Pending restocking tasks
    pending_tasks = (
        db.query(func.count(RestockingTask.id))
        .filter(RestockingTask.status.in_(["PENDING", "IN_PROGRESS"]))
        .scalar()
    ) or 0

    # Shelf observations today
    observations_today = (
        db.query(func.count(ShelfObservation.id))
        .filter(ShelfObservation.captured_at >= today_start)
        .scalar()
    ) or 0

    return {
        "total_products": total_products,
        "inventory_value": round(inventory_value, 2),
        "low_stock_count": low_stock_count,
        "out_of_stock_count": out_of_stock_count,
        "sales_today": round(sales_today, 2),
        "sales_7d": round(sales_7d, 2),
        "sales_30d": round(sales_30d, 2),
        "active_alerts": active_alerts,
        "pending_tasks": pending_tasks,
        "observations_today": observations_today,
    }


@router.get("/sales-chart")
def get_sales_chart_data(db: Session = Depends(get_db)):
    """
    Returns daily sales totals for the last 30 days for charting.
    """
    now = datetime.now(timezone.utc)
    result = []
    for i in range(29, -1, -1):
        day = now - timedelta(days=i)
        day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = day_start + timedelta(days=1)

        daily_total = (
            db.query(func.sum(Sale.total_amount))
            .filter(Sale.sale_date >= day_start, Sale.sale_date < day_end)
            .scalar()
        ) or 0.0

        daily_count = (
            db.query(func.count(Sale.id))
            .filter(Sale.sale_date >= day_start, Sale.sale_date < day_end)
            .scalar()
        ) or 0

        result.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "label": day_start.strftime("%b %d"),
            "total": round(daily_total, 2),
            "count": daily_count,
        })

    return result


@router.get("/category-breakdown")
def get_category_breakdown(db: Session = Depends(get_db)):
    """
    Returns product count and inventory value per category.
    """
    rows = (
        db.query(
            Category.name,
            func.count(Product.id).label("product_count"),
            func.coalesce(func.sum(Inventory.quantity_in_stock), 0).label("total_stock"),
            func.coalesce(func.sum(Product.price * Inventory.quantity_in_stock), 0).label("value"),
        )
        .outerjoin(Product, Category.id == Product.category_id)
        .outerjoin(Inventory, Product.id == Inventory.product_id)
        .group_by(Category.id)
        .all()
    )

    return [
        {
            "category": r.name,
            "product_count": r.product_count,
            "total_stock": r.total_stock,
            "value": round(float(r.value), 2),
        }
        for r in rows
    ]


@router.get("/top-products")
def get_top_products(db: Session = Depends(get_db)):
    """
    Returns top 10 products by sales revenue (last 30 days).
    """
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    rows = (
        db.query(
            Product.name,
            Product.brand,
            func.sum(SaleItem.subtotal).label("revenue"),
            func.sum(SaleItem.quantity).label("units_sold"),
        )
        .join(SaleItem, Product.id == SaleItem.product_id)
        .join(Sale, SaleItem.sale_id == Sale.id)
        .filter(Sale.sale_date >= thirty_days_ago)
        .group_by(Product.id)
        .order_by(desc("revenue"))
        .limit(10)
        .all()
    )

    return [
        {
            "name": r.name,
            "brand": r.brand,
            "revenue": round(float(r.revenue), 2),
            "units_sold": int(r.units_sold),
        }
        for r in rows
    ]


@router.get("/inventory-status")
def get_inventory_status(db: Session = Depends(get_db)):
    """
    Returns inventory status breakdown and low-stock product list.
    """
    # Status counts
    healthy = (
        db.query(func.count(Product.id))
        .join(Inventory, Product.id == Inventory.product_id)
        .filter(Inventory.quantity_in_stock > Product.min_stock_level)
        .scalar()
    ) or 0

    low = (
        db.query(func.count(Product.id))
        .join(Inventory, Product.id == Inventory.product_id)
        .filter(
            Inventory.quantity_in_stock <= Product.min_stock_level,
            Inventory.quantity_in_stock > 0,
        )
        .scalar()
    ) or 0

    out = (
        db.query(func.count(Product.id))
        .join(Inventory, Product.id == Inventory.product_id)
        .filter(Inventory.quantity_in_stock == 0)
        .scalar()
    ) or 0

    # Low stock product details
    low_stock_products = (
        db.query(
            Product.name,
            Product.brand,
            Inventory.quantity_in_stock,
            Product.min_stock_level,
            Product.shelf_location,
        )
        .join(Inventory, Product.id == Inventory.product_id)
        .filter(Inventory.quantity_in_stock <= Product.min_stock_level)
        .order_by(Inventory.quantity_in_stock)
        .limit(15)
        .all()
    )

    return {
        "status_counts": {
            "healthy": healthy,
            "low": low,
            "out_of_stock": out,
        },
        "low_stock_products": [
            {
                "name": p.name,
                "brand": p.brand,
                "quantity": p.quantity_in_stock,
                "min_level": p.min_stock_level,
                "location": p.shelf_location,
            }
            for p in low_stock_products
        ],
    }


@router.get("/recent-alerts")
def get_recent_alerts(db: Session = Depends(get_db)):
    """
    Returns recent alerts, most recent first.
    """
    alerts = (
        db.query(
            Alert.id,
            Alert.alert_type,
            Alert.severity,
            Alert.message,
            Alert.is_resolved,
            Alert.created_at,
            Product.name.label("product_name"),
        )
        .outerjoin(Product, Alert.product_id == Product.id)
        .order_by(desc(Alert.created_at))
        .limit(20)
        .all()
    )

    return [
        {
            "id": a.id,
            "type": a.alert_type,
            "severity": a.severity,
            "message": a.message,
            "is_resolved": a.is_resolved,
            "created_at": str(a.created_at),
            "product_name": a.product_name,
        }
        for a in alerts
    ]


@router.get("/restocking-tasks")
def get_restocking_tasks(db: Session = Depends(get_db)):
    """
    Returns active restocking tasks.
    """
    tasks = (
        db.query(
            RestockingTask.id,
            RestockingTask.quantity_needed,
            RestockingTask.priority,
            RestockingTask.status,
            RestockingTask.source,
            RestockingTask.assigned_to,
            RestockingTask.created_at,
            Product.name.label("product_name"),
        )
        .join(Product, RestockingTask.product_id == Product.id)
        .order_by(
            case(
                (RestockingTask.priority == "URGENT", 0),
                (RestockingTask.priority == "HIGH", 1),
                (RestockingTask.priority == "MEDIUM", 2),
                (RestockingTask.priority == "LOW", 3),
            ),
            desc(RestockingTask.created_at),
        )
        .limit(20)
        .all()
    )

    return [
        {
            "id": t.id,
            "product_name": t.product_name,
            "quantity_needed": t.quantity_needed,
            "priority": t.priority,
            "status": t.status,
            "source": t.source,
            "assigned_to": t.assigned_to,
            "created_at": str(t.created_at),
        }
        for t in tasks
    ]


@router.get("/stock-movements")
def get_recent_stock_movements(db: Session = Depends(get_db)):
    """
    Returns stock movement type breakdown for the last 7 days.
    """
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)

    rows = (
        db.query(
            StockMovement.movement_type,
            func.count(StockMovement.id).label("count"),
            func.sum(StockMovement.quantity).label("total_qty"),
        )
        .filter(StockMovement.created_at >= seven_days_ago)
        .group_by(StockMovement.movement_type)
        .all()
    )

    return [
        {
            "type": r.movement_type,
            "count": r.count,
            "total_quantity": int(r.total_qty) if r.total_qty else 0,
        }
        for r in rows
    ]
