from sqlalchemy.orm import Session
from app.models.role_model import Role

DEFAULT_ROLES = ["Customer", "Admin", "Employer", "Employee"]

def seed_roles(db: Session):
    for role_name in DEFAULT_ROLES:
        if not db.query(Role).filter(Role.name == role_name).first():
            db.add(Role(name=role_name))
    db.commit()
