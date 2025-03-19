from sqlalchemy import Column, Integer, String, Time, ForeignKey
from sqlalchemy.orm import relationship
from app.db_config import Base
from app.association import day_shift_team, shift_expertise
from app.models.user_availability_model import UserAvailability

class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    time_start = Column(Time)
    time_end = Column(Time)
    task = Column(String(150), nullable=True)
    no_of_users = Column(Integer, default=1) 
    team_id = Column(Integer, ForeignKey("teams.id"))

    # Relationships
    team = relationship("Team", back_populates="shifts")
    days = relationship(
        "Day", 
        back_populates="shifts",
        secondary=day_shift_team,
        overlaps="days",
    )
    # added userConstraint relationship
    expertises = relationship("Expertise", secondary=shift_expertise, back_populates="shifts")

    assignments = relationship("Assignment", back_populates="shift", cascade="all, delete-orphan")