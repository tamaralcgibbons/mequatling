from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FertiliserBase(BaseModel):
    name: str
    unit: str
    current_stock: Optional[float] = 0.0
    notes: Optional[str] = None

class FertiliserCreate(FertiliserBase):
    pass

class FertiliserUpdate(FertiliserBase):
    pass

class FertiliserOut(FertiliserBase):
    id: int

    class Config:
        orm_mode = True

class FertiliserEventBase(BaseModel):
    fertiliser_id: int
    event_type: str  # "in", "out"
    amount: float
    date: datetime
    reason: Optional[str] = None

class FertiliserEventOut(FertiliserEventBase):
    id: int

    class Config:
        orm_mode = True