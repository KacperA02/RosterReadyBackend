from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from app.db_config import Base
from app.association import team_user
# Creating the Users structure
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    email = Column(String(50), unique=True, index=True)

    created_teams = relationship("Team", back_populates="creator")
    teams = relationship("Team", secondary=team_user, back_populates="users")
    # added userConstraint relationship
    user_constraints = relationship("UserConstraint", back_populates="user")