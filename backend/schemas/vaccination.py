from typing import Optional, List
from pydantic import BaseModel, validator
from datetime import datetime


class GroupVaccIn(BaseModel):
    group_id: int
    vaccine_id: int
    date: str                 # 'YYYY-MM-DD'
    dose_per_animal: float
    method: Optional[str] = None

    @validator("date")
    def _vd(cls, v):
        datetime.strptime(v, "%Y-%m-%d")
        return v


class AnimalVaccIn(BaseModel):
    animal_id: int
    vaccine_id: int
    date: str                 # 'YYYY-MM-DD'
    dose: float
    method: Optional[str] = None
    source: Optional[str] = "manual"   # 'group' | 'manual'

    @validator("date")
    def _vd(cls, v):
        datetime.strptime(v, "%Y-%m-%d")
        return v


class VaccinationOut(BaseModel):
    id: int
    date: str

    animal_id: int
    animal_tag: Optional[str]
    animal_name: Optional[str]

    group_id: Optional[int]
    group_name: Optional[str]

    vaccine_id: int
    vaccine_name: str

    dose: float
    unit: Optional[str]
    method: Optional[str]
    source: Optional[str]

    camp_id: Optional[int]
    camp_name: Optional[str]

    class Config:
        orm_mode = True
