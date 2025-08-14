# backend/routers/groups.py
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.db import SessionLocal                     # ✅ correct import
from backend.models.group import Group
from backend.models.animal import Animal
from backend.models.camp import Camp

router = APIRouter(prefix="/groups", tags=["groups"])

# ---------- DB dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- Schemas ----------
class GroupIn(BaseModel):
    name: Optional[str] = None
    camp_id: Optional[int] = None
    animal_ids: Optional[List[int]] = None  # set membership if given

class GroupOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)     # ✅ Pydantic v2

    id: int
    name: str
    camp_id: Optional[int] = None
    animal_count: int = 0

# ---------- Helpers ----------
def _count_members(db: Session, group_id: int) -> int:
    return int(
        db.execute(
            select(func.count(Animal.id))
            .where(Animal.group_id == group_id, Animal.deceased == False)  # noqa: E712
        ).scalar() or 0
    )

def _group_out(db: Session, g: Group) -> GroupOut:
    return GroupOut(id=g.id, name=g.name, camp_id=g.camp_id, animal_count=_count_members(db, g.id))

# ---------- Routes ----------
@router.get("/")
def list_groups(db: Session = Depends(get_db)):
    counts = dict(
        db.execute(
            select(Animal.group_id, func.count(Animal.id))
            .where(Animal.deceased == False)  # noqa: E712
            .group_by(Animal.group_id)
        ).all()
    )
    rows = db.execute(select(Group).order_by(Group.name)).scalars().all()
    return [{
        "id": g.id,
        "name": g.name,
        "camp_id": g.camp_id,
        "animal_count": int(counts.get(g.id, 0)),
        "created_at": g.created_at,
        "updated_at": g.updated_at,
    } for g in rows]

@router.post("/", response_model=GroupOut, status_code=status.HTTP_201_CREATED)
def create_group(payload: GroupIn, db: Session = Depends(get_db)):
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=400, detail="Group name is required")

    if payload.camp_id is not None:
        if payload.camp_id and not db.get(Camp, payload.camp_id):
            raise HTTPException(status_code=404, detail="Camp not found")

    g = Group(name=name, camp_id=payload.camp_id)
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

class MoveCampIn(BaseModel):
    camp_id: int

@router.post("/{group_id}/move-camp")
def move_group_camp(group_id: int, payload: MoveCampIn, db: Session = Depends(get_db)):
    g = db.get(Group, group_id)
    if not g:
        raise HTTPException(status_code=404, detail="Group not found")
    c = db.get(Camp, payload.camp_id)
    if not c:
        raise HTTPException(status_code=404, detail="Camp not found")

    # update group and all member animals
    g.camp_id = payload.camp_id
    db.query(Animal).filter(Animal.group_id == g.id).update(
        {Animal.camp_id: payload.camp_id}, synchronize_session=False
    )
    db.commit()
    return {"ok": True}

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
