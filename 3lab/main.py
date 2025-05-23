from fastapi import FastAPI
import uvicorn

from app.api import users, tasks
from app.core.config import SERVER_HOST, SERVER_PORT
from app.db import db
#from app.websocket.endpoint import ws
from app.websocket.endpoint import websocket_endpoint
from app.api.users import oauth2_scheme

db.init()

app = FastAPI(title="RAR password finder", version="0.0.1")
app.include_router(users.router)
app.include_router(tasks.router)

app.add_api_websocket_route("/ws", websocket_endpoint) #, dependencies=[Depends(oauth2_scheme)])
#app.mount("/ws", ws)

def serve():
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT, log_level="debug", ws="websockets")

if __name__ == "__main__":
    serve()
