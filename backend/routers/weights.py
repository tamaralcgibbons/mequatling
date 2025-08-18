from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.models.weight import Weight
from backend.models.animal import Animal
from backend.db.session import get_db
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import sqlalchemy as sa

router = APIRouter(tags=["weights"])

class WeightIn(BaseModel):
    animal_id: Optional[int] = None
    tag_number: Optional[str] = None
    weight: float
    date: date

class WeightOut(BaseModel):
    id: int
    animal_id: int
    weight: float
    date: date

@router.get("/")
def get_weights(
    animal_id: Optional[int] = None,
    tag_number: Optional[str] = None,
    group_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Weight)
    if tag_number is not None:
        animal = db.query(Animal).filter(Animal.tag_number == tag_number).first()
        if not animal:
            return []
        query = query.filter(Weight.animal_id == animal.id)
        return [
            {"date": w.date, "weight": w.weight}
            for w in query.order_by(Weight.date.desc()).all()
        ]
    elif animal_id is not None:
        query = query.filter(Weight.animal_id == animal_id)
        return [
            {"date": w.date, "weight": w.weight}
            for w in query.order_by(Weight.date.desc()).all()
        ]
    elif group_id is not None:
        animal_ids = [
            a.id
            for a in db.query(Animal).filter(Animal.group_id == group_id, Animal.deceased == False).all()
        ]
        if not animal_ids:
            return []
        results = (
            db.query(Weight.date, sa.func.avg(Weight.weight).label("avg_weight"))
            .filter(Weight.animal_id.in_(animal_ids))
            .group_by(Weight.date)
            .order_by(Weight.date.desc())
            .all()
        )
        return [
            {"date": r.date, "avg_weight": round(r.avg_weight, 1) if r.avg_weight else None}
            for r in results
        ]
    else:
        return [
            {"date": w.date, "weight": w.weight}
            for w in query.order_by(Weight.date.desc()).all()
        ]

@router.post("/")
def record_weight(payload: WeightIn, db: Session = Depends(get_db)):
    animal = db.get(Animal, payload.animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    weight = Weight(
        animal_id=payload.animal_id,
        weight=payload.weight,
        date=payload.date
    )
    db.add(weight)
    # Update animal's current_weight and weight_date
    animal.current_weight = payload.weight
    animal.weight_date = payload.date
    db.commit()
    db.refresh(weight)
    return {
        "id": weight.id,
        "animal_id": weight.animal_id,
        "weight": weight.weight,
        "date": weight.date
    }