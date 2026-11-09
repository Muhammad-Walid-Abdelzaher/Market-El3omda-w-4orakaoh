from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.inventory import Inventory, StockMovement
from app.models.operations import Alert
from app.models.product import Category, Product
from app.models.sales import Sale, SaleItem
from app.schemas.entries import ProductCreate, SaleCreate, StockReceive

router = APIRouter()


def _product_data(product: Product) -> dict:
    return {
        "id": product.id,
        "name": product.name,
        "brand": product.brand,
        "barcode": product.barcode,
        "category": product.category.name if product.category else "",
        "size": product.size or "",
        "purchase_price": product.purchase_price,
        "selling_price": product.price,
        "minimum_stock": product.min_stock_level,
        "quantity": product.inventory.quantity_in_stock if product.inventory else 0,
    }


@router.get("/products")
def list_products(db: Session = Depends(get_db)):
    products = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.inventory))
        .filter(Product.is_active.is_(True))
        .order_by(Product.name)
        .all()
    )
    return [_product_data(product) for product in products]


@router.post("/products", status_code=status.HTTP_201_CREATED)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    if db.query(Product.id).filter(Product.barcode == payload.barcode).first():
        raise HTTPException(status_code=409, detail="A product with this barcode already exists.")

    category = db.query(Category).filter(Category.name == payload.category).first()
    if category is None:
        category = Category(name=payload.category)
        db.add(category)
        db.flush()

    product = Product(
        name=payload.name,
        brand=payload.brand,
        barcode=payload.barcode,
        price=payload.selling_price,
        purchase_price=payload.purchase_price,
        size=payload.size,
        category_id=category.id,
        min_stock_level=payload.minimum_stock,
        is_active=True,
    )
    db.add(product)
    try:
        db.flush()
        db.add(Inventory(product_id=product.id, quantity_in_stock=0))
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="A product with this barcode already exists.") from error
    db.refresh(product)
    return _product_data(product)


@router.get("/products/barcode/{barcode}")
def get_product_by_barcode(barcode: str, db: Session = Depends(get_db)):
    product = (
        db.query(Product)
        .options(joinedload(Product.category), joinedload(Product.inventory))
        .filter(Product.barcode == barcode, Product.is_active.is_(True))
        .first()
    )
    if product is None:
        raise HTTPException(status_code=404, detail="No product is registered for this barcode.")
    return _product_data(product)


@router.get("/inventory")
def list_inventory(db: Session = Depends(get_db)):
    products = (
        db.query(Product)
        .options(joinedload(Product.inventory))
        .filter(Product.is_active.is_(True))
        .order_by(Product.name)
        .all()
    )
    return [
        {
            "product_id": product.id,
            "name": product.name,
            "barcode": product.barcode,
            "quantity": product.inventory.quantity_in_stock if product.inventory else 0,
            "minimum_stock": product.min_stock_level,
            "updated_at": product.inventory.updated_at if product.inventory else None,
        }
        for product in products
    ]


@router.post("/inventory/receive", status_code=status.HTTP_201_CREATED)
def receive_stock(payload: StockReceive, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.id == payload.product_id, Product.is_active.is_(True)).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found.")
    try:
        inventory = db.query(Inventory).filter(Inventory.product_id == product.id).first()
        if inventory is None:
            inventory = Inventory(product_id=product.id, quantity_in_stock=0)
            db.add(inventory)
            db.flush()
        db.query(Inventory).filter(Inventory.product_id == product.id).update(
            {
                Inventory.quantity_in_stock: Inventory.quantity_in_stock + payload.quantity,
                Inventory.updated_at: datetime.now(timezone.utc),
            },
            synchronize_session=False,
        )
        db.add(
            StockMovement(
                product_id=product.id,
                movement_type="RECEIVE",
                quantity=payload.quantity,
                unit_cost=payload.unit_cost if payload.unit_cost is not None else product.purchase_price,
                batch_number=payload.batch_number.strip() if payload.batch_number else None,
                employee=payload.employee.strip(),
                reason="Stock received",
            )
        )
        db.commit()
        db.refresh(inventory)
    except Exception:
        db.rollback()
        raise
    return {
        "message": f"Received {payload.quantity} units of {product.name}.",
        "product_id": product.id,
        "quantity": inventory.quantity_in_stock,
    }


def _sale_data(sale: Sale) -> dict:
    return {
        "id": sale.id,
        "created_at": sale.sale_date,
        "total_amount": sale.total_amount,
        "employee": sale.notes,
        "items": [
            {
                "product_id": item.product_id,
                "name": item.product.name,
                "barcode": item.product.barcode,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "subtotal": item.subtotal,
            }
            for item in sale.items
        ],
    }


@router.get("/sales")
def list_sales(db: Session = Depends(get_db)):
    sales = (
        db.query(Sale)
        .options(joinedload(Sale.items).joinedload(SaleItem.product))
        .order_by(Sale.sale_date.desc())
        .limit(100)
        .all()
    )
    return [_sale_data(sale) for sale in sales]


@router.get("/sales/{sale_id}")
def get_sale(sale_id: int, db: Session = Depends(get_db)):
    sale = (
        db.query(Sale)
        .options(joinedload(Sale.items).joinedload(SaleItem.product))
        .filter(Sale.id == sale_id)
        .first()
    )
    if sale is None:
        raise HTTPException(status_code=404, detail="Sale not found.")
    return _sale_data(sale)


@router.post("/sales", status_code=status.HTTP_201_CREATED)
def create_sale(payload: SaleCreate, db: Session = Depends(get_db)):
    quantities: dict[int, int] = {}
    for line in payload.items:
        quantities[line.product_id] = quantities.get(line.product_id, 0) + line.quantity

    try:
        products: dict[int, Product] = {}
        inventories: dict[int, Inventory] = {}
        for product_id, quantity in quantities.items():
            product = (
                db.query(Product)
                .filter(Product.id == product_id, Product.is_active.is_(True))
                .first()
            )
            if product is None:
                raise HTTPException(status_code=404, detail=f"Product {product_id} not found.")
            inventory = db.query(Inventory).filter(Inventory.product_id == product_id).first()
            available = inventory.quantity_in_stock if inventory else 0
            if quantity > available:
                raise HTTPException(
                    status_code=409,
                    detail=f"Not enough stock for {product.name}. Available quantity: {available}.",
                )
            products[product_id] = product
            if inventory is None:
                raise HTTPException(
                    status_code=409,
                    detail=f"Not enough stock for {product.name}. Available quantity: 0.",
                )
            inventories[product_id] = inventory

        sale = Sale(
            sale_date=datetime.now(timezone.utc),
            total_amount=round(
                sum(products[product_id].price * quantity for product_id, quantity in quantities.items()),
                2,
            ),
            source="POS",
            notes=payload.employee.strip(),
        )
        db.add(sale)
        db.flush()
        for product_id, quantity in quantities.items():
            product = products[product_id]
            subtotal = round(product.price * quantity, 2)
            db.add(
                SaleItem(
                    sale_id=sale.id,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=product.price,
                    subtotal=subtotal,
                )
            )
            changed = (
                db.query(Inventory)
                .filter(
                    Inventory.product_id == product_id,
                    Inventory.quantity_in_stock >= quantity,
                )
                .update(
                    {
                        Inventory.quantity_in_stock: Inventory.quantity_in_stock - quantity,
                        Inventory.updated_at: datetime.now(timezone.utc),
                    },
                    synchronize_session=False,
                )
            )
            if changed != 1:
                available = inventories[product_id].quantity_in_stock
                raise HTTPException(
                    status_code=409,
                    detail=f"Not enough stock for {products[product_id].name}. Available quantity: {available}.",
                )
            db.add(
                StockMovement(
                    product_id=product_id,
                    movement_type="SALE",
                    quantity=-quantity,
                    unit_cost=product.purchase_price,
                    employee=payload.employee.strip(),
                    reason=f"Sale #{sale.id}",
                    reference=str(sale.id),
                )
            )
        db.commit()
        db.refresh(sale)
        return _sale_data(sale)
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


@router.get("/dashboard/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    return {
        "registered_products": db.query(func.count(Product.id)).filter(Product.is_active.is_(True)).scalar() or 0,
        "inventory_units": db.query(func.coalesce(func.sum(Inventory.quantity_in_stock), 0)).scalar() or 0,
        "stock_receipts": db.query(func.count(StockMovement.id)).filter(StockMovement.movement_type.in_(["RECEIVE", "DELIVERY"])).scalar() or 0,
        "completed_sales": db.query(func.count(Sale.id)).scalar() or 0,
        "active_alerts": db.query(func.count(Alert.id)).filter(Alert.is_resolved.is_(False)).scalar() or 0,
    }
