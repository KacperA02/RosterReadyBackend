from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from app.dependencies.db_config import Base
from app.association import user_roles

class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(60), unique=True, index=True)
    
    users = relationship("User", secondary=user_roles, back_populates="roles")