# backend/models/camp.py
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from backend.db import Base

class Camp(Base):
    __tablename__ = "camps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)  # optional; remove if you don't store it

    # One-to-many: a camp can have many animals.
    # Using backref creates Animal.camp automatically (no need to edit animal.py).
    animals = relationship("Animal", backref="camp")
