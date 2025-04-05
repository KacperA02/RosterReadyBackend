from sqlalchemy import Column, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.dependencies.db_config import Base
class Assignment(Base):
    __tablename__ = 'assignments'
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    day_id = Column(Integer, ForeignKey("days.id"))
    team_id = Column(Integer,ForeignKey("teams.id"))
    shift_id = Column(Integer,ForeignKey("shifts.id")) 
    solution_id = Column(Integer, ForeignKey("solutions.id"))
    locked = Column(Boolean, default=False)
    
    solution = relationship("Solution", back_populates="assignments")
    user = relationship("User", back_populates="assignments")   
    day = relationship("Day", back_populates="assignments")    
    shift = relationship("Shift", back_populates="assignments")
    team = relationship("Team", back_populates="assignments")