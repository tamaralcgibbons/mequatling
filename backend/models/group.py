from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from backend.db import Base

class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    camp_id = Column(Integer, ForeignKey("camps.id"), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Link to Camp. Use backref so Camp.groups is created automatically
    # without needing to change camp.py.
    camp = relationship("Camp", backref="groups", uselist=False)

    def touch(self):
        self.updated_at = datetime.utcnow()

class GroupMovementEvent(Base):
    __tablename__ = "group_movement_events"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    from_camp_id = Column(Integer, ForeignKey("camps.id"), nullable=True)
    to_camp_id = Column(Integer, ForeignKey("camps.id"), nullable=False)
    date = Column(DateTime, nullable=False, default=datetime.utcnow)
    reason = Column(Text, nullable=True)
