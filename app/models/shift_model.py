from sqlalchemy import Column, Integer, String, Time, ForeignKey
from sqlalchemy.orm import relationship
from app.db_config import Base

class Shift(Base):
    __tablename__ = "shifts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True) 
    time_start = Column(Time) 
    time_end = Column(Time)
    team_id = Column(Integer, ForeignKey("teams.id"))

    # realtionship with team
    team = relationship("Team", back_populates="shifts")