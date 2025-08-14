from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.orm import relationship
from backend.db import Base

class Feed(Base):
    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    unit = Column(String(20), nullable=False)  # e.g. kg, L, bag
    current_stock = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)

class FeedEvent(Base):
    __tablename__ = "feed_events"

    id = Column(Integer, primary_key=True, index=True)
    feed_id = Column(Integer, nullable=False)
    event_type = Column(String(20), nullable=False)  # "in", "out", "mix"
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=True)
    # For mix events, you may want to track output product and components
    output_feed_id = Column(Integer, nullable=True)
    components = Column(Text, nullable=True)  # JSON string