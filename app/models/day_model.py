from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.dependencies.db_config import Base
from app.association import day_shift_team
from app.models.user_availability_model import UserAvailability

class Day(Base):
    __tablename__ = "days"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)

    # added relationships for many to many table
    shifts = relationship(
        "Shift",
        secondary=day_shift_team,
        back_populates="days",
        overlaps="days",
    )
    teams = relationship(
        "Team",
        secondary=day_shift_team,
        back_populates="days",
        overlaps="days,shifts",
    )
    
    user_availability = relationship("UserAvailability", back_populates="day", foreign_keys=[UserAvailability.day_id])
    
    assignments = relationship("Assignment", back_populates="day", cascade="all, delete-orphan")