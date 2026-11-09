import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models.inventory import StockMovement


@pytest.fixture()
def client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    test_sessions = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    def override_get_db():
        db = test_sessions()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client, test_sessions
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def register_product(client: TestClient, barcode: str = "0123456789012") -> dict:
    response = client.post(
        "/api/products",
        json={
            "name": "Whole milk",
            "brand": "Farm",
            "barcode": barcode,
            "category": "Dairy",
            "size": "1 L",
            "purchase_price": 1.25,
            "selling_price": 2.5,
            "minimum_stock": 4,
        },
    )
    assert response.status_code == 201
    return response.json()


def receive(client: TestClient, product_id: int, quantity: int = 8):
    return client.post(
        "/api/inventory/receive",
        json={"product_id": product_id, "quantity": quantity, "unit_cost": 1.25, "employee": "Alex"},
    )


def test_barcode_lookup_and_unknown_barcode(client):
    test_client, _ = client
    product = register_product(test_client)
    found = test_client.get("/api/products/barcode/0123456789012")
    assert found.status_code == 200
    assert found.json()["id"] == product["id"]
    assert found.json()["quantity"] == 0
    assert test_client.get("/api/products/barcode/9999999999999").status_code == 404


def test_duplicate_product_barcode_is_rejected(client):
    test_client, _ = client
    register_product(test_client)
    duplicate = test_client.post(
        "/api/products",
        json={
            "name": "Another item",
            "barcode": "0123456789012",
            "category": "Grocery",
            "size": "500 g",
            "purchase_price": 1,
            "selling_price": 2,
            "minimum_stock": 2,
        },
    )
    assert duplicate.status_code == 409


def test_receiving_increases_inventory_and_records_receipt(client):
    test_client, test_sessions = client
    product = register_product(test_client)
    response = test_client.post(
        "/api/inventory/receive",
        json={
            "product_id": product["id"],
            "quantity": 7,
            "unit_cost": 1.25,
            "batch_number": "LOT-7",
            "employee": "Alex",
        },
    )
    assert response.status_code == 201
    assert response.json()["quantity"] == 7
    assert test_client.get("/api/products/barcode/0123456789012").json()["quantity"] == 7
    assert test_client.get("/api/dashboard/summary").json()["stock_receipts"] == 1
    with test_sessions() as db:
        movement = db.query(StockMovement).one()
        assert movement.movement_type == "RECEIVE"
        assert movement.quantity == 7
        assert movement.unit_cost == 1.25
        assert movement.batch_number == "LOT-7"
        assert movement.employee == "Alex"


def test_checkout_saves_total_and_reduces_stock(client):
    test_client, _ = client
    first = register_product(test_client)
    second = register_product(test_client, "4006381333931")
    receive(test_client, first["id"], 5)
    receive(test_client, second["id"], 3)

    sale = test_client.post(
        "/api/sales",
        json={
            "employee": "Sam",
            "items": [
                {"product_id": first["id"], "quantity": 2},
                {"product_id": second["id"], "quantity": 1},
            ],
        },
    )
    assert sale.status_code == 201
    receipt = sale.json()
    assert receipt["total_amount"] == 7.5
    assert len(receipt["items"]) == 2
    assert test_client.get(f"/api/sales/{receipt['id']}").json()["total_amount"] == 7.5
    assert test_client.get("/api/products/barcode/0123456789012").json()["quantity"] == 3
    assert test_client.get("/api/products/barcode/4006381333931").json()["quantity"] == 2


def test_checkout_rejects_insufficient_stock_without_sale(client):
    test_client, _ = client
    product = register_product(test_client)
    receive(test_client, product["id"], 1)
    sale = test_client.post(
        "/api/sales",
        json={"items": [{"product_id": product["id"], "quantity": 2}]},
    )
    assert sale.status_code == 409
    assert test_client.get("/api/products/barcode/0123456789012").json()["quantity"] == 1
    assert test_client.get("/api/sales").json() == []


def test_sale_commit_failure_rolls_back_sale_and_inventory(client, monkeypatch):
    test_client, _ = client
    product = register_product(test_client)
    receive(test_client, product["id"], 4)

    def fail_commit(_self):
        raise RuntimeError("Simulated database commit failure")

    monkeypatch.setattr(Session, "commit", fail_commit)
    failed = TestClient(app, raise_server_exceptions=False).post(
        "/api/sales",
        json={"items": [{"product_id": product["id"], "quantity": 2}]},
    )
    assert failed.status_code == 500
    monkeypatch.undo()
    assert test_client.get("/api/products/barcode/0123456789012").json()["quantity"] == 4
    assert test_client.get("/api/sales").json() == []
