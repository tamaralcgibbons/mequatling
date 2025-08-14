# backend/routers/vaccinations.py
from datetime import datetime, date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, field_validator, ConfigDict
from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from backend.db import SessionLocal                    # ✅ correct import
from backend.models.vaccination import Vaccination
from backend.models.vaccine import Vaccine
from backend.models.animal import Animal
from backend.models.group import Group
from backend.models.camp import Camp

router = APIRouter(prefix="/vaccinations", tags=["vaccinations"])

# ---------- DB dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Schemas ----------
class GroupVaccIn(BaseModel):
    group_id: int
    vaccine_id: int
    date: str
    dose_per_animal: float
    method: Optional[str] = None

    @field_validator("date")
    @classmethod
    def _vd(cls, v: str) -> str:
        datetime.strptime(v, "%Y-%m-%d")
        return v

class AnimalVaccIn(BaseModel):
    animal_id: int
    vaccine_id: int
    date: str
    dose: float
    method: Optional[str] = None
    source: Optional[str] = "manual"  # 'group' | 'manual'

    @field_validator("date")
    @classmethod
    def _vd(cls, v: str) -> str:
        datetime.strptime(v, "%Y-%m-%d")
        return v

class VaccinationOut(BaseModel):
    # We construct this manually, so no need for from_attributes
    id: int
    date: Optional[str]
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

# ---------- Helpers ----------
def _parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()

def _dec_stock(vaccine: Vaccine, amount: float):
    """Basic stock decrement; never below zero."""
    cur = float(vaccine.current_stock or 0.0)
    cur -= float(amount or 0.0)
    vaccine.current_stock = cur if cur > 0 else 0.0

# ---------- Endpoints ----------
@router.post("/group", status_code=status.HTTP_200_OK)
def vaccinate_group(payload: GroupVaccIn, db: Session = Depends(get_db)):
    g = db.get(Group, payload.group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    vax = db.get(Vaccine, payload.vaccine_id)
    if not vax:
        raise HTTPException(status_code=404, detail="Vaccine not found")

    dose = float(payload.dose_per_animal)
    if dose <= 0:
        raise HTTPException(status_code=400, detail="dose_per_animal must be > 0")

    vacc_date = _parse_date(payload.date)

    # current members at time of recording (exclude deceased)
    members = db.execute(
        select(Animal).where(Animal.group_id == g.id, Animal.deceased == False)  # noqa: E712
    ).scalars().all()
    if not members:
        return {"ok": True, "applied": 0}

    # write one vaccination per member
    for a in members:
        rec = Vaccination(
            animal_id=a.id,
            vaccine_id=vax.id,
            date=vacc_date,
            dose=dose,
            method=payload.method,
            source="group",
        )
        db.add(rec)

    # decrement stock
    _dec_stock(vax, dose * len(members))
    db.commit()
    return {"ok": True, "applied": len(members), "stock": vax.current_stock}

@router.post("/animal", status_code=status.HTTP_200_OK)
def vaccinate_animal(payload: AnimalVaccIn, db: Session = Depends(get_db)):
    a = db.get(Animal, payload.animal_id)
    if not a:
        raise HTTPException(status_code=404, detail="Animal not found")
    vax = db.get(Vaccine, payload.vaccine_id)
    if not vax:
        raise HTTPException(status_code=404, detail="Vaccine not found")

    dose = float(payload.dose)
    if dose <= 0:
        raise HTTPException(status_code=400, detail="dose must be > 0")

    rec = Vaccination(
        animal_id=a.id,
        vaccine_id=vax.id,
        date=_parse_date(payload.date),
        dose=dose,
        method=payload.method,
        source=payload.source or "manual",
    )
    db.add(rec)

    # decrement stock for manual entries; for 'group' we assume already decremented
    if (payload.source or "manual") == "manual":
        _dec_stock(vax, dose)

    db.commit()
    return {"ok": True, "stock": vax.current_stock}

@router.get("", response_model=List[VaccinationOut])
def list_vaccinations(
    db: Session = Depends(get_db)):
    group_id: Optional[int] = Query(None),
    vaccine_id: Optional[int] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    q: Optional[str] = Query(None),

    q_v = (
        select(Vaccination, Animal, Vaccine, Group, Camp)
        .join(Animal, Vaccination.animal_id == Animal.id)
        .join(Vaccine, Vaccination.vaccine_id == Vaccine.id)
        .outerjoin(Group, Animal.group_id == Group.id)
        .outerjoin(Camp, Animal.camp_id == Camp.id)
    )

    conditions = []
    if group_id is not None:
        conditions.append(Group.id == group_id)
    if vaccine_id is not None:
        conditions.append(Vaccination.vaccine_id == vaccine_id)
    if date_from:
        conditions.append(Vaccination.date >= _parse_date(date_from))
    if date_to:
        conditions.append(Vaccination.date <= _parse_date(date_to))
    if source:
        conditions.append(Vaccination.source == source)

    if conditions:
        q_v = q_v.where(and_(*conditions))

    rows = db.execute(
        q_v.order_by(Vaccination.date.desc(), Vaccination.id.desc())
    ).all()

    out: List[VaccinationOut] = []
    for vrec, a, v, g, c in rows:
        out.append(
            VaccinationOut(
                id=vrec.id,
                date=vrec.date.isoformat() if vrec.date else None,
                animal_id=a.id,
                animal_tag=a.tag_number,
                animal_name=a.name,
                group_id=(g.id if g else None),
                group_name=(g.name if g else None),
                vaccine_id=v.id,
                vaccine_name=v.name,
                dose=float(vrec.dose or 0),
                unit=v.unit,
                method=vrec.method,
                source=vrec.source,
                camp_id=(c.id if c else None),
                camp_name=(c.name if c else None),
            )
        )

    # simple client-side contains filter on text fields
    if q:
        ql = q.lower()
        out = [
            r
            for r in out
            if (r.animal_tag and ql in r.animal_tag.lower())
            or (r.animal_name and ql in r.animal_name.lower())
            or (r.vaccine_name and ql in r.vaccine_name.lower())
            or (r.group_name and ql in r.group_name.lower())
        ]

    return out
