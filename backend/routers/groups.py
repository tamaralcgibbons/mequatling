# backend/routers/groups.py
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.db import SessionLocal                     # ✅ correct import
from backend.models.group import Group
from backend.models.animal import Animal
from backend.models.camp import Camp
from backend.schemas.group import GroupMovementEventIn
from backend.models.group import GroupMovementEvent
from backend.models.history import AnimalHistory

router = APIRouter(prefix="/groups", tags=["groups"])

# ---------- DB dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Schemas ----------
class MoveCampIn(BaseModel):
    camp_id: int

class GroupIn(BaseModel):
    name: Optional[str] = None
    camp_id: Optional[int] = None
    animal_ids: Optional[List[int]] = None  # set membership if given
    notes: Optional[str] = None

class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)     # ✅ Pydantic v2

    id: int
    name: str
    camp_id: Optional[int] = None
    animal_count: int = 0
    notes: Optional[str] = None

# ---------- Helpers ----------
def _count_members(db: Session, group_id: int) -> int:
    return int(
        db.execute(
            select(func.count(Animal.id))
            .where(Animal.group_id == group_id, Animal.deceased == False)  # noqa: E712
        ).scalar() or 0
    )

def _group_out(db: Session, g: Group) -> GroupOut:
    return GroupOut(id=g.id, name=g.name, camp_id=g.camp_id, animal_count=_count_members(db, g.id), notes=g.notes)

# ---------- Routes ----------
@router.get("/")
def list_groups(db: Session = Depends(get_db)):
    counts = dict(
        db.execute(
            select(Animal.group_id, func.count(Animal.id))
            .where(Animal.deceased == False)
            .group_by(Animal.group_id)
        ).all()
    )
    rows = db.execute(select(Group).order_by(Group.name)).scalars().all()
    # Get all animals in one query
    all_animals = db.execute(select(Animal)).scalars().all()
    group_animals_map = {}
    for a in all_animals:
        if a.group_id not in group_animals_map:
            group_animals_map[a.group_id] = []
        group_animals_map[a.group_id].append({
            "id": a.id,
            "tag_number": a.tag_number,
            "sex": a.sex,
            "current_weight": a.current_weight,
            "pregnant": a.pregnant,
            "pregnancy_duration": a.pregnancy_duration,
            "pregnancy_date": a.pregnancy_date.isoformat() if a.pregnancy_date else None,
            "deceased": a.deceased,
        })
    result = []
    for g in rows:
        animals = [a for a in group_animals_map.get(g.id, []) if not a["deceased"]]
        weights = [a["current_weight"] for a in animals if a["current_weight"] is not None]
        avg_weight = round(sum(weights) / len(weights), 1) if weights else None
        result.append({
            "id": g.id,
            "name": g.name,
            "camp_id": g.camp_id,
            "animal_count": int(counts.get(g.id, 0)),
            "notes": g.notes or "",
            "created_at": g.created_at,
            "updated_at": g.updated_at,
            "animals": animals,
            "avg_weight": avg_weight,
        })
    return result

@router.post("/", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
def create_group(payload: GroupIn, db: Session = Depends(get_db)):
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Group name is required")

    if payload.camp_id is not None:
        if payload.camp_id and not db.get(Camp, payload.camp_id):
            raise HTTPException(status_code=404, detail="Camp not found")

    g = Group(name=name, camp_id=payload.camp_id, notes=payload.notes)
    db.add(g)
    db.commit()
    db.refresh(g)

    # assign members if provided (ignore empty list vs None distinction)
    if payload.animal_ids:
        db.query(Animal).filter(Animal.id.in_(payload.animal_ids)).update(
            {Animal.group_id: g.id}, synchronize_session=False
        )
        db.commit()

    return _group_out(db, g)

@router.post("/move")
def record_group_movement(event: GroupMovementEventIn, db: Session = Depends(get_db)):
    movement = GroupMovementEvent(**event.dict())
    db.add(movement)
    db.commit()
    db.refresh(movement)
    # Optionally update the group's camp_id
    group = db.get(Group, event.group_id)
    if group:
        group.camp_id = event.to_camp_id
        db.commit()
    return movement

@router.post("/{group_id}/move-camp")
def move_group_camp(group_id: int, payload: MoveCampIn, db: Session = Depends(get_db)):
    g = db.get(Group, group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    c = db.get(Camp, payload.camp_id)
    if not c:
        raise HTTPException(status_code=404, detail="Camp not found")

    # Record movement event
    from_camp_id = g.camp_id
    movement = GroupMovementEvent(
        group_id=group_id,
        from_camp_id=from_camp_id,
        to_camp_id=payload.camp_id,
        date=datetime.utcnow(),
        reason="Moved via move-camp endpoint"
    )
    db.add(movement)

    # update group and all member animals
    g.camp_id = payload.camp_id
    db.query(Animal).filter(Animal.group_id == g.id).update(
        {Animal.camp_id: payload.camp_id}, synchronize_session=False
    )
    db.commit()
    return {"ok": True}

@router.patch("/{group_id}", response_model=GroupOut)
def update_group(group_id: int, payload: GroupIn, db: Session = Depends(get_db)):
    g = db.get(Group, group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")

    if payload.name is not None:
        new_name = (payload.name or "").strip()
        if new_name:
            g.name = new_name

    if payload.camp_id is not None:
        if payload.camp_id and not db.get(Camp, payload.camp_id):
            raise HTTPException(status_code=404, detail="Camp not found")
        g.camp_id = payload.camp_id

    if payload.notes is not None:
        g.notes = payload.notes

    db.commit()
    db.refresh(g)

    # Membership sync if provided (None means "don't touch")
    if payload.animal_ids is not None:
        ids_set = set(payload.animal_ids or [])
        if ids_set:
            # Clear members no longer in the set
            db.query(Animal).filter(
                Animal.group_id == g.id,
                ~Animal.id.in_(ids_set)
            ).update({Animal.group_id: None}, synchronize_session=False)
            # Assign new members
            db.query(Animal).filter(Animal.id.in_(ids_set)).update(
                {Animal.group_id: g.id}, synchronize_session=False
            )
        else:
            # Empty list => remove all members
            db.query(Animal).filter(Animal.group_id == g.id).update(
                {Animal.group_id: None}, synchronize_session=False
            )
        db.commit()

    return _group_out(db, g)

@router.delete("/{group_id}")
def delete_group(group_id: int, db: Session = Depends(get_db)):
    g = db.get(Group, group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")

    # unassign members
    db.query(Animal).filter(Animal.group_id == g.id).update(
        {Animal.group_id: None}, synchronize_session=False
    )
    db.delete(g)
    db.commit()
    return {"ok": True}

@router.get("/{group_id}/weight-history")
def group_weight_history(group_id: int, db: Session = Depends(get_db)):
    # Get all weights for animals in the group
    animals = db.execute(select(Animal).where(Animal.group_id == group_id, Animal.deceased == False)).scalars().all()
    animal_ids = [a.id for a in animals]
    if not animal_ids:
        return []
    from backend.models.weight import Weight
    weights = db.execute(
        select(Weight.date, func.avg(Weight.weight))
        .where(Weight.animal_id.in_(animal_ids))
        .group_by(Weight.date)
        .order_by(Weight.date.desc())
    ).all()
    return [{"date": d.isoformat(), "avg_weight": round(avg, 1) if avg else None} for d, avg in weights]

@router.post("/{group_id}/slaughter")
def group_slaughter(group_id: int, payload: dict, db: Session = Depends(get_db)):
    g = db.get(Group, group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    reason = (payload.get("reason") or "").strip() or None
    date_str = payload.get("date")
    event_date = datetime.utcnow().date()
    if date_str:
        try:
            event_date = datetime.fromisoformat(date_str).date()
        except Exception:
            pass

    # Mark all animals as slaughtered and record history
    animals = db.query(Animal).filter(Animal.group_id == group_id, Animal.deceased == False).all()
    for a in animals:
        a.deceased = True
        a.killed = True
        a.death_reason = reason
        a.touch()
        db.commit()
        history = AnimalHistory(
            animal_id=a.id,
            event_type="slaughtered",
            event_date=event_date,
            reason=reason,
        )
        db.add(history)
        db.commit()
    return {"ok": True, "count": len(animals)}