from sqlalchemy.orm import Session

from app.models.models import User
from app.services.security import hash_password


def add_user(db: Session, email: str, password: str):
    password_hash = hash_password(password)
    existing_user = get_user(db, email)
    if existing_user is not None:
        raise ValueError("User with such email already exists")
    user = User(
        email=email,
        password_hash=password_hash
    )
    db.add(user)
    db.commit()
    return user


def get_user(db: Session, email: str):
    user = db.query(User).filter(User.email == email).first()
    return user
