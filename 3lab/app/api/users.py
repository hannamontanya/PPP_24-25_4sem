from fastapi import Depends, APIRouter, HTTPException, Form, status
from fastapi.responses import Response
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.services.security import login_user, get_token_contents, AuthorizationException
from app.db.db import get_db
from app.cruds import users as users_crud
from app.core.config import OAUTH_ENDPOINT


router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=OAUTH_ENDPOINT)


@router.post("/sign_up")
def create_user(email: str, password: str, db: Session = Depends(get_db)):
    try:
        users_crud.add_user(db, email, password)        
        return login_user(db, email, password)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"{e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")

@router.post(OAUTH_ENDPOINT)
def login_via_oauth(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    logged_user_data = login_user(db, username, password)
    return {
        "access_token": logged_user_data['token'], 
        "token_type": "bearer"
    }

@router.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):
    return login_user(db, email, password)

@router.get("/users/me")
def get_logged_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        if not token:
            return None
        contents = get_token_contents(token)
        email = contents.get('email')
    except AuthorizationException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Failed to validate bearer token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    user = users_crud.get_user(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return {
        "id": user.id,
        "email": user.email
    }
