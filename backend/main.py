from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
import os, shutil
from datetime import date, datetime
from pydantic import validator

def _parse_date(v: Optional[date | datetime | str]) -> Optional[date]:
    if v in (None, "", "null"):
        return None
    if isinstance(v, date) and not isinstance(v, datetime):
        return v
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, str):
        s = v.strip()
        try:
            if s.endswith("Z"):
                s = s[:-1] + "+00:00"
            return datetime.fromisoformat(s).date()
        except Exception:
            try:
                return datetime.strptime(s, "%Y-%m-%d").date()
            except Exception:
                return None
    return None

# --- Models ___
class Camp(SQLModel, table = True):
    id: Optional[int] = Field(default = None, primary_key = True)
    name: str

class Animal(SQLModel, table = True):
    id: Optional[int] = Field(default = None, primary_key = True)
    name: Optional[str] = None
    tag_number: Optional[str] = None
    birth_date: Optional[date] = None
    sex: Optional[str] = None
    pregnancy_status: Optional[str] = None
    camp_id: Optional[int] = Field(default = None, foreign_key = "camp.id")
    photo_path: Optional[str] = None
    notes: Optional[str] = None

    @validator("birth_date", pre=True)
    def _coerce_birth_date(cls, v):
        if v in (None, "", "null"):
            return None
        if isinstance(v, date) and not isinstance(v, datetime):
            return v
        if isinstance(v, datetime):
            return v.date()
        if isinstance(v, str):
            s = v.strip()
            # ISO-8601 or YYYY-MM-DD
            try:
                # handle trailing Z
                if s.endswith("Z"):
                    s = s[:-1] + "+00:00"
                dt = datetime.fromisoformat(s)
                return dt.date()
            except Exception:
                pass
            try:
                return datetime.strptime(s, "%Y-%m-%d").date()
            except Exception:
                raise ValueError("birth_date must be YYYY-MM-DD")
        raise ValueError("Invalid birth_date")

class AnimalUpdate(SQLModel):
    name: Optional[str] = None
    tag_number: Optional[str] = None
    birth_date: Optional[str] = None  # accept string; we'll coerce
    sex: Optional[str] = None
    pregnancy_status: Optional[str] = None
    camp_id: Optional[int] = None
    notes: Optional[str] = None

class StockItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str  # e.g., "vaccines", "feed", "consumables"
    quantity: float = 0
    unit: str = "units"  # e.g., "doses", "kg", "bags"
    min_threshold: float = 0

# --- DB & app setup ---
os.makedirs("uploads", exist_ok = True)
engine = create_engine("sqlite:///farm.db", echo = False)
SQLModel.metadata.create_all(engine)

app = FastAPI(title = "Mequatling")

from fastapi.responses import JSONResponse
from starlette.requests import Request
import traceback, logging

@app.exception_handler(Exception)
async def _dev_exception_handler(request: Request, exc: Exception):
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    logging.error("Unhandled error at %s: %s\n%s", request.url.path, exc, tb)
    return JSONResponse(status_code=500, content={"detail": f"{type(exc).__name__}: {exc}"})

app.add_middleware(
    CORSMiddleware, 
    allow_origins = ["http://localhost:5173", "http://127.0.0.1:5173", "*"], 
    allow_methods = ["*"], 
    allow_headers = ["*"]
)

app.mount("/uploads", StaticFiles(directory = "uploads"), name = "uploads")

def get_session():
    with Session(engine) as session:
        yield session

@app.get("/__debug")
def __debug(session: Session = Depends(get_session)):
    import sqlite3, os
    db_path = os.path.abspath("farm.db")
    cols = []
    try:
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        rows = cur.execute("PRAGMA table_info(animal)").fetchall()
        con.close()
        # rows: (cid, name, type, notnull, dflt_value, pk)
        cols = [{"cid": r[0], "name": r[1], "type": r[2], "notnull": r[3], "default": r[4], "pk": r[5]} for r in rows]
    except Exception as e:
        cols = [{"error": str(e)}]
    return {
        "main_file": __file__,
        "cwd": os.getcwd(),
        "db_path": db_path,
        "model_cols": [c.name for c in Animal.__table__.columns],
        "db_cols": cols
    }

# --- Endpoints ---
@app.post("/animals/")
def create_animal(data: Animal, session: Session = Depends(get_session)):
    # coerce date
    bd = _parse_date(data.birth_date) if data.birth_date else None

    # normalise strings
    sex = (data.sex or None)
    if sex: sex = sex.strip().upper()

    ps = (data.pregnancy_status or None)
    if ps:
        ps = ps.strip().lower()
        if ps not in ("pregnant", "open"):
            raise HTTPException(400, "pregnancy_status must be 'pregnant' or 'open'")

    animal = Animal(
        name=data.name,
        tag_number=data.tag_number,
        birth_date=bd,
        sex=sex,
        camp_id=data.camp_id,
        notes=data.notes,
        pregnancy_status=ps,
    )
    try:
        session.add(animal)
        session.commit()
        session.refresh(animal)
        return animal
    except SQLAlchemyError as e:
        session.rollback()
        raise HTTPException(400, detail=str(getattr(e, "orig", e)))

@app.get("/animals/")
def list_animals(session: Session = Depends(get_session)):
    animals = session.exec(select(Animal)).all()
    return animals

@app.post("/animals/{animal_id}/upload-photo")
async def upload_photo(animal_id:int, file: UploadFile = File(...), session: Session = Depends(get_session)):
    animal = session.get(Animal, animal_id)
    if not animal:
        raise HTTPException(status_code = 404, detail = "Animal not found")
    filename = f"{animal_id}_{file.filename}"
    filepath = os.path.join("uploads", filename)
    with open(filepath, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    animal.photo_path = f"/uploads/{filename}"
    session.add(animal)
    session.commit()
    session.refresh(animal)
    return {"photo_url": animal.photo_path}

@app.patch("/animals/{animal_id}")
def update_animal(animal_id: int, data: AnimalUpdate, session: Session = Depends(get_session)):
    animal = session.get(Animal, animal_id)
    if not animal:
        raise HTTPException(404, "Animal not found")

    payload = data.dict(exclude_unset=True)
    # trim + ''->None
    for k, v in list(payload.items()):
        if isinstance(v, str):
            v = v.strip()
            payload[k] = v if v else None

    # date
    if "birth_date" in payload:
        payload["birth_date"] = _parse_date(payload["birth_date"]) if payload["birth_date"] else None

    # sex
    if "sex" in payload and payload["sex"]:
        payload["sex"] = payload["sex"].upper()

    # pregnancy_status
    if "pregnancy_status" in payload and payload["pregnancy_status"]:
        s = payload["pregnancy_status"].lower()
        if s not in ("pregnant", "open"):
            raise HTTPException(400, "pregnancy_status must be 'pregnant' or 'open'")
        payload["pregnancy_status"] = s

    for k, v in payload.items():
        setattr(animal, k, v)

    session.add(animal)
    session.commit()
    session.refresh(animal)
    return animal

@app.post("/camps/")
def create_camp(camp: Camp, session: Session = Depends(get_session)):
    session.add(camp)
    session.commit()
    session.refresh(camp)
    return camp

@app.get("/camps/")
def list_camps(session: Session = Depends(get_session)):
    return session.exec(select(Camp)).all()

@app.post("/stocks/")
def create_stock(item: StockItem, session: Session = Depends(get_session)):
    session.add(item)
    session.commit()
    session.refresh(item)
    return item

@app.get("/stocks/")
def list_stocks(session: Session = Depends(get_session)):
    return session.exec(select(StockItem)).all()

@app.get("/stats/herd-summary")
def herd_summary(session: Session = Depends(get_session)):
    animals = session.exec(select(Animal)).all()
    counts = {"total": 0, "bulls": 0, "cows": 0, "heifers": 0, "calves": 0, "unknown": 0}
    today = date.today()

    for a in animals:
        counts["total"] += 1
        sex = (a.sex or "").strip().upper()
        bd = _parse_date(a.birth_date)
        months = ((today - bd).days // 30) if bd else None

        if months is not None and months < 6:
            counts["calves"] += 1
            continue

        if sex == "F":
            if months is not None and months < 36:
                counts["heifers"] += 1
            else:
                counts["cows"] += 1
        elif sex == "M":
            if months is not None and months >= 6:
                counts["bulls"] += 1
            else:
                counts["unknown"] += 1
        else:
            counts["unknown"] += 1

    return counts

@app.get("/stats/camps-summary")
def camps_summary(session: Session = Depends(get_session)):
    camps = session.exec(select(Camp)).all()
    animals = session.exec(select(Animal)).all()

    counts_by_camp: dict[Optional[int], int] = {c.id: 0 for c in camps}
    unassigned = 0
    for a in animals:
        if a.camp_id is None:
            unassigned += 1
        else:
            counts_by_camp[a.camp_id] = counts_by_camp.get(a.camp_id, 0) + 1

    data = [{"id": c.id, "name": c.name, "animal_count": counts_by_camp.get(c.id, 0)} for c in camps]
    data.append({"id": None, "name": "Unassigned", "animal_count": unassigned})
    return data

@app.get("/stats/stocks-summary")
def stocks_summary(session: Session = Depends(get_session)):
    try:
        items = session.exec(select(StockItem)).all()  # ok if you added StockItem; otherwise caught
    except Exception:
        return {"totals_by_category": {}, "low_stock": [], "total_items": 0}

    totals: dict[str, float] = {}
    low_list: list[dict] = []
    for it in items:
        cat = (it.category or "uncategorized").strip().lower()
        qty = float(it.quantity or 0)
        totals[cat] = totals.get(cat, 0.0) + qty
        if qty <= float(it.min_threshold or 0):
            low_list.append({
                "id": it.id, "name": it.name, "category": it.category,
                "quantity": it.quantity, "unit": it.unit, "min_threshold": it.min_threshold
            })
    return {"totals_by_category": totals, "low_stock": low_list, "total_items": len(items)}

@app.delete("/animals/{animal_id}")
def delete_animal(animal_id: int, session: Session = Depends(get_session)):
    animal = session.get(Animal, animal_id)
    if not animal:
        raise HTTPException(status_code=404, detail="Animal not found")
    session.delete(animal)
    session.commit()
    return {"ok": True}

from fastapi.staticfiles import StaticFiles

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/", StaticFiles(directory="frontend/dist", html=True), name="frontend")