from typing import Optional
from pydantic import BaseModel


class CampIn(BaseModel):
    name: Optional[str] = None


class CampOut(BaseModel):
    id: int
    name: str
    animal_count: int = 0

    class Config:
        orm_mode = True
