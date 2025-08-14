from typing import List, Optional
from pydantic import BaseModel


class VaccineIn(BaseModel):
    name: Optional[str] = None
    default_dose: Optional[float] = None
    unit: Optional[str] = None
    methods: Optional[List[str]] = None
    current_stock: Optional[float] = 0.0


class VaccineOut(BaseModel):
    id: int
    name: str
    default_dose: Optional[float] = None
    unit: Optional[str] = None
    methods: List[str] = []
    current_stock: float = 0.0

    class Config:
        orm_mode = True
