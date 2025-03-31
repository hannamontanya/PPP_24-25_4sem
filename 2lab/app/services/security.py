import hashlib

from fastapi import HTTPException
import jwt
from sqlalchemy.orm import Session

from app.core.config import SECRET_KEY, ALGORITHM, OAUTH_ENDPOINT
from app.models.models import User


class AuthorizationException(Exception):
    pass


def hash_password(password_str):
    return hashlib.pbkdf2_hmac(
        "sha256", password_str.encode(), b"RARsalt", 100_000
    ).hex()

def verify_password(plain_password, hashed_password):
    return hash_password(plain_password) == hashed_password

def create_token(email: str):
    payload = {
        "email": email
    }
    encoded_jwt = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_token_contents(token: str):
    try:
        contents = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = contents.get("email")
        if email is None:
            raise AuthorizationException("Could not validate token")
        return {
            "email": email
        }
    except jwt.exceptions.PyJWTError:
        raise AuthorizationException("Could not validate token")

def find_user_check_password(db: Session, email: str, password: str):
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return False
    if not verify_password(password, user.password_hash):
        return False
    return user

def login_user(db: Session, email: str, password: str):
    user = find_user_check_password(db, email, password)
    if not user:
        raise HTTPException(
            status_code=401, detail="Wrong email or password")
    try:
        token = create_token(user.email)
        return {
            "id" : user.id,
            "email": user.email,
            "token": token
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")
