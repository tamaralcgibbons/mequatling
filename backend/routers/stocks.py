from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
import json

from backend.db import SessionLocal
from backend.models.vaccine import Vaccine, VaccineWasteEvent
from backend.models.feed import Feed, FeedEvent
from backend.models.fertiliser import Fertiliser, FertiliserEvent
from backend.models.fuel import Fuel, FuelEvent
from backend.schemas.vaccine import VaccineCreate, VaccineEventIn
from backend.schemas.feed import FeedCreate, FeedUpdate
from backend.schemas.fertiliser import FertiliserCreate, FertiliserUpdate
from backend.schemas.fuel import FuelCreate, FuelUpdate

router = APIRouter(prefix="/stocks", tags=["stocks"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Vaccines ---
@router.get("/vaccines")
def list_vaccines(db: Session = Depends(get_db)):
    vaccines = db.query(Vaccine).order_by(Vaccine.name).all()
    for v in vaccines:
        v.methods = json.loads(v.methods) if v.methods else []
    return vaccines

@router.post("/vaccines")
def create_vaccine(vaccine: VaccineCreate, db: Session = Depends(get_db)):
    data = vaccine.dict()
    data["methods"] = json.dumps(data["methods"])  # Serialize list to JSON string
    obj = Vaccine(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    # Deserialize methods for output
    obj.methods = json.loads(obj.methods) if obj.methods else []
    return obj

@router.post("/vaccines/{vaccine_id}/event")
def record_vaccine_event(vaccine_id: int, event: VaccineEventIn, db: Session = Depends(get_db)):
    vaccine = db.get(Vaccine, vaccine_id)
    if not vaccine:
        raise HTTPException(status_code=404, detail="Vaccine not found")
    obj = VaccineEvent(**event.dict())
    if event.event_type == "in":
        vaccine.current_stock += event.amount
    elif event.event_type == "out":
        vaccine.current_stock -= event.amount
    db.add(obj)
    db.commit()
    db.refresh(vaccine)
    return {"ok": True, "current_stock": vaccine.current_stock}

@router.post("/vaccines/{vaccine_id}/waste")
def record_vaccine_waste(vaccine_id: int, amount: float, date: str, reason: str = "", db: Session = Depends(get_db)):
    vaccine = db.get(Vaccine, vaccine_id)
    if not vaccine:
        raise HTTPException(status_code=404, detail="Vaccine not found")
    waste_event = VaccineWasteEvent(
        vaccine_id=vaccine_id,
        amount=amount,
        date=datetime.strptime(date, "%Y-%m-%d"),
        reason=reason
    )
    vaccine.current_stock -= amount
    db.add(waste_event)
    db.commit()
    db.refresh(vaccine)
    return {"ok": True, "current_stock": vaccine.current_stock}

# --- Feed ---
@router.get("/feeds")
def list_feeds(db: Session = Depends(get_db)):
    return db.query(Feed).order_by(Feed.name).all()

@router.post("/feeds", response_model=None)
def create_feed(feed: FeedCreate, db: Session = Depends(get_db)):
    obj = Feed(**feed.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.patch("/feeds/{feed_id}", response_model=None)
def update_feed(feed_id: int, feed: FeedUpdate, db: Session = Depends(get_db)):
    obj = db.get(Feed, feed_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Feed not found")
    for k, v in feed.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@router.post("/feeds/{feed_id}/event")
def record_feed_event(feed_id: int, event_type: str, amount: float, date: str, reason: str = "", db: Session = Depends(get_db)):
    feed = db.get(Feed, feed_id)
    if not feed:
        raise HTTPException(status_code=404, detail="Feed not found")
    event = FeedEvent(
        feed_id=feed_id,
        event_type=event_type,
        amount=amount,
        date=datetime.strptime(date, "%Y-%m-%d"),
        reason=reason
    )
    if event_type == "in":
        feed.current_stock += amount
    elif event_type == "out":
        feed.current_stock -= amount
    db.add(event)
    db.commit()
    db.refresh(feed)
    return {"ok": True, "current_stock": feed.current_stock}

@router.post("/feeds/mix")
def mix_feeds(components: dict, output_feed_id: int, output_amount: float, date: str, reason: str = "", db: Session = Depends(get_db)):
    # components: {feed_id: amount}
    for fid, amt in components.items():
        feed = db.get(Feed, fid)
        if not feed:
            raise HTTPException(status_code=404, detail=f"Feed {fid} not found")
        feed.current_stock -= amt
        event = FeedEvent(
            feed_id=fid,
            event_type="mix",
            amount=amt,
            date=datetime.strptime(date, "%Y-%m-%d"),
            reason=f"Used in mix for feed {output_feed_id}"
        )
        db.add(event)
    output_feed = db.get(Feed, output_feed_id)
    if not output_feed:
        raise HTTPException(status_code=404, detail="Output feed not found")
    output_feed.current_stock += output_amount
    mix_event = FeedEvent(
        feed_id=output_feed_id,
        event_type="in",
        amount=output_amount,
        date=datetime.strptime(date, "%Y-%m-%d"),
        reason=reason or "Feed mix"
    )
    db.add(mix_event)
    db.commit()
    db.refresh(output_feed)
    return {"ok": True, "output_stock": output_feed.current_stock}

# --- Fertiliser ---
@router.get("/fertilisers")
def list_fertilisers(db: Session = Depends(get_db)):
    return db.query(Fertiliser).order_by(Fertiliser.name).all()

@router.post("/fertilisers", response_model=None)
def create_fertiliser(fert: FertiliserCreate, db: Session = Depends(get_db)):
    obj = Fertiliser(**fert.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.patch("/fertilisers/{fertiliser_id}", response_model=None)
def update_fertiliser(fertiliser_id: int, fert: FertiliserUpdate, db: Session = Depends(get_db)):
    obj = db.get(Fertiliser, fertiliser_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Fertiliser not found")
    for k, v in fert.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@router.post("/fertilisers/{fertiliser_id}/event")
def record_fertiliser_event(fertiliser_id: int, event_type: str, amount: float, date: str, reason: str = "", db: Session = Depends(get_db)):
    fert = db.get(Fertiliser, fertiliser_id)
    if not fert:
        raise HTTPException(status_code=404, detail="Fertiliser not found")
    event = FertiliserEvent(
        fertiliser_id=fertiliser_id,
        event_type=event_type,
        amount=amount,
        date=datetime.strptime(date, "%Y-%m-%d"),
        reason=reason
    )
    if event_type == "in":
        fert.current_stock += amount
    elif event_type == "out":
        fert.current_stock -= amount
    db.add(event)
    db.commit()
    db.refresh(fert)
    return {"ok": True, "current_stock": fert.current_stock}

# --- Fuel ---
@router.get("/fuels")
def list_fuels(db: Session = Depends(get_db)):
    return db.query(Fuel).order_by(Fuel.type).all()

@router.post("/fuels", response_model=None)
def create_fuel(fuel: FuelCreate, db: Session = Depends(get_db)):
    obj = Fuel(**fuel.dict())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.patch("/fuels/{fuel_id}", response_model=None)
def update_fuel(fuel_id: int, fuel: FuelUpdate, db: Session = Depends(get_db)):
    obj = db.get(Fuel, fuel_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Fuel not found")
    for k, v in fuel.dict(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@router.post("/fuels/{fuel_id}/event")
def record_fuel_event(fuel_id: int, event_type: str, amount: float, date: str, reason: str = "", db: Session = Depends(get_db)):
    fuel = db.get(Fuel, fuel_id)
    if not fuel:
        raise HTTPException(status_code=404, detail="Fuel not found")
    event = FuelEvent(
        fuel_id=fuel_id,
        event_type=event_type,
        amount=amount,
        date=datetime.strptime(date, "%Y-%m-%d"),
        reason=reason
    )
    if event_type == "in":
        fuel.current_stock += amount
    elif event_type == "out":
        fuel.current_stock -= amount
    db.add(event)
    db.commit()
    db.refresh(fuel)
    return {"ok": True, "current_stock": fuel.current_stock}