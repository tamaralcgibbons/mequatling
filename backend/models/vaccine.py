from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from backend.db import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class Vaccine(Base):
    __tablename__ = "vaccines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    default_dose = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)  # e.g. mL, dose
    methods = Column(Text, nullable=True)      # store as JSON string
    current_stock = Column(Float, default=0.0)
    stock_movements = relationship("StockLedger", back_populates="vaccine", cascade="all, delete-orphan")
    vaccinations = relationship("Vaccination", back_populates="vaccine", cascade="all, delete-orphan")
    events = relationship("VaccineEvent", back_populates="vaccine", cascade="all, delete-orphan")
    notes = Column(Text, nullable=True)
    stocktakes = relationship("VaccineStocktakeEvent", back_populates="vaccine", cascade="all, delete-orphan")  # <-- Added

class VaccineEvent(Base):
    __tablename__ = "vaccine_events"

    id = Column(Integer, primary_key=True, index=True)
    vaccine_id = Column(Integer, ForeignKey("vaccines.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(32), nullable=False)  # e.g., "in", "out", "adjustment"
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    reason = Column(String(255), nullable=True)

    vaccine = relationship("Vaccine", back_populates="events")

class VaccineWasteEvent(Base):
    __tablename__ = "vaccine_waste_events"

    id = Column(Integer, primary_key=True, index=True)
    vaccine_id = Column(Integer, nullable=False)
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=True)

class VaccineStocktakeEvent(Base):
    __tablename__ = "vaccine_stocktake_events"

    id = Column(Integer, primary_key=True, index=True)
    vaccine_id = Column(Integer, ForeignKey("vaccines.id", ondelete="CASCADE"), nullable=False, index=True)
    recorded_stock = Column(Float, nullable=False)  # The manually counted stock
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    vaccine = relationship("Vaccine", back_populates="stocktakes")