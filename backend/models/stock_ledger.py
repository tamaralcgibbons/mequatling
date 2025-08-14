from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from backend.db import Base

class StockLedger(Base):
    """
    Optional stock movement log for vaccines.
    Records every increment/decrement so you can audit stock.
    """
    __tablename__ = "stock_ledger"

    id = Column(Integer, primary_key=True, index=True)
    vaccine_id = Column(Integer, ForeignKey("vaccines.id", ondelete="CASCADE"), nullable=False, index=True)

    # +ve for additions, -ve for consumption
    delta = Column(Float, nullable=False)

    reason = Column(String(255), nullable=True)   # e.g., "group vaccination", "manual", "adjustment"
    ref_type = Column(String(32), nullable=True)  # e.g., "vaccination_group", "vaccination_animal", "adjustment"
    ref_id = Column(Integer, nullable=True)       # optional external id

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # optional running totals
    balance_after = Column(Float, nullable=True)

    # relationships
    vaccine = relationship("Vaccine", back_populates="stock_movements")
