from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class GroupIn(BaseModel):
    name: Optional[str] = None
    camp_id: Optional[int] = None
    animal_ids: Optional[List[int]] = None  # if provided, sync membership
    notes: Optional[str] = None

class AnimalSummary(BaseModel):
    id: int
    tag_number: str
    sex: str
    current_weight: Optional[float] = None
    pregnant: Optional[bool] = None
    pregnancy_duration: Optional[str] = None
    pregnancy_date: Optional[str] = None

class GroupOut(BaseModel):
    id: int
    name: str
    camp_id: Optional[int] = None
    animal_count: int
    notes: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    animals: List[AnimalSummary] = []
    avg_weight: Optional[float] = None

    class Config:
        orm_mode = True


class MoveCampIn(BaseModel):
    camp_id: int

class GroupMovementEventIn(BaseModel):
    group_id: int
    from_camp_id: Optional[int]
    to_camp_id: int
    date: datetime
    reason: Optional[str] = None
