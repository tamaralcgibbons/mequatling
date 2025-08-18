from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.models.vaccine import Vaccine

router = APIRouter(tags=["vaccines"])

@router.get("/")
def list_vaccines(db: Session = Depends(get_db)):
    return db.query(Vaccine).all()