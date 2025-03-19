from sqlalchemy import Column, Integer, ForeignKey, String, DateTime,Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db_config import Base
from app.enums import InvitationStatus

class TeamInvitation(Base):
    __tablename__ = 'team_invitations'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id')) 
    team_id = Column(Integer, ForeignKey('teams.id')) 
    status = Column(Enum(InvitationStatus), default=InvitationStatus.PENDING) 
    created_at = Column(DateTime, default=func.now())  
    user = relationship('User', back_populates='invitations')  
    team = relationship('Team', back_populates='invitations') 
