from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.db import Base
from datetime import datetime

class Feed(Base):
    __tablename__ = "feeds"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    unit = Column(String(20), nullable=False)  # e.g. kg, L, bag
    current_stock = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    stocktakes = relationship("FeedStocktakeEvent", back_populates="feed", cascade="all, delete-orphan")  # <-- Added

class FeedEvent(Base):
    __tablename__ = "feed_events"

    id = Column(Integer, primary_key=True, index=True)
    feed_id = Column(Integer, nullable=False)
    event_type = Column(String(20), nullable=False)  # "in", "out", "mix"
    amount = Column(Float, nullable=False)
    date = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=True)
    output_feed_id = Column(Integer, nullable=True)
    components = Column(Text, nullable=True)  # JSON string

class FeedStocktakeEvent(Base):
    __tablename__ = "feed_stocktake_events"

    id = Column(Integer, primary_key=True, index=True)
    feed_id = Column(Integer, ForeignKey("feeds.id", ondelete="CASCADE"), nullable=False, index=True)
    recorded_stock = Column(Float, nullable=False)  # The manually counted stock
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(Text, nullable=True)

    feed = relationship("Feed", back_populates="stocktakes")