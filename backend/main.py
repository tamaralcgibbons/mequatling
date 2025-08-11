from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import SQLModel, Field, Session, create_engine, select
from typing import Optional
import os, shutil
from datetime import datetime

# --- Models ___
class Camp(SQLModel, table = True):
    id: Optional[int] = Field(default = None, primary_key = True)
    name: str

class Animal(SQLModel, table = True):
    id: Optional[int] = Field(default - None, primary_key = True)
    name: str
    tag_number: Optional[str] = None
    birth_date: Optional[date] = None
    sex: Optional[str] = None
    camp_id = Optional[int] = Field(default = None, foreign_key = "camp.id")
    photo_path = Optional[str] = None
    stats: Optional[str] = None

# --- DB & app setup ---
os.makedirs("uploads", exist_ok = True)
engine = create_engine("sqlite:///farm.db", echo = False)
SQLModel.metadata.create_all(engine)

app = FastAPI(title = "Mequatling")
app.add_middleware(CORSMiddleware, allow_origins = ["*"], allow_methods = ["*"], allow_headers = ["*"])

app.mount("/uploads", StaticFiles(directory = "uploads"), name = "uploads")

def get_session():
    with Session(engine) as session:
        yield session

# --- Endpoints ---
@app.post("/animals/")
def create_animal(animal: Animal, session: Session = Depends(get_session)):
    session.add(animal)
    session.commit()
    session.refresh(animal)
    return animal

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
