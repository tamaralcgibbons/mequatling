from typing import Optional, Tuple

from sqlalchemy.orm import Session

from backend.models.vaccine import Vaccine
from backend.models.stock_ledger import StockLedger


def adjust_stock(
    db: Session,
    *,
    vaccine_id: int,
    delta: float,
    reason: Optional[str] = None,
    ref_type: Optional[str] = None,
    ref_id: Optional[int] = None,
    allow_negative: bool = False,
) -> Vaccine:
    """
    Adjust a vaccine's stock by `delta` (positive to add, negative to consume).
    Writes a StockLedger row and returns the updated Vaccine.

    If allow_negative=False (default), clamps at 0 and records the actual delta used.
    """
    v: Vaccine = db.get(Vaccine, vaccine_id)
    if not v:
        raise ValueError("Vaccine not found")

    start = float(v.current_stock or 0.0)
    end = start + float(delta)

    actual_delta = float(delta)
    if not allow_negative and end < 0:
        # clamp to zero; adjust actual_delta so ledger reflects what really happened
        actual_delta = -start
        end = 0.0

    v.current_stock = end
    db.add(v)

    # ledger
    ledger = StockLedger(
        vaccine_id=v.id,
        delta=actual_delta,
        reason=reason,
        ref_type=ref_type,
        ref_id=ref_id,
        balance_after=end,
    )
    db.add(ledger)
    db.flush()  # so ledger gets an id if caller wants it

    return v


def decrement_for_group(
    db: Session,
    *,
    vaccine_id: int,
    dose_per_animal: float,
    group_size: int,
    reason: str = "group vaccination",
    ref_type: str = "vaccination_group",
    ref_id: Optional[int] = None,
    allow_negative: bool = False,
) -> Vaccine:
    """
    Convenience wrapper: subtract dose_per_animal * group_size from stock.
    """
    total = float(dose_per_animal or 0.0) * int(group_size or 0)
    if total <= 0:
        return db.get(Vaccine, vaccine_id)
    return adjust_stock(
        db,
        vaccine_id=vaccine_id,
        delta=-total,
        reason=reason,
        ref_type=ref_type,
        ref_id=ref_id,
        allow_negative=allow_negative,
    )


def decrement_for_animal(
    db: Session,
    *,
    vaccine_id: int,
    dose: float,
    reason: str = "manual vaccination",
    ref_type: str = "vaccination_animal",
    ref_id: Optional[int] = None,
    allow_negative: bool = False,
) -> Vaccine:
    """
    Convenience wrapper: subtract a single animal dose from stock.
    """
    d = float(dose or 0.0)
    if d <= 0:
        return db.get(Vaccine, vaccine_id)
    return adjust_stock(
        db,
        vaccine_id=vaccine_id,
        delta=-d,
        reason=reason,
        ref_type=ref_type,
        ref_id=ref_id,
        allow_negative=allow_negative,
    )
