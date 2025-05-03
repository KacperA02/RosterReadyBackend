from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import pymysql
pymysql.install_as_MySQLdb()
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Get the database URL from environment variables
DATABASE_URL = os.getenv("MYSQL_URL")

# Check if DATABASE_URL is loaded correctly
if not DATABASE_URL:
    raise ValueError("Database not found")

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Single Base class for all models
Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
