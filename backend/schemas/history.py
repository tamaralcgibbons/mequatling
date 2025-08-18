from pydantic import BaseModel
from typing import Optional

class AnimalHistoryOut(BaseModel):
    id: int
    animal_id: int
    event_type: str
    event_date: str  # ISO date string
    reason: Optional[str] = None
    name: Optional[str] = None

    class Config:
        orm_mode = True