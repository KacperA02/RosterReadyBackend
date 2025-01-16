from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from typing import Annotated
import models
from db_config import engine, SessionLocal
from sqlalchemy.orm import Session

app = FastAPI
