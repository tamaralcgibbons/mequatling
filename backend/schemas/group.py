from typing import List, Optional
from pydantic import BaseModel


class GroupIn(BaseModel):
    name: Optional[str] = None
    camp_id: Optional[int] = None
    animal_ids: Optional[List[int]] = None  # if provided, sync membership


class GroupOut(BaseModel):
    id: int
    name: str
    camp_id: Optional[int] = None
    animal_count: int = 0

    class Config:
        orm_mode = True


class MoveCampIn(BaseModel):
    camp_id: int
