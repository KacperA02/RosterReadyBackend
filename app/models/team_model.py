from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from db_config import Base
# Creating the teams structure
class Team(Base):
    __tablename__ = 'teams'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    employer_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    # adding a relationship between team and user
    employer = relationship("User", back_populates="teams")