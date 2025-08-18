from pydantic import BaseModel
from typing import Optional
from datetime import date

class CampBase(BaseModel):
    name: str
    description: Optional[str] = None
    greenfeed: Optional[bool] = False
    greenfeed_planting_date: Optional[date] = None
    greenfeed_amount: Optional[float] = None
    fertilised_date: Optional[date] = None
    fertilised_amount: Optional[float] = None
    grazed_status: Optional[str] = "N"
    grazed_out_date: Optional[date] = None
    notes: Optional[str] = None

class CampCreate(CampBase):
    pass

class CampUpdate(CampBase):
    pass

class CampOut(CampBase):
    id: int

    class Config:
        orm_mode = True