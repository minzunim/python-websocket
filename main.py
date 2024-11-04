from typing import Dict, List
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="templates")

app = FastAPI(docs_url="/documentation", redoc_url=None)


class ConnectionManager:
    def __init__(self):
        # self.active_connections: list[WebSocket] = []
        self.rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, room_id: int, client_id: int, websocket: WebSocket):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        self.rooms[room_id].append(websocket)
        
        await self.broadcast(room_id, f"{client_id} 님이 입장했습니다.")

    def disconnect(self, room_id: int, websocket: WebSocket):
        self.rooms[room_id].remove(websocket)
        if not self.rooms[room_id]:
            del self.rooms[room_id]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, room_id: int, message: str):
        for connection in self.rooms.get(room_id, []):
            try:
                await connection.send_text(message)
            except Exception as e:
            # 에러 로그를 남기거나 연결을 제거하는 로직을 추가할 수 있습니다.
                print(f"Error sending message to connection: {e}")
                


manager = ConnectionManager()

# index.html 연결
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws/{room_id}/{client_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: int, client_id: int):
    await manager.connect(room_id, client_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.broadcast(room_id, f"{client_id}: {data}")
    except Exception as e: 
        print(f"Error sending message to connection here: {e}")
    finally:
        manager.disconnect(room_id, websocket)