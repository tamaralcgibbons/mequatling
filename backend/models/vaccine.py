from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Float, JSON
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from backend.db import Base

# JSON that works on SQLite (JSON) and Postgres (JSONB)
JSON_COMPAT = JSON().with_variant(JSONB, "postgresql")

class Vaccine(Base):
    __tablename__ = "vaccines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)

    # Defaults for UI convenience
    default_dose = Column(Float, nullable=True)       # e.g., 2.0
    unit = Column(String(32), nullable=True)          # e.g., "mL"
    methods = Column(JSON_COMPAT, nullable=False, default=list)  # ["IM","SC","oral"]

    # Simple running balance; decremented when vaccinations are recorded
    current_stock = Column(Float, nullable=False, default=0.0)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # relationships
    vaccinations = relationship("Vaccination", back_populates="vaccine", cascade="all, delete-orphan")
    stock_movements = relationship("StockLedger", back_populates="vaccine", cascade="all, delete-orphan")

    def touch(self):
        self.updated_at = datetime.utcnow()
