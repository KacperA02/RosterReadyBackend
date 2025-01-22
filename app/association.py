from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db_config import Base

# Association table for many-to-many relationship between Team and User
team_user = Table(
    "team_user",
    Base.metadata,
    Column("team_id", Integer, ForeignKey("teams.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
)

# Association table for many-to-many relationship between Day, Shift, and Team
day_shift_team = Table(
    "day_shift_team",
    Base.metadata,
    Column("day_id", Integer, ForeignKey("days.id"), primary_key=True),
    Column("shift_id", Integer, ForeignKey("shifts.id"), primary_key=True),
    Column("team_id", Integer, ForeignKey("teams.id"), primary_key=True),
)
