from datetime import date, datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Date, Text
from sqlalchemy.orm import relationship
from backend.db import Base

class Vaccination(Base):
    __tablename__ = "vaccinations"

    id = Column(Integer, primary_key=True, index=True)

    animal_id = Column(Integer, ForeignKey("animals.id", ondelete="CASCADE"), nullable=False, index=True)
    vaccine_id = Column(Integer, ForeignKey("vaccines.id", ondelete="CASCADE"), nullable=False, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="SET NULL"), nullable=True, index=True)  # Optional: for group vaccinations

    date = Column(Date, nullable=False)
    dose = Column(Float, nullable=False)        # amount administered to this animal
    method = Column(String(64), nullable=True)  # e.g., "IM", "SC", "oral"
    source = Column(String(16), nullable=True)  # "group" | "manual"
    notes = Column(Text, nullable=True)         # notes about this vaccination

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # relationships
    animal = relationship("Animal")  # add back_populates on Animal if you want reverse access
    vaccine = relationship("Vaccine", back_populates="vaccinations")
    group = relationship("Group")    # Optional: for group vaccinations