from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.db_config import Base
from app.association import day_shift_team

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
