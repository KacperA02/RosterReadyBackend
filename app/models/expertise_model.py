from sqlalchemy import Column, Integer, String,ForeignKey
from sqlalchemy.orm import relationship
from app.dependencies.db_config import Base
from app.association import user_expertise,shift_expertise

class Expertise(Base):
    __tablename__ = "expertises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    team_id = Column(Integer, ForeignKey("teams.id"))
    
    team = relationship("Team", back_populates="expertises")
    users = relationship("User",secondary=user_expertise, back_populates="expertises")
    shifts = relationship("Shift",secondary=shift_expertise, back_populates="expertises")
   
    
