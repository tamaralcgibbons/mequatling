from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime

class FeedBase(BaseModel):
    name: str
    unit: str
    current_stock: Optional[float] = 0.0
    notes: Optional[str] = None

class FeedCreate(FeedBase):
    pass

class FeedUpdate(FeedBase):
    pass

class FeedOut(FeedBase):
    id: int

    class Config:
        orm_mode = True

class FeedEventBase(BaseModel):
    feed_id: int
    event_type: str  # "in", "out", "mix"
    amount: float
    date: datetime
    reason: Optional[str] = None
    output_feed_id: Optional[int] = None
    components: Optional[Dict[int, float]] = None  # For mix events

class FeedEventOut(FeedEventBase):
    id: int

    class Config:
        orm_mode = True

# --- Feed Stocktake Event schemas ---
class FeedStocktakeEventIn(BaseModel):
    feed_id: int
    recorded_stock: float
    date: datetime
    notes: Optional[str] = None

class FeedStocktakeEventOut(FeedStocktakeEventIn):
    id: int

    class Config:
        orm_mode = True