"""
StockVision AI - Database Connection & Session Management

Sets up the SQLAlchemy engine, session factory, and provides
a dependency for FastAPI route handlers.
"""

from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


# Create the SQLAlchemy engine
# check_same_thread=False is required for SQLite with FastAPI (multi-threaded)
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=settings.DEBUG,  # Log SQL queries in debug mode
)

# Enable WAL mode and foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Enable SQLite performance and integrity settings."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class for all SQLAlchemy models
class Base(DeclarativeBase):
    pass


def get_db():
    """
    FastAPI dependency that provides a database session.

    Usage in route handlers:
        @router.get("/products")
        def get_products(db: Session = Depends(get_db)):
            ...

    The session is automatically closed after the request completes.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create all tables defined by SQLAlchemy models.
    Call this once at application startup.
    """
    # Import all models so they are registered with Base.metadata
    import app.models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "sqlite":
        _migrate_sqlite_columns()


def _migrate_sqlite_columns():
    migrations = {
        "products": {
            "purchase_price": "FLOAT NOT NULL DEFAULT 0",
            "size": "VARCHAR(100)",
        },
        "stock_movements": {
            "unit_cost": "FLOAT NOT NULL DEFAULT 0",
            "batch_number": "VARCHAR(100)",
            "employee": "VARCHAR(120)",
        },
    }
    with engine.begin() as connection:
        inspector = inspect(connection)
        for table_name, columns in migrations.items():
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, definition in columns.items():
                if column_name not in existing:
                    connection.execute(
                        text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")
                    )
