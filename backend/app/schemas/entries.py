from pydantic import BaseModel, Field, field_validator


class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    brand: str | None = Field(default=None, max_length=100)
    barcode: str = Field(min_length=1, max_length=50)
    category: str = Field(min_length=1, max_length=100)
    size: str = Field(min_length=1, max_length=100)
    purchase_price: float = Field(ge=0)
    selling_price: float = Field(gt=0)
    minimum_stock: int = Field(default=10, ge=0)

    @field_validator("name", "barcode", "category", "size")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be blank.")
        return value

    @field_validator("brand")
    @classmethod
    def strip_brand(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None


class StockReceive(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)
    unit_cost: float | None = Field(default=None, ge=0)
    batch_number: str | None = Field(default=None, max_length=100)
    employee: str = Field(default="Staff", min_length=1, max_length=120)


class SaleLineCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class SaleCreate(BaseModel):
    items: list[SaleLineCreate] = Field(min_length=1)
    employee: str = Field(default="Cashier", min_length=1, max_length=120)
