from fastapi import Depends, APIRouter, HTTPException, File
from sqlalchemy.orm import Session

from app.services.tasks import create_task, extract_hash_from_rar
from app.db.db import get_db
from app.api.users import get_logged_user
import app.cruds.tasks as tasks_crud

router = APIRouter()


@router.post("/extract_hash")
def extract_hash_from_rar_file(file: bytes = File(), _ = Depends(get_logged_user)):
    hash = extract_hash_from_rar(file)
    return {
        "hash": hash
    }

@router.post("/brut_hash")
def start_bruteforce_hash_task(hash: str, charset: str, max_length: int, db: Session = Depends(get_db), user = Depends(get_logged_user)):
    if max_length < 1 or max_length > 8:
        raise HTTPException(status_code=500, detail="max_length should be more than 0 and less than 9")
    try:
        return create_task(db, hash, charset, max_length, user["id"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")

@router.get("/get_status")
def bruteforce_hash_task_status(id: int, db: Session = Depends(get_db), _ = Depends(get_logged_user)):
    task = tasks_crud.get_task(db, id)
    if not task:
        return None
    return {
        "status": task.status,
        "progress": task.progress,
        "result": task.result
    }
