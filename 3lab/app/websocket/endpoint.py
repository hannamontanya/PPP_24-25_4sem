import asyncio
import threading
from fastapi import WebSocket, HTTPException
import json

from app.db.db import SessionLocal
from app.services.security import get_token_contents
from app.cruds import users as users_crud
from app.services.tasks import create_task 
from app.celery.celery_app import celapp
from app.cruds import tasks as tasks_crud


current_user = None

async def websocket_start_brutforce_task(websocket: WebSocket, data: str, user_id: int):
    args = list(filter(None, data.split()))
    if len(args) != 4:
        raise ValueError("Wrong number of arguments! Command format is 'start hash-string-or-file password-charset max-password-length")
    if not args[3].isdigit():
        raise ValueError("maxlen (argument 3) should be a number")    
    db = SessionLocal()
    ret = create_task(db, args[1], args[2], int(args[3]), user_id)
    await websocket.send_text(f"Bruteforce task start requested. Task id={ret['task_id']}")
    
async def websocket_stop_brutforce_task(websocket: WebSocket, data: str, user_id: int):
    args = list(filter(None, data.split()))
    if len(args) != 2:
        raise ValueError("Wrong number of arguments! Command format is 'stop task-id")
    if not args[1].isdigit():
        raise ValueError("task-id (argument 1) should be a number")    
    task_id = int(args[1])
    db = SessionLocal()
    dbtask = tasks_crud.get_task(db, task_id)
    if dbtask is None:
        raise ValueError(f"Task with id={task_id} not found in database")    
    if dbtask.user_id != user_id:
        raise ValueError(f"Task with id={task_id} belongs to another user")
    if dbtask.status != "running":
        raise ValueError(f"Task with id={task_id} is not running")
    await websocket.send_text(f"Bruteforce task stop requested. Task id={task_id}")
    celapp.control.revoke(str(task_id), terminate=True)
    dbtask.status = "cancelled"
    dbtask.progress = 100
    dbtask.result = "none"
    db.commit()
 
async def websocket_info_brutforce_task(websocket: WebSocket, data: str, user_id: int):
    args = list(filter(None, data.split()))
    if len(args) != 2:
        raise ValueError("Wrong number of arguments! Command format is 'info task-id")
    if not args[1].isdigit():
        raise ValueError("task-id (argument 1) should be a number")    
    task_id = int(args[1])
    db = SessionLocal()
    dbtask = tasks_crud.get_task(db, task_id)
    if dbtask is None:
        raise ValueError(f"Task with id={task_id} not found in database")    
    if dbtask.user_id != user_id:
        raise ValueError(f"Task with id={task_id} belongs to another user")
    await websocket.send_text(f"Bruteforce task info requested. Task id={task_id}")
    await websocket.send_text(json.dumps({
        "status": dbtask.status,
        "progress": dbtask.progress,
        "result": dbtask.result        
    }))
 
def celery_callback_processing(websocket: WebSocket):
    state = celapp.events.State()

    def on_task_started(event):
        state.event(event)        
        if not event['uuid'].isdigit():
            asyncio.run(websocket.send_text(str(event)))
        task_id = int(event['uuid'])
        db = SessionLocal()
        dbtask = tasks_crud.get_task(db, task_id)
        if dbtask is None:
            asyncio.run(websocket.send_text(str(event)))
        asyncio.run(websocket.send_json({  
            "status": "STARTED",
            "task_id": task_id,
            "hash_type": "rar",
            "charset_length": len(dbtask.charset),
            "max_length": dbtask.max_length,
        }))

    def on_task_succeeded(event):
        state.event(event)
        if not event['uuid'].isdigit():
            asyncio.run(websocket.send_text(str(event)))
        task_id = int(event['uuid'])
        db = SessionLocal()
        dbtask = tasks_crud.get_task(db, task_id)
        if dbtask is None:
            asyncio.run(websocket.send_text(str(event)))
        asyncio.run(websocket.send_json({  
            "status": "COMPLETED",
            "task_id": task_id,
            "result": dbtask.result,
            "elapsed_time": event['runtime'],
        }))

    def on_task_revoked(event):
        state.event(event)
        asyncio.run(websocket.send_json({  
            "status": "CANCELLED",
            "task_id": event['uuid'],
        }))

    def callback(event):
        state.event(event)
        asyncio.run(websocket.send_text(str(event)))

    with celapp.connection() as connection:
        receiver = celapp.events.Receiver(connection, handlers={
            'task-started': on_task_started,
            'task-succeeded': on_task_succeeded,
            'task-revoked': on_task_revoked,
            'task-failed': callback,
        })
        receiver.capture(limit=None, timeout=None, wakeup=True)


async def websocket_endpoint(websocket: WebSocket):
    # user authorization
    if "authorization" not in websocket.headers:
        raise HTTPException(status_code=401, detail="Ошибка аутентификации")
    token = websocket.headers["authorization"].replace("Bearer ", "")
    payload = get_token_contents(token)
    if not payload or 'email' not in payload:
        raise HTTPException(status_code=401, detail="Ошибка аутентификации")    
    db = SessionLocal()
    current_user = users_crud.get_user(db, payload['email'])
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )
    #print(websocket.headers)
    #payload = { 'email': 'b@b.b' }
    await websocket.accept()

    # celery callback processing
    ct = threading.Thread(target=celery_callback_processing, args=(websocket,))
    ct.daemon = True
    ct.start()

    # main loop
    while True:
        data = await websocket.receive_text()
        cmd = data.strip().lower()
        if cmd.find("start") == 0:
            try:
                await websocket_start_brutforce_task(websocket, data, current_user.id)
            except ValueError as e:
                await websocket.send_text(str(e))
        elif cmd.find("stop") == 0:
            try:
                await websocket_stop_brutforce_task(websocket, data, current_user.id)
            except ValueError as e:
                await websocket.send_text(str(e))
        elif cmd.find("info") == 0:
            try:
                await websocket_info_brutforce_task(websocket, data, current_user.id)
            except ValueError as e:
                await websocket.send_text(str(e))
        else:
            await websocket.send_text(f"{payload['email']} said: {data}")
    