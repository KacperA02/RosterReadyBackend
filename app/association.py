from sqlalchemy import Table, Column, Integer, ForeignKey
from app.db_config import Base


# Association table for many-to-many relationship between Day, Shift, and Team
day_shift_team = Table(
    "day_shift_team",
    Base.metadata,
    Column("day_id", Integer, ForeignKey("days.id"), primary_key=True),
    Column("shift_id", Integer, ForeignKey("shifts.id"), primary_key=True),
    Column("team_id", Integer, ForeignKey("teams.id"), primary_key=True),
)

user_roles = Table(
    "user_roles",
    Base.metadata,
    Column("user_id", ForeignKey("users.id"), primary_key=True),
    Column("role_id", ForeignKey("roles.id"), primary_key=True)
)
