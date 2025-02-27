from sqlalchemy import Column, Integer, Date
from app.db_config import Base

class Week(Base):
    __tablename__ = "weeks"

    id = Column(Integer, primary_key=True, index=True)
    week_number = Column(Integer, unique=True, nullable=False)  
    start_date = Column(Date, nullable=False) 
    end_date = Column(Date, nullable=False) 
