from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.db_config import Base
from app.association import day_shift_team
from app.models.user_model import User  
from app.models.expertise_model import Expertise

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    creator_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    creator = relationship("User", back_populates="created_teams", foreign_keys=[creator_id]) 
    users = relationship("User", back_populates="team", foreign_keys=[User.team_id])
    shifts = relationship("Shift", back_populates="team")
    invitations = relationship("TeamInvitation", back_populates="team")
    days = relationship(
        "Day",
        secondary=day_shift_team,
        back_populates="teams",
        overlaps="days" 
    )
    # added userConstraint relationship
    user_constraints = relationship("UserConstraint", back_populates="team")
    expertises = relationship("Expertise", back_populates="team", foreign_keys=[Expertise.team_id])