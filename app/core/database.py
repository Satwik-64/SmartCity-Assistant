# app/core/database.py
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from typing import Generator

from app.core.config import settings
from app.models import Base
from app.services.admin_bootstrap import ensure_seed_admin


def _build_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite"):
        return create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )

    return create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=1800,
        pool_size=10,
        max_overflow=20,
    )


DATABASE_URL = settings.database_url
engine = _build_engine(DATABASE_URL)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database - create all tables"""
    Base.metadata.create_all(bind=engine)
    _apply_schema_patches()
    print("[OK] Database tables created successfully")


def _bootstrap_seed_accounts() -> None:
    try:
        with SessionLocal() as session:
            ensure_seed_admin(session)
    except Exception as exc:
        print(f"[WARN] Failed to ensure seed admin account: {exc}")


def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_column(engine: Engine, table_name: str, column_name: str, ddl: str) -> None:
    inspector = inspect(engine)
    try:
        columns = {col["name"] for col in inspector.get_columns(table_name)}
    except Exception:
        return

    if column_name in columns:
        return

    statement = text(f"ALTER TABLE {table_name} ADD COLUMN {ddl}")
    try:
        with engine.begin() as connection:
            connection.execute(statement)
        print(f"[PATCH] Added missing column '{column_name}' to '{table_name}' table")
    except Exception as exc:
        print(f"[WARN] Failed to add column '{column_name}' to '{table_name}': {exc}")


def _apply_schema_patches() -> None:
    """Apply simple schema migrations for legacy databases."""
    _ensure_column(engine, "users", "department", "department VARCHAR(255) NULL")
    _ensure_column(engine, "users", "position", "position VARCHAR(255) NULL")
    _ensure_column(
        engine,
        "users",
        "updated_at",
        "updated_at DATETIME(6) NULL DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6)",
    )
    _ensure_column(engine, "users", "last_login", "last_login DATETIME(6) NULL")
    _ensure_column(engine, "users", "feedback_route", "feedback_route VARCHAR(255) NULL")
    _ensure_column(engine, "users", "is_approved", "is_approved TINYINT(1) NOT NULL DEFAULT 0")
    _ensure_user_timestamp_defaults()


def _ensure_user_timestamp_defaults() -> None:
    if not DATABASE_URL.startswith("mysql"):
        return

    try:
        database_name = engine.url.database
        if not database_name:
            return

        with engine.connect() as connection:
            column_info = connection.execute(
                text(
                    """
                    SELECT COLUMN_DEFAULT, IS_NULLABLE
                    FROM information_schema.columns
                    WHERE table_schema = :schema
                      AND table_name = 'users'
                      AND column_name = 'created_at'
                    """
                ),
                {"schema": database_name},
            ).mappings().first()

        if column_info and column_info.get("COLUMN_DEFAULT") and column_info.get("IS_NULLABLE") == "NO":
            return

        with engine.begin() as connection:
            connection.execute(text("UPDATE users SET created_at = NOW(6) WHERE created_at IS NULL"))
            connection.execute(
                text(
                    "ALTER TABLE users MODIFY created_at DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)"
                )
            )
    except Exception as exc:
        print(f"[WARN] Failed to enforce created_at default: {exc}")


# Initialize database on import
try:
    init_db()
    _bootstrap_seed_accounts()
except Exception as e:
    print("=" * 60)
    print("[ERROR] Database Initialization Failed")
    print("=" * 60)
    print(f"Error: {str(e)}")
    print("\nTroubleshooting Steps:")
    print("1. Check if MySQL server is running")
    print("2. Verify database exists and user has permissions")
    print("3. Ensure DATABASE_URL in .env is correct")
    print("4. Run test_db_connection.py to verify connection")
    print("5. Check logs for detailed error messages")
