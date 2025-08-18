from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from backend.db import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class Fuel(Base):
    __tablename__ = "fuels"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(100), unique=True, nullable=False)  # e.g. diesel, petrol
    unit = Column(String(20), nullable=False)  # e.g. L, gal
    current_stock = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    stocktakes = relationship("FuelStocktakeEvent", back_populates="fuel", cascade="all, delete-orphan")  # <-- Added

class FuelEvent(Base):
    __tablename__ = "fuel_events"

    id = Column(Integer, primary_key=True, index=True)
    fuel_id = Column(Integer, nullable=False)
    event_type = Column(String(20), nullable=False)  # "in", "out"
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=True)

class FuelStocktakeEvent(Base):
    __tablename__ = "fuel_stocktake_events"

    id = Column(Integer, primary_key=True, index=True)
    fuel_id = Column(Integer, ForeignKey("fuels.id", ondelete="CASCADE"), nullable=False, index=True)
    recorded_stock = Column(Float, nullable=False)  # The manually counted stock
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    fuel = relationship("Fuel", back_populates="stocktakes")