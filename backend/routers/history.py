from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db import SessionLocal
from backend.models.vaccine import VaccineEvent, VaccineWasteEvent, Vaccine, VaccineStocktakeEvent
from backend.models.feed import FeedEvent, Feed, FeedStocktakeEvent
from backend.models.fertiliser import FertiliserEvent, Fertiliser, FertiliserStocktakeEvent
from backend.models.fuel import FuelEvent, Fuel, FuelStocktakeEvent
from backend.models.group import GroupMovementEvent, Group
from backend.models.camp import Camp
from backend.models.history import AnimalHistory
from datetime import date, datetime
# import AnimalEvent if you have one

router = APIRouter(prefix="/history", tags=["history"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/")
def get_all_events(db: Session = Depends(get_db)):
    events = []
    # Group movement events (Animal filter)
    for e in db.query(GroupMovementEvent).all():
        group = db.get(Group, e.group_id)
        from_camp = db.get(Camp, e.from_camp_id) if e.from_camp_id else None
        to_camp = db.get(Camp, e.to_camp_id)
        events.append({
            "id": e.id,
            "type": "animal",
            "event_type": "group_movement",
            "date": e.date,
            "reason": e.reason or "",
            "item_id": e.group_id,
            "name": group.name if group else "",
            "from_camp": from_camp.name if from_camp else "",
            "to_camp": to_camp.name if to_camp else "",
        })
    # Vaccine events
    for e in db.query(VaccineEvent).all():
        vaccine = db.get(Vaccine, e.vaccine_id)
        events.append({
            "id": e.id,
            "type": "vaccine",
            "event_type": e.event_type,
            "amount": e.amount,
            "unit": vaccine.unit if vaccine else "",
            "date": e.date,
            "reason": e.reason,
            "item_id": e.vaccine_id,
            "name": vaccine.name,
        })
    # Vaccine waste events
    for e in db.query(VaccineWasteEvent).all():
        vaccine = db.get(Vaccine, e.vaccine_id)
        events.append({
            "id": e.id,
            "type": "vaccine_waste",
            "event_type": "waste",
            "amount": e.amount,
            "unit": vaccine.unit if vaccine else "",
            "date": e.date,
            "reason": e.reason,
            "item_id": e.vaccine_id,
            "name": vaccine.name if vaccine else "",
        })
    # Vaccine stocktake events
    for e in db.query(VaccineStocktakeEvent).all():
        vaccine = db.get(Vaccine, e.vaccine_id)
        events.append({
            "id": e.id,
            "type": "vaccine_stocktake",
            "event_type": "stocktake",
            "amount": e.recorded_stock,
            "current_stock": vaccine.current_stock,
            "unit": vaccine.unit if vaccine else "",
            "date": e.date,
            "reason": e.notes,
            "item_id": e.vaccine_id,
            "name": vaccine.name if vaccine else "",
        })
    # Feed events
    for e in db.query(FeedEvent).all():
        feed = db.get(Feed, e.feed_id)
        reason = e.reason
        if reason and reason.startswith("Used in mix for feed "):
            try:
                target_id = int(reason.split("Used in mix for feed ")[1])
                target_feed = db.get(Feed, target_id)
                if target_feed:
                    reason = f"Used in mix for {target_feed.name}"
            except Exception:
                pass
        events.append({
            "id": e.id,
            "type": "feed",
            "event_type": e.event_type,
            "amount": e.amount,
            "unit": feed.unit if feed else "",
            "date": e.date,
            "reason": reason,
            "item_id": e.feed_id,
            "name": feed.name,
        })
    # Feed stocktake events
    for e in db.query(FeedStocktakeEvent).all():
        feed = db.get(Feed, e.feed_id)
        events.append({
            "id": e.id,
            "type": "feed_stocktake",
            "event_type": "stocktake",
            "amount": e.recorded_stock,
            "current_stock": feed.current_stock,
            "unit": feed.unit if feed else "",
            "date": e.date,
            "reason": e.notes,
            "item_id": e.feed_id,
            "name": feed.name if feed else "",
        })
    # Fertiliser events
    for e in db.query(FertiliserEvent).all():
        fertiliser = db.get(Fertiliser, e.fertiliser_id)
        events.append({
            "id": e.id,
            "type": "fertiliser",
            "event_type": e.event_type,
            "amount": e.amount,
            "unit": fertiliser.unit if fertiliser else "",
            "date": e.date,
            "reason": e.reason,
            "item_id": e.fertiliser_id,
            "name": fertiliser.name,
        })
    # Fertiliser stocktake events
    for e in db.query(FertiliserStocktakeEvent).all():
        fertiliser = db.get(Fertiliser, e.fertiliser_id)
        events.append({
            "id": e.id,
            "type": "fertiliser_stocktake",
            "event_type": "stocktake",
            "amount": e.recorded_stock,
            "current_stock": fertiliser.current_stock,
            "unit": fertiliser.unit if fertiliser else "",
            "date": e.date,
            "reason": e.notes,
            "item_id": e.fertiliser_id,
            "name": fertiliser.name if fertiliser else "",
        })
    # Fuel events
    for e in db.query(FuelEvent).all():
        fuel = db.get(Fuel, e.fuel_id)
        events.append({
            "id": e.id,
            "type": "fuel",
            "event_type": e.event_type,
            "amount": e.amount,
            "unit": fuel.unit if fuel else "",
            "date": e.date,
            "reason": e.reason,
            "item_id": e.fuel_id,
            "name": fuel.type if fuel else "",
        })
    # Fuel stocktake events
    for e in db.query(FuelStocktakeEvent).all():
        fuel = db.get(Fuel, e.fuel_id)
        events.append({
            "id": e.id,
            "type": "fuel_stocktake",
            "event_type": "stocktake",
            "amount": e.recorded_stock,
            "current_stock": fuel.current_stock,
            "unit": fuel.unit if fuel else "",
            "date": e.date,
            "reason": e.notes,
            "item_id": e.fuel_id,
            "name": fuel.type if fuel else "",
        })
    # Animal history events (slaughter/deceased)
    for e in db.query(AnimalHistory).all():
        events.append({
            "id": e.id,
            "type": "animal",
            "event_type": e.event_type,  # "slaughtered" or "deceased"
            "date": e.event_date,
            "reason": e.reason,
            "item_id": e.animal_id,
            "name": getattr(e.animal, "tag_number", None) if hasattr(e, "animal") else None,
        })
    # Before sorting, ensure all dates are strings:
    for e in events:
        if isinstance(e["date"], (datetime, date)):
            e["date"] = e["date"].isoformat()
    events.sort(key=lambda x: x["date"], reverse=True)
    return events

@router.get("")
def get_all_events_no_slash(db: Session = Depends(get_db)):
    return get_all_events(db)