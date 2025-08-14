from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from backend.db import Base

class Fuel(Base):
    __tablename__ = "fuels"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String(100), unique=True, nullable=False)  # e.g. diesel, petrol
    unit = Column(String(20), nullable=False)  # e.g. L, gal
    current_stock = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)

class FuelEvent(Base):
    __tablename__ = "fuel_events"

    id = Column(Integer, primary_key=True, index=True)
    fuel_id = Column(Integer, nullable=False)
    event_type = Column(String(20), nullable=False)  # "in", "out"
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=True)