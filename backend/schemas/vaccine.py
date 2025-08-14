from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

# --- Vaccine schemas ---
class VaccineBase(BaseModel):
    name: Optional[str] = None
    default_dose: Optional[float] = None
    unit: Optional[str] = None
    methods: Optional[List[str]] = None
    current_stock: Optional[float] = None
    notes: Optional[str] = None

class VaccineCreate(VaccineBase):
    name: str
    default_dose: float
    unit: str
    methods: List[str]
    current_stock: float

class VaccineUpdate(VaccineBase):
    pass

class VaccineOut(VaccineBase):
    id: int
    name: str
    default_dose: float
    unit: str
    methods: List[str]
    current_stock: float
    notes: Optional[str] = None

    class Config:
        orm_mode = True

# --- Vaccine Event schemas ---
class VaccineEventIn(BaseModel):
    vaccine_id: int
    event_type: str  # "in", "out", "adjustment"
    amount: float
    date: datetime
    reason: Optional[str] = None

class VaccineEventOut(VaccineEventIn):
    id: int

    class Config:
        orm_mode = True

# --- Vaccine Waste Event schemas ---
class VaccineWasteEventIn(BaseModel):
    vaccine_id: int
    amount: float
    date: datetime
    reason: Optional[str] = None

class VaccineWasteEventOut(VaccineWasteEventIn):
    id: int

    class Config:
        orm_mode = True