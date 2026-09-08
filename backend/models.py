"""
models.py
---------
Database entity definitions for calculation audit/telemetry logs.
"""

from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime

from database import Base


class CalculationLog(Base):
    """One row per calculate/compare request, used for usage analytics."""

    __tablename__ = "calculation_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    regime = Column(String(16), nullable=False)              # "new" | "old" | "compare"
    gross_income = Column(Float, nullable=False)
    recommended_regime = Column(String(16), nullable=True)   # populated for "compare" rows
