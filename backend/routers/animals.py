# backend/routers/animals.py
from datetime import datetime
import os
from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.db import SessionLocal             # ✅ correct import
from backend.models.animal import Animal
from backend.models.history import AnimalHistory

MEDIA_PHOTOS_DIR = "backend/media/photos"
os.makedirs(MEDIA_PHOTOS_DIR, exist_ok=True)

router = APIRouter(prefix="/animals", tags=["animals"])

# ---------- DB dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Schemas ----------
class AnimalIn(BaseModel):
    tag_number: Optional[str] = None
    name: Optional[str] = None
    sex: Optional[str] = None  # 'F'|'M'
    birth_date: Optional[str] = None  # 'YYYY-MM-DD'
    pregnancy_status: Optional[str] = None  # 'pregnant'|'open'|None
    camp_id: Optional[int] = None
    group_id: Optional[int] = None
    notes: Optional[str] = None
    has_calved: Optional[bool] = False
    calves_count: Optional[int] = 0
    calves_tags: Optional[List[str]] = Field(default_factory=list)
    current_weight: Optional[float] = None
    weight_date: Optional[str] = None  # 'YYYY-MM-DD'
    pregnant: Optional[bool] = None
    pregnancy_duration: Optional[str] = None
    pregnancy_date: Optional[str] = None

    @field_validator("sex", mode="before")
    @classmethod
    def upper_sex(cls, v):
        return v.upper() if isinstance(v, str) else v

    @field_validator("birth_date")
    @classmethod
    def check_date_format(cls, v):
        if v in (None, ""):
            return None
        try:
            datetime.strptime(v, "%Y-%m-%d")
        except Exception:
            raise ValueError("birth_date must be YYYY-MM-DD")
        return v

    @field_validator("pregnancy_status")
    @classmethod
    def norm_preg(cls, v):
        if v is None:
            return None
        v2 = str(v).lower()
        if v2 not in ("pregnant", "open"):
            raise ValueError("pregnancy_status must be 'pregnant' or 'open'")
        return v2

class AnimalOut(BaseModel):
    # Pydantic v2 style
    model_config = ConfigDict(from_attributes=True)

    id: int
    tag_number: Optional[str]
    name: Optional[str]
    sex: Optional[str]
    birth_date: Optional[str]  # we serialize to ISO string
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
    mother_id: Optional[int] = None
    current_weight: Optional[float]
    weight_date: Optional[str]
    pregnant: Optional[bool]
    pregnancy_duration: Optional[str]
    pregnancy_date: Optional[str]

class DeceasedIn(BaseModel):
    killed: Optional[bool] = False
    reason: Optional[str] = None
    date: Optional[str] = None

# ---------- Helpers ----------
def parse_date_str(s: Optional[str]):
    if not s:
        return None
    return datetime.strptime(s, "%Y-%m-%d").date()

def _apply_incoming(a: Animal, payload: AnimalIn):
    if payload.tag_number is not None:
        a.tag_number = payload.tag_number
    if payload.name is not None:
        a.name = payload.name
    if payload.sex is not None:
        a.sex = payload.sex
    if payload.birth_date is not None:
        a.birth_date = parse_date_str(payload.birth_date)
    if payload.pregnancy_status is not None:
        a.pregnancy_status = payload.pregnancy_status
    if payload.camp_id is not None:
        a.camp_id = payload.camp_id
    if payload.group_id is not None:
        a.group_id = payload.group_id
    if payload.notes is not None:
        a.notes = payload.notes
    if payload.current_weight is not None:
        a.current_weight = payload.current_weight
    if payload.weight_date is not None:
        a.weight_date = parse_date_str(payload.weight_date)
    if payload.pregnant is not None:
        a.pregnant = payload.pregnant
    if payload.pregnancy_duration is not None:
        a.pregnancy_duration = payload.pregnancy_duration
    if payload.pregnancy_date is not None:
        a.pregnancy_date = parse_date_str(payload.pregnancy_date)

    # Parity
    if payload.has_calved is not None:
        a.has_calved = bool(payload.has_calved)
    if payload.calves_count is not None:
        a.calves_count = int(payload.calves_count or 0)
    if payload.calves_tags is not None:
        a.calves_tags = list(payload.calves_tags or [])
    a.touch()

def _link_mother_to_calves(db: Session, mother: Animal):
    """
    Simple mother–calf linking by tag number.
    For each tag in calves_tags, find an existing animal and set its mother_id.
    Ignores 'unknown'.
    """
    if not mother.calves_tags:
        return
    tags = [t for t in mother.calves_tags if t and t.strip().lower() != "unknown"]
    if not tags:
        return
    q = db.execute(select(Animal).where(Animal.tag_number.in_(tags)))
    for calf in q.scalars().all():
        calf.mother_id = mother.id
        calf.touch()

def _serialize(a: Animal) -> dict:
    """Return plain JSON-safe dict for frontend."""
    return {
        "id": a.id,
        "tag_number": a.tag_number,
        "name": a.name,
        "sex": a.sex,
        "birth_date": a.birth_date.isoformat() if a.birth_date else None,
        "pregnancy_status": a.pregnancy_status,
        "camp_id": a.camp_id,
        "group_id": a.group_id,
        "notes": a.notes,
        "photo_path": a.photo_path,
        "deceased": a.deceased,
        "killed": a.killed,
        "death_reason": a.death_reason,
        "has_calved": a.has_calved,
        "calves_count": a.calves_count,
        "calves_tags": a.calves_tags,
        "mother_id": getattr(a, "mother_id", None),
        "created_at": a.created_at,
        "updated_at": a.updated_at,
        "current_weight": a.current_weight,
        "weight_date": a.weight_date.isoformat() if a.weight_date else None,
        "pregnant": a.pregnant,
        "pregnancy_duration": a.pregnancy_duration,
        "pregnancy_date": a.pregnancy_date.isoformat() if a.pregnancy_date else None,
    }

# ---------- Routes ----------
@router.get("/")
def list_animals(db: Session = Depends(get_db)):
    rows = db.execute(select(Animal).order_by(Animal.id.desc())).scalars().all()
    return [_serialize(a) for a in rows]

@router.post("/", response_model=AnimalOut, status_code=status.HTTP_201_CREATED)
def create_animal(payload: AnimalIn, db: Session = Depends(get_db)):
    a = Animal()
    _apply_incoming(a, payload)
    db.add(a)
    db.commit()
    db.refresh(a)

    # link mother to calves by tag numbers
    if a.has_calved and a.calves_count and a.calves_tags:
        _link_mother_to_calves(db, a)
        db.commit()
        db.refresh(a)

    # Pydantic v2 friendly serialization
    out = AnimalOut.model_validate(_serialize(a))
    return out

@router.patch("/{animal_id}", response_model=AnimalOut)
def update_animal(animal_id: int, payload: AnimalIn, db: Session = Depends(get_db)):
    a = db.get(Animal, animal_id)
    if not a:
        raise HTTPException(status_code=404, detail="Animal not found")
    _apply_incoming(a, payload)
    db.commit()
    db.refresh(a)

    if a.has_calved and a.calves_count and a.calves_tags:
        _link_mother_to_calves(db, a)
        db.commit()
        db.refresh(a)

    out = AnimalOut.model_validate(_serialize(a))
    return out

@router.post("/{animal_id}/deceased", status_code=200)
def mark_deceased(animal_id: int, payload: DeceasedIn, db: Session = Depends(get_db)):
    a = db.get(Animal, animal_id)
    if not a:
        raise HTTPException(status_code=404, detail="Animal not found")
    a.deceased = True
    a.killed = bool(payload.killed)
    a.death_reason = (payload.reason or "").strip() or None
    a.touch()
    db.commit()

    # Record history event
    event_type = "slaughtered" if a.killed else "deceased"
    event_date = datetime.utcnow().date()
    try:
        if hasattr(payload, "date") and payload.date:
            event_date = parse_date_str(payload.date)
    except Exception:
        pass
    history = AnimalHistory(
        animal_id=a.id,
        event_type=event_type,
        event_date=event_date,
        reason=a.death_reason,
    )
    db.add(history)
    db.commit()
    return {"ok": True}

@router.delete("/{animal_id}")
def delete_animal(animal_id: int, hard: bool = False, db: Session = Depends(get_db)):
    a = db.get(Animal, animal_id)
    if not a:
        raise HTTPException(status_code=404, detail="Animal not found")
    if not hard:
        raise HTTPException(
            status_code=400,
            detail="Use POST /animals/{id}/deceased or set ?hard=true to permanently delete",
        )
    db.delete(a)
    db.commit()
    return {"ok": True}

@router.post("/{animal_id}/upload-photo")
def upload_photo(animal_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    a = db.get(Animal, animal_id)
    if not a:
        raise HTTPException(status_code=404, detail="Animal not found")

    # Save file
    safe_name = f"{animal_id}_{int(datetime.utcnow().timestamp())}_{file.filename.replace(' ', '_')}"
    dest_path = os.path.join(MEDIA_PHOTOS_DIR, safe_name)
    with open(dest_path, "wb") as f:
        f.write(file.file.read())

    # API serves /media/*, so store relative URL path
    a.photo_path = f"/media/photos/{safe_name}"
    a.touch()
    db.commit()
    db.refresh(a)
    return {"photo_path": a.photo_path}

@router.get("/{animal_id}/history")
def get_animal_history(animal_id: int, db: Session = Depends(get_db)):
    rows = db.execute(
        select(AnimalHistory).where(AnimalHistory.animal_id == animal_id).order_by(AnimalHistory.event_date.desc())
    ).scalars().all()
    return [
        {
            "event_type": h.event_type,
            "event_date": h.event_date.isoformat(),
            "reason": h.reason,
        }
        for h in rows
    ]
