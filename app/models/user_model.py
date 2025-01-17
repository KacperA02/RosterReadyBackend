from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from app.db_config import Base
# Creating the Users structure
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    email = Column(String(50), unique=True, index=True)

    created_teams = relationship("Team", back_populates="creator")
    teams = relationship("Team", secondary="team_members", back_populates="members")