from datetime import timedelta
# Import the necessary functions and classes from FastAPI
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
# Import the functions from auth.py
from app.dependencies.auth import create_access_token, verify_password, get_user_by_email
from app.db_config import get_db
# import the Token and LoginRequest schemas
from app.schemas.auth_schema import Token, LoginRequest  

router = APIRouter()
# login route for generating JWT token
@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: LoginRequest,  
    db: Session = Depends(get_db),
):
    user = get_user_by_email(db, form_data.email)  
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # create the access token and include the user's roles
    access_token = create_access_token(
        data={"sub": user.email, "roles": [role.name for role in user.roles]},
    )
    # return the access token
    return {"access_token": access_token, "token_type": "bearer"}

