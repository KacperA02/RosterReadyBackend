from sqlalchemy import Boolean, Column, Integer, String,ForeignKey
from sqlalchemy.orm import relationship
from app.dependencies.db_config import Base
from app.association import user_roles,user_expertise
# Creating the Users structure
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), index=True)
    last_name = Column(String(50), index=True)
    email = Column(String(50), unique=True, index=True)
    password = Column(String(60))
    mobile_number = Column(String(12), unique=True, index=True)
    day_off_count = Column(Integer, default=0)  # Set default value to 0
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)

    roles = relationship("Role", secondary=user_roles, back_populates="users")
    
    team = relationship("Team", back_populates="users", foreign_keys=[team_id])
    
    created_teams = relationship("Team", back_populates="creator", foreign_keys="[Team.creator_id]")
    
    invitations = relationship("TeamInvitation", back_populates="user")
    
    user_availability = relationship("UserAvailability", back_populates="user")
    
    expertises = relationship("Expertise", secondary=user_expertise, back_populates="users")
    
    assignments = relationship("Assignment", back_populates="user", cascade="all, delete-orphan")
