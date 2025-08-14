# backend/routers/camps.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.db import SessionLocal                 # ✅ correct import
from backend.models.camp import Camp
from backend.models.animal import Animal

router = APIRouter(prefix="/camps", tags=["camps"])

# ---------- DB dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Schemas ----------
class CampIn(BaseModel):
    name: Optional[str] = None

class CampOut(BaseModel):
    # Pydantic v2 config
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    animal_count: int = 0

# ---------- Helpers ----------
def _count_animals_in_camp(db: Session, camp_id: int) -> int:
    return int(
        db.execute(
            select(func.count(Animal.id)).where(
                Animal.camp_id == camp_id,
                Animal.deceased == False,  # noqa: E712
            )
        ).scalar() or 0
    )

def _out(db: Session, c: Camp) -> CampOut:
    return CampOut(id=c.id, name=c.name, animal_count=_count_animals_in_camp(db, c.id))

# ---------- Routes ----------
@router.get("/")
def list_camps(db: Session = Depends(get_db)):
    # Build counts dict excluding deceased
    counts = dict(
        db.execute(
            select(Animal.camp_id, func.count(Animal.id))
            .where(Animal.deceased == False)  # noqa: E712
            .group_by(Animal.camp_id)
        ).all()
    )
    camps = db.execute(select(Camp).order_by(Camp.name)).scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "description": getattr(c, "description", None),
            "animal_count": int(counts.get(c.id, 0)),
        }
        for c in camps
    ]

@router.post("/", response_model=CampOut, status_code=status.HTTP_201_CREATED)
def create_camp(payload: CampIn, db: Session = Depends(get_db)):
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Camp name is required")
    c = Camp(name=name)
    db.add(c)
    db.commit()
    db.refresh(c)
    return _out(db, c)

@router.patch("/{camp_id}", response_model=CampOut)
def update_camp(camp_id: int, payload: CampIn, db: Session = Depends(get_db)):
    c = db.get(Camp, camp_id)
    if not c:
        raise HTTPException(status_code=404, detail="Camp not found")
    if payload.name is not None:
        new_name = (payload.name or "").strip()
        if new_name:
            c.name = new_name
    db.commit()
    db.refresh(c)
    return _out(db, c)

@router.delete("/{camp_id}")
def delete_camp(camp_id: int, db: Session = Depends(get_db)):
    c = db.get(Camp, camp_id)
    if not c:
        raise HTTPException(status_code=404, detail="Camp not found")
    # Optional guard: block delete if animals exist
    # if _count_animals_in_camp(db, c.id) > 0:
    #     raise HTTPException(status_code=400, detail="Camp has animals; move them first.")
    db.delete(c)
    db.commit()
    return {"ok": True}
