from sqlalchemy import Column, Integer, String, Text, Boolean, Date, Float, Text
from sqlalchemy.orm import relationship
from backend.db import Base

class Camp(Base):
    __tablename__ = "camps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)  # optional

    # New fields for management
    greenfeed = Column(Boolean, default=False)
    greenfeed_planting_date = Column(Date, nullable=True)
    greenfeed_amount = Column(Float, nullable=True)
    fertilised_date = Column(Date, nullable=True)
    fertilised_amount = Column(Float, nullable=True)
    grazed_status = Column(String(20), default="N")  # "Y", "N", "in_progress"
    grazed_out_date = Column(Date, nullable=True)
    notes = Column(Text, nullable=True)

    # One-to-many: a camp can have many animals.
    animals = relationship("Animal", backref="camp")