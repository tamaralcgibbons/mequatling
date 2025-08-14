from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from backend.db import Base

class Fertiliser(Base):
    __tablename__ = "fertilisers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    unit = Column(String(20), nullable=False)  # e.g. kg, L, bag
    current_stock = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)

class FertiliserEvent(Base):
    __tablename__ = "fertiliser_events"

    id = Column(Integer, primary_key=True, index=True)
    fertiliser_id = Column(Integer, nullable=False)
    event_type = Column(String(20), nullable=False)  # "in", "out"
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=True)