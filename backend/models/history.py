from sqlalchemy import Column, Integer, String, Date, ForeignKey
from sqlalchemy.orm import relationship
from backend.db import Base

class AnimalHistory(Base):
    __tablename__ = "animal_history"

    id = Column(Integer, primary_key=True, index=True)
    animal_id = Column(Integer, ForeignKey("animals.id"), nullable=False)
    event_type = Column(String(32), nullable=False)  # "slaughtered", "deceased", etc.
    event_date = Column(Date, nullable=False)
    reason = Column(String(256), nullable=True)

    animal = relationship("Animal", back_populates="history")