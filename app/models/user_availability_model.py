from sqlalchemy import Column, Integer, ForeignKey, Boolean, String
from sqlalchemy.orm import relationship
from app.dependencies.db_config import Base

class UserAvailability(Base):
    __tablename__ = "user_availability"
    
    id = Column(Integer, primary_key=True, index=True)  
    user_id = Column(Integer, ForeignKey("users.id"))
    team_id = Column(Integer, ForeignKey("teams.id"))
    day_id = Column(Integer, ForeignKey("days.id"))
    reason = Column(String(50))
    approved = Column(Boolean, default=False)

    user = relationship("User", back_populates="user_availability")
    day = relationship("Day", back_populates="user_availability")
    team = relationship("Team", back_populates="user_availability")
