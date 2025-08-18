from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class FuelBase(BaseModel):
    type: str
    unit: str
    current_stock: Optional[float] = 0.0
    notes: Optional[str] = None

class FuelCreate(FuelBase):
    pass

class FuelUpdate(FuelBase):
    pass

class FuelOut(FuelBase):
    id: int

    class Config:
        orm_mode = True

class FuelEventBase(BaseModel):
    fuel_id: int
    event_type: str  # "in", "out"
    amount: float
    date: datetime
    reason: Optional[str] = None

class FuelEventOut(FuelEventBase):
    id: int

    class Config:
        orm_mode = True

# --- Fuel Stocktake Event schemas ---
class FuelStocktakeEventIn(BaseModel):
    fuel_id: int
    recorded_stock: float
    date: datetime
    notes: Optional[str] = None

class FuelStocktakeEventOut(FuelStocktakeEventIn):
    id: int

    class Config:
        orm_mode = True