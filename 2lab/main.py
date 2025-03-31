from fastapi import FastAPI
import uvicorn

from app.api import users, tasks
from app.core.config import SERVER_HOST, SERVER_PORT
from app.db import db


db.init()

app = FastAPI(title="RAR password finder", version="0.0.1")
app.include_router(users.router)
app.include_router(tasks.router)

def serve():
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)

if __name__ == "__main__":
    serve()
