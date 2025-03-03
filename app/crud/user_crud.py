from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user_model import User
from app.models.role_model import Role
from app.schemas.user_schema import UserCreate
# Importing the function from auth.py to hash the password and get user by email
from app.dependencies.auth import hash_password, get_user_by_email 

def create_user(db: Session, user: UserCreate):
    # Check if email is already registered
    if get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if mobile number is already registered
    db_number = db.query(User).filter(User.mobile_number == user.mobile_number).first()
    if db_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mobile number already registered"
        )

    # using the function from auth.py to hash the password
    encrypted_password = hash_password(user.password)
    
    # Adding the customer role to a newly created user
    customer_role = db.query(Role).filter(Role.name == "Customer").first()
    if not customer_role:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Customer role not found! Ensure roles are seeded."
        )
    # Create a new user with the hashed password and customer role
    new_user = User(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        mobile_number=user.mobile_number,
        password=encrypted_password,
        roles=[customer_role]
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()
