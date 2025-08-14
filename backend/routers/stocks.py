# backend/routers/stocks.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.db import SessionLocal                 # ✅ correct import
from backend.models.vaccine import Vaccine

router = APIRouter(prefix="/stocks", tags=["stocks"])

# ---------- DB dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Schemas ----------
class VaccineIn(BaseModel):
    name: Optional[str] = None
    default_dose: Optional[float] = None
    unit: Optional[str] = None
    methods: Optional[List[str]] = None
    current_stock: Optional[float] = 0.0

class VaccineOut(BaseModel):
    # Pydantic v2 config
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    default_dose: Optional[float] = None
    unit: Optional[str] = None
    methods: List[str] = Field(default_factory=list)
    current_stock: float = 0.0

# ---------- Helpers ----------
def _out(v: Vaccine) -> VaccineOut:
    return VaccineOut(
        id=v.id,
        name=v.name,
        default_dose=v.default_dose,
        unit=v.unit,
        methods=(v.methods or []),
        current_stock=float(v.current_stock or 0),
    )

# ---------- Routes ----------
@router.get("/vaccines", response_model=List[VaccineOut])
def list_vaccines(db: Session = Depends(get_db)):
    rows = db.execute(select(Vaccine).order_by(Vaccine.id.desc())).scalars().all()
    return [_out(v) for v in rows]

@router.post("/vaccines", response_model=VaccineOut, status_code=status.HTTP_201_CREATED)
def create_vaccine(payload: VaccineIn, db: Session = Depends(get_db)):
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Vaccine name is required")
    v = Vaccine(
        name=name,
        default_dose=payload.default_dose,
        unit=(payload.unit or None),
        methods=(payload.methods or []),
        current_stock=float(payload.current_stock or 0),
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return _out(v)

@router.patch("/vaccines/{vaccine_id}", response_model=VaccineOut)
def update_vaccine(vaccine_id: int, payload: VaccineIn, db: Session = Depends(get_db)):
    v = db.get(Vaccine, vaccine_id)
    if not v:
        raise HTTPException(status_code=404, detail="Vaccine not found")
    if payload.name is not None:
        v.name = (payload.name or "").strip() or v.name
    if payload.default_dose is not None:
        v.default_dose = payload.default_dose
    if payload.unit is not None:
        v.unit = (payload.unit or None)
    if payload.methods is not None:
        v.methods = payload.methods or []
    if payload.current_stock is not None:
        v.current_stock = float(payload.current_stock)
    db.commit()
    db.refresh(v)
    return _out(v)

@router.delete("/vaccines/{vaccine_id}")
def delete_vaccine(vaccine_id: int, db: Session = Depends(get_db)):
    v = db.get(Vaccine, vaccine_id)
    if not v:
        raise HTTPException(status_code=404, detail="Vaccine not found")
    db.delete(v)
    db.commit()
    return {"ok": True}
