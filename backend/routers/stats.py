# backend/routers/stats.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func
from backend.db import SessionLocal
from backend.models.animal import Animal
from backend.models.camp import Camp
from backend.models.vaccine import Vaccine
from backend.models.group import Group
from datetime import date, datetime

router = APIRouter(prefix="/stats", tags=["stats"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def age_months(d: date) -> int:
    if not d:
        return 0
    today = date.today()
    years = today.year - d.year
    months = today.month - d.month
    if today.day < d.day:
        months -= 1
    total = years * 12 + months
    return max(0, total)

@router.get("/herd-summary")
def herd_summary(db: Session = Depends(get_db)):
    """
    Counts exclude deceased animals.
    Parity rule for females:
      - Cow  = sex F and has_calved True
      - Heifer = sex F and has_calved False
    Calves: animals < 6 months (any sex); calves are excluded from bulls/cows/heifers buckets to avoid double counting.
    Bulls: sex M and not a calf.
    Unknown: everything else not in the above buckets (e.g., missing sex).
    """
    animals = db.execute(
        select(Animal).where(Animal.deceased == False)  # noqa: E712
    ).scalars().all()
    total = len(animals)

    calves = cows = heifers = bulls = unknown = 0

    for a in animals:
        is_calf = age_months(a.birth_date) < 6 if a.birth_date else False
        if is_calf:
            calves += 1
            continue

        s = (a.sex or "").upper()
        if s == "F":
            if a.has_calved:
                cows += 1
            else:
                heifers += 1
        elif s == "M":
            bulls += 1
        else:
            unknown += 1

    return {
        "total": total,
        "bulls": bulls,
        "cows": cows,
        "heifers": heifers,
        "calves": calves,
        "unknown": unknown,
    }

@router.get("/camps-summary")
def camps_summary(db: Session = Depends(get_db)):
    # Count non-deceased animals per camp
    counts = dict(
        db.execute(
            select(Animal.camp_id, func.count(Animal.id))
            .where(Animal.deceased == False)  # noqa: E712
            .group_by(Animal.camp_id)
        ).all()
    )
    rows = db.execute(select(Camp).order_by(Camp.name)).scalars().all()
    groups = db.execute(select(Group)).scalars().all()
    camp_to_group = {g.camp_id: g.name for g in groups if g.camp_id is not None}
    return [
        {"id": c.id, "name": c.name, "animal_count": int(counts.get(c.id, 0)), "group_name": camp_to_group.get(c.id, ""), "notes": c.notes}
        for c in rows
    ]

@router.get("/stocks-summary")
def stocks_summary(db: Session = Depends(get_db)):
    # Minimal summary based on vaccines; extend if you track more stock categories
    total_items = db.execute(select(func.count(Vaccine.id))).scalar() or 0
    totals_by_category = {"Vaccines": int(total_items)}
    low_stock = []  # add threshold logic if/when you add a min field
    return {
        "totals_by_category": totals_by_category,
        "low_stock": low_stock,
        "total_items": int(total_items),
    }
