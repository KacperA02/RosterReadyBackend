from datetime import timedelta
# Import the necessary functions and classes from FastAPI
from fastapi import APIRouter, Depends, HTTPException, status, Response
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
# Import the functions from auth.py
from app.dependencies.auth import create_access_token, verify_password, get_user_by_email, get_current_user
from app.dependencies.db_config import get_db
# import the Token and LoginRequest schemas
from app.schemas.auth_schema import Token, LoginRequest  
from app.schemas.user_schema import UserResponse

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_current_user_data(current_user: UserResponse = Depends(get_current_user)):
    return current_user 

# login route for generating JWT token
@router.post("/login", response_model=Token)
async def login_for_access_token(
    response: Response,
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
        data={
            "sub": user.email,
            "roles": [role.name for role in user.roles],
            "id": user.id,
            "team_id":user.team_id
            }
    )
    response = JSONResponse(content={"access_token": access_token, "token_type": "bearer"})
    response.status_code = status.HTTP_200_OK  
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=False,  
        secure=True,  
        samesite="None",  
    )
    return response
    
@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logged out successfully"}

   
