from sqlalchemy import Column, Integer, DateTime,Enum, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.dependencies.db_config import Base
from app.enums import SolutionStatus
class Solution(Base):
    __tablename__ = 'solutions'
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    week_id = Column(Integer, ForeignKey("weeks.id"))
    status = Column(Enum(SolutionStatus), default=SolutionStatus.DRAFT)
    created_at = Column(DateTime, default=datetime.timestamp)
    
    assignments = relationship("Assignment", back_populates="solution")
    team = relationship("Team", back_populates="solutions") 
    week = relationship("Week", back_populates="solutions") 

    