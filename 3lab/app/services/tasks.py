import itertools
import os
import sys
import subprocess
import tempfile
import threading

from fastapi import WebSocket, HTTPException
from sqlalchemy.orm import Session

from app.celery.celery_app import celapp
from app.core.config import JOHN_PATH
from app.cruds import tasks as tasks_crud
from app.db.db import SessionLocal
from app.models.models import Task


def extract_hash_from_rar(hash_bytes):
    executable_path = os.path.join(JOHN_PATH, "run", "rar2john")
    try:        
        f = tempfile.NamedTemporaryFile(delete=False)
        f.write(hash_bytes)
        f.close()
        command = f"{executable_path} {os.path.realpath(f.name)}"
        print(command)
        process_result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        #os.unlink(f.name)
        output = process_result.stdout
        print(output)
        if process_result.returncode != 0:
            raise OSError("Failed to launch rar2john. Is John The Ripper installed? In Windows set app/core/config.py JOHN_PATH to JTR root folder. " + output)
        parts = output.split(":")
        #if parts and len(parts) > 1:
        #    return parts[-1]
        #else:
        return output
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")


def generate_word(chars_list, min_len, max_len):
    for i in range(min_len, max_len+1):
        for j in itertools.product(chars_list, repeat=i):
            yield ''.join(j)


def execute_bruteforce_attack(task: Task):
    executable_path = os.path.join(JOHN_PATH, "run", "john")
    try:
        # write hash to file
        fh = tempfile.NamedTemporaryFile(mode="wt", delete=False)
        fh.write(task.hash)
        fh.close()
        
        # write wordlist to file
        fw = tempfile.NamedTemporaryFile(mode="wt", delete=False)
        for word in generate_word(task.charset, 1, task.max_length):   
            fw.write(word + "\n")
        fw.close()

        #execute brute force attack by John the Ripper
        command = f"{executable_path} --wordlist={os.path.realpath(fw.name)} {os.path.realpath(fh.name)}"
        print(command, flush=True)
        process_result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        output = process_result.stdout
        print(output, flush=True)

        #query password by John the Ripper
        command = f"{executable_path} --show {os.path.realpath(fh.name)}"
        print(command, flush=True)
        process_result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        output = process_result.stdout
        print(output, flush=True)

        #extract password from John the Ripper output
        parts = output.split("\n")
        subparts = parts[0].split(":")
        if len(subparts) > 1:
            output = subparts[1]

        #delete temporary files
        #os.unlink(fh.name)
        #os.unlink(fw.name)

        task.status = "completed"
    except Exception as error:
        output = f"Error executing program: {error}"
        task.status = "failed"

    db = SessionLocal()
    dbtask = tasks_crud.get_task(db, task.id)
    dbtask.status = task.status
    dbtask.progress = 100
    dbtask.result = output
    db.commit()
    return dbtask


@celapp.task()
def execute_bruteforce_attack_task(task_id: int):
    db = SessionLocal()
    dbtask = tasks_crud.get_task(db, task_id)
    task = execute_bruteforce_attack(dbtask)
    #if ws is not None:
    #    ws.send_text(f"Bruteforce task finished. Task id={task.id}\nResult: {task.result}")


def create_task(db: Session, hash: str, charset: str, max_length: int, user_id: int):
    task = tasks_crud.add_task(db, hash, charset, max_length, user_id)
    
    # run via celery
    execute_bruteforce_attack_task.apply_async(args=[task.id], task_id=str(task.id))

    # run in another thread
    #thread = threading.Thread(target=execute_bruteforce_attack, args=(task,))
    #thread.start()
    
    # run directly
    #execute_bruteforce_attack(task)

    return {
        "task_id": task.id
    }
    
