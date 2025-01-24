from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db_config import Base
# model to hold users constraints to be passed to the csp
class UserConstraint(Base):
    __tablename__ = "userConstraint"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    shift_id = Column(Integer, ForeignKey("shifts.id"), primary_key=True)
    team_id = Column(Integer, ForeignKey("teams.id"), primary_key=True)
    day_id = Column(Integer, ForeignKey("days.id"), primary_key=True)
    is_available = Column(Boolean, default=True)
    is_preferred = Column(Boolean, default=False)

    # Relationships to other tables
    user = relationship("User", back_populates="user_constraints")
    shift = relationship("Shift", back_populates="user_constraints")
    day = relationship("Day", back_populates="user_constraints")
    team = relationship("Team", back_populates="user_constraints")
