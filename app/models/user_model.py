from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship
from db_config import Base
# Creating the Users structure
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    # adding a relationship between team and user
    teams = relationship("Team", back_populates="employer")