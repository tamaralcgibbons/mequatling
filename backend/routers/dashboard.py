# backend/routers/dashboard.py
from typing import Dict
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import select, func

from backend.db import SessionLocal
from backend.models.animal import Animal
from backend.models.camp import Camp
from backend.models.vaccine import Vaccine

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# ---------- DB dependency ----------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ---------- helpers ----------
def age_months(d: date | None) -> int:
    if not d:
        return 0
    today = date.today()
    years = today.year - d.year
    months = today.month - d.month
    if today.day < d.day:
        months -= 1
    total = years * 12 + months
    return max(0, total)

# ---------- routes ----------
@router.get("/herd-summary")
def herd_summary(db: Session = Depends(get_db)) -> Dict:
    """
    Counts exclude deceased animals.
    Parity rule for females:
      - Cow: F and has_calved True
      - Heifer: F and has_calved False
    Calves: < 6 months (any sex), excluded from bulls/cows/heifers.
    Bulls: M and not a calf.
    Unknown: anything else not classified (e.g., missing sex).
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
def camps_summary(db: Session = Depends(get_db)) -> Dict:
    # Build camp list + counts (excluding deceased) in Python for portability
    camps = db.execute(select(Camp).order_by(Camp.name)).scalars().all()
    animals = db.execute(
        select(Animal).where(Animal.deceased == False)  # noqa: E712
    ).scalars().all()

    count_by_camp: dict[int | None, int] = {}
    for a in animals:
        count_by_camp[a.camp_id] = count_by_camp.get(a.camp_id, 0) + 1

    return {
        "camps": [
            {"id": c.id, "name": c.name, "animal_count": int(count_by_camp.get(c.id, 0))}
            for c in camps
        ]
    }

@router.get("/stocks-summary")
def stocks_summary(db: Session = Depends(get_db)) -> Dict:
    # Minimal stock summary from Vaccine rows; extend if you track more categories
    total_items = db.execute(select(func.count(Vaccine.id))).scalar() or 0
    return {
        "totals_by_category": {"vaccines": int(total_items)},  # keep lowercase key per your example
        "low_stock": [],                                       # add threshold logic if/when you track it
        "total_items": int(total_items),
    }
