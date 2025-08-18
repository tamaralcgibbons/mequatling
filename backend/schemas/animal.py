from typing import List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime


class AnimalIn(BaseModel):
    tag_number: Optional[str] = None
    name: Optional[str] = None
    sex: Optional[str] = None            # 'F' | 'M'
    birth_date: Optional[str] = None     # 'YYYY-MM-DD'
    pregnancy_status: Optional[str] = None  # 'pregnant' | 'open' | None
    camp_id: Optional[int] = None
    group_id: Optional[int] = None
    notes: Optional[str] = None

    # Parity / calves
    has_calved: Optional[bool] = False
    calves_count: Optional[int] = 0
    calves_tags: Optional[List[str]] = Field(default_factory=list)

    # Pregnancy test fields
    pregnant: Optional[bool] = None
    pregnancy_duration: Optional[str] = None
    pregnancy_date: Optional[str] = None

    @validator("sex")
    def _upper_sex(cls, v):
        return v.upper() if isinstance(v, str) else v

    @validator("birth_date")
    def _date_fmt(cls, v):
        if not v:
            return None
        datetime.strptime(v, "%Y-%m-%d")
        return v

    @validator("pregnancy_status")
    def _preg_values(cls, v):
        if v is None:
            return v
        v2 = v.lower()
        if v2 not in ("pregnant", "open"):
            raise ValueError("pregnancy_status must be 'pregnant' or 'open'")
        return v2


class AnimalOut(BaseModel):
    id: int
    tag_number: Optional[str]
    name: Optional[str]
    sex: Optional[str]
    birth_date: Optional[str]
    pregnancy_status: Optional[str]
    camp_id: Optional[int]
    group_id: Optional[int]
    notes: Optional[str]
    photo_path: Optional[str]

    deceased: bool
    killed: Optional[bool]
    death_reason: Optional[str]

    has_calved: bool
    calves_count: int
    calves_tags: List[str]

    # Pregnancy test fields
    pregnant: Optional[bool]
    pregnancy_duration: Optional[str]
    pregnancy_date: Optional[str]

    mother_id: Optional[int]

    class Config:
        orm_mode = True


class DeceasedIn(BaseModel):
    killed: Optional[bool] = False
    reason: Optional[str] = None
