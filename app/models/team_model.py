from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db_config import Base

# Association table for many-to-many relationship between Team and User
team_members = Table(
    "team_members",
    Base.metadata,
    Column("team_id", Integer, ForeignKey("teams.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)

class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), index=True)
    creator_id = Column(Integer, ForeignKey("users.id"))

    # Relationships
    creator = relationship("User", back_populates="created_teams")
    members = relationship("User", secondary=team_members, back_populates="teams")
