"""
database.py
------------
SQLAlchemy engine/session configuration for calculation telemetry.
Targets AWS RDS PostgreSQL in production; falls back to local Postgres
for development via the DATABASE_URL environment variable.
"""

import os
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://tax_user:tax_pass@localhost:5432/tax_calculator",
)

# pool_pre_ping guards against RDS connections dropped after idling.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency yielding a request-scoped DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """Create tables on startup if they don't already exist (dev convenience)."""
    from models import CalculationLog  # noqa: F401  (ensures model is registered)
    Base.metadata.create_all(bind=engine)


def log_calculation_async(
    regime: str,
    gross_income: float,
    recommended_regime: Optional[str] = None,
) -> None:
    """
    Persist a calculation audit row. Designed to be scheduled via
    FastAPI's BackgroundTasks so it runs *after* the HTTP response has
    already been sent -- a slow or unreachable database never adds
    latency to the user-facing request, and any failure here is
    swallowed so telemetry issues can never break the calculator.
    """
    from models import CalculationLog  # local import avoids circular import

    db = SessionLocal()
    try:
        db.add(
            CalculationLog(
                regime=regime,
                gross_income=gross_income,
                recommended_regime=recommended_regime,
            )
        )
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
