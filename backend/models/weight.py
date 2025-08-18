from sqlalchemy import Column, Integer, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from backend.db import Base

class Weight(Base):
    __tablename__ = "weights"

    id = Column(Integer, primary_key=True)
    animal_id = Column(Integer, ForeignKey("animals.id"), nullable=False)
    weight = Column(Float, nullable=False)
    date = Column(Date, nullable=False)

    animal = relationship("Animal", back_populates="weights")