from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from backend.db import Base
from sqlalchemy.orm import relationship
from datetime import datetime

class Fertiliser(Base):
    __tablename__ = "fertilisers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    unit = Column(String(20), nullable=False)  # e.g. kg, L, bag
    current_stock = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    stocktakes = relationship("FertiliserStocktakeEvent", back_populates="fertiliser", cascade="all, delete-orphan")  # <-- Added

class FertiliserEvent(Base):
    __tablename__ = "fertiliser_events"

    id = Column(Integer, primary_key=True, index=True)
    fertiliser_id = Column(Integer, nullable=False)
    event_type = Column(String(20), nullable=False)  # "in", "out"
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=True)

class FertiliserStocktakeEvent(Base):
    __tablename__ = "fertiliser_stocktake_events"

    id = Column(Integer, primary_key=True, index=True)
    fertiliser_id = Column(Integer, ForeignKey("fertilisers.id", ondelete="CASCADE"), nullable=False, index=True)
    recorded_stock = Column(Float, nullable=False)  # The manually counted stock
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    fertiliser = relationship("Fertiliser", back_populates="stocktakes")