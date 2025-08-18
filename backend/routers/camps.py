from typing import Optional
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.db import SessionLocal
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
    description: Optional[str] = None
    greenfeed: Optional[bool] = False
    greenfeed_planting_date: Optional[str] = None
    greenfeed_amount: Optional[float] = None
    fertilised_date: Optional[str] = None
    fertilised_amount: Optional[float] = None
    grazed_status: Optional[str] = "N"
    grazed_out_date: Optional[str] = None
    notes: Optional[str] = None

class CampOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    description: Optional[str] = None
    greenfeed: Optional[bool] = False
    greenfeed_planting_date: Optional[str] = None
    greenfeed_amount: Optional[float] = None
    fertilised_date: Optional[str] = None
    fertilised_amount: Optional[float] = None
    grazed_status: Optional[str] = "N"
    grazed_out_date: Optional[str] = None
    animal_count: int = 0
    notes: Optional[str] = None

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

def _parse_date(d):
    if not d:
        return None
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        try:
            return datetime.strptime(d, "%Y-%m-%d").date()
        except Exception:
            return None
    return None

def _out(db: Session, c: Camp) -> CampOut:
    return CampOut(
        id=c.id,
        name=c.name,
        description=getattr(c, "description", None),
        greenfeed=getattr(c, "greenfeed", False),
        greenfeed_planting_date=str(getattr(c, "greenfeed_planting_date", "")) if getattr(c, "greenfeed_planting_date", None) else None,
        greenfeed_amount=getattr(c, "greenfeed_amount", None),
        fertilised_date=str(getattr(c, "fertilised_date", "")) if getattr(c, "fertilised_date", None) else None,
        fertilised_amount=getattr(c, "fertilised_amount", None),
        grazed_status=getattr(c, "grazed_status", "N"),
        grazed_out_date=str(getattr(c, "grazed_out_date", "")) if getattr(c, "grazed_out_date", None) else None,
        animal_count=_count_animals_in_camp(db, c.id),
        notes=getattr(c, "notes", None)
    )

# ---------- Routes ----------
@router.get("/")
def list_camps(db: Session = Depends(get_db)):
    counts = dict(
        db.execute(
            select(Animal.camp_id, func.count(Animal.id))
            .where(Animal.deceased == False)
            .group_by(Animal.camp_id)
        ).all()
    )
    camps = db.execute(select(Camp).order_by(Camp.name)).scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "description": getattr(c, "description", None),
            "greenfeed": getattr(c, "greenfeed", False),
            "greenfeed_planting_date": str(getattr(c, "greenfeed_planting_date", "")) if getattr(c, "greenfeed_planting_date", None) else None,
            "greenfeed_amount": getattr(c, "greenfeed_amount", None),
            "fertilised_date": str(getattr(c, "fertilised_date", "")) if getattr(c, "fertilised_date", None) else None,
            "fertilised_amount": getattr(c, "fertilised_amount", None),
            "grazed_status": getattr(c, "grazed_status", "N"),
            "grazed_out_date": str(getattr(c, "grazed_out_date", "")) if getattr(c, "grazed_out_date", None) else None,
            "animal_count": int(counts.get(c.id, 0)),
            "notes": getattr(c, "notes", None),
        }
        for c in camps
    ]

@router.post("/", response_model=CampOut, status_code=status.HTTP_201_CREATED)
def create_camp(payload: CampIn, db: Session = Depends(get_db)):
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Camp name is required")
    c = Camp(
        name=name,
        description=payload.description,
        greenfeed=payload.greenfeed,
        greenfeed_planting_date=_parse_date(payload.greenfeed_planting_date),
        greenfeed_amount=payload.greenfeed_amount,
        fertilised_date=_parse_date(payload.fertilised_date),
        fertilised_amount=payload.fertilised_amount,
        grazed_status=payload.grazed_status,
        grazed_out_date=_parse_date(payload.grazed_out_date),
        notes=payload.notes,
    )
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
    if payload.description is not None:
        c.description = payload.description
    if payload.greenfeed is not None:
        c.greenfeed = payload.greenfeed
    if payload.greenfeed_planting_date is not None:
        c.greenfeed_planting_date = _parse_date(payload.greenfeed_planting_date)
    if payload.greenfeed_amount is not None:
        c.greenfeed_amount = payload.greenfeed_amount
    if payload.fertilised_date is not None:
        c.fertilised_date = _parse_date(payload.fertilised_date)
    if payload.fertilised_amount is not None:
        c.fertilised_amount = payload.fertilised_amount
    if payload.grazed_status is not None:
        c.grazed_status = payload.grazed_status
    if payload.grazed_out_date is not None:
        c.grazed_out_date = _parse_date(payload.grazed_out_date)
    if payload.notes is not None:
        c.notes = payload.notes
    db.commit()
    db.refresh(c)
    return _out(db, c)

@router.delete("/{camp_id}")
def delete_camp(camp_id: int, db: Session = Depends(get_db)):
    c = db.get(Camp, camp_id)
    if not c:
        raise HTTPException(status_code=404, detail="Camp not found")
    db.delete(c)
    db.commit()
    return {"ok": True}