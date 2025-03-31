from sqlalchemy.orm import Session

from app.models.models import Task


def add_task(db: Session, hash: str, charset: str, max_length: int, user_id: int):
    task = Task(
        hash=hash,
        charset=charset,
        max_length=max_length,
        status="running",
        progress=0,
        user_id=user_id,
    )
    db.add(task)
    db.commit()
    return task


def get_task(db: Session, id: int):
    task = db.query(Task).filter(Task.id == id).first()
    return task
