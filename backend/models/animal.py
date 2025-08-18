# backend/models/animal.py
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Date, Boolean, Text, DateTime, ForeignKey, JSON, Float
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from backend.db import Base  # use the ONE shared Base
from backend.models.weight import Weight
from backend.models.history import AnimalHistory

# JSON that works on SQLite (JSON) and Postgres (JSONB)
JSON_COMPAT = JSON().with_variant(JSONB, "postgresql")

history = relationship("AnimalHistory", back_populates="animal", cascade="all, delete-orphan")

class Animal(Base):
    __tablename__ = "animals"

    id = Column(Integer, primary_key=True, index=True)
    tag_number = Column(String(64), index=True)
    name = Column(String(255))
    sex = Column(String(1))  # 'F' | 'M' | None
    birth_date = Column(Date)
    pregnancy_status = Column(String(32))  # 'pregnant' | 'open' | None

    # add FKs so joins / referential integrity work (only if you have these tables)
    camp_id = Column(Integer, ForeignKey("camps.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    notes = Column(Text)
    photo_path = Column(String(512))

    # Deceased flags
    deceased = Column(Boolean, nullable=False, default=False)
    killed = Column(Boolean)
    death_reason = Column(Text)

    # Parity / calves
    has_calved = Column(Boolean, nullable=False, default=False)
    calves_count = Column(Integer, nullable=False, default=0)
    calves_tags = Column(JSON_COMPAT, nullable=False, default=list)  # list[str]

    # Optional direct mother link (self-referential)
    mother_id = Column(Float, ForeignKey("animals.id"))
    mother = relationship("Animal", remote_side=[id], uselist=False)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Weight tracking
    current_weight = Column(Integer, nullable=True)
    weight_date = Column(Date, nullable=True)

    # Pregnancy tracking
    pregnant = Column(Boolean, nullable=True, default=False)
    pregnancy_duration = Column(String(32), nullable=True)  # e.g. "2.5 months"
    pregnancy_date = Column(Date, nullable=True)

    # Weight history relationship
    weights = relationship("Weight", back_populates="animal")

    history = relationship("AnimalHistory", back_populates="animal", cascade="all, delete-orphan")

    def touch(self):
        self.updated_at = datetime.utcnow()
