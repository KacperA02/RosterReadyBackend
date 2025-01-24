from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db_config import Base
from app.association import team_user, day_shift_team

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    creator_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    creator = relationship("User", back_populates="created_teams")
    users = relationship("User", secondary=team_user, back_populates="teams")
    shifts = relationship("Shift", back_populates="team")
    days = relationship(
        "Day",
        secondary=day_shift_team,
        back_populates="teams",
        overlaps="days" 
    )
