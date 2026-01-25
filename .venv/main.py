import os
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from google import genai

load_dotenv()

API_KEY = os.getenv('API_KEY')

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

f = open("./static/index.html", "r")
indexpage = f.read()
f.close()

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        client = genai.Client(api_key=API_KEY)
        response = client.models.generate_content(
            model="gemini-2.5-flash", contents=message
        )
        await websocket.send_text(response.text)

    # async def broadcast(self, message: str):
    #     for connection in self.active_connections:
    #         await connection.send_text(message)

manager = ConnectionManager()

def HTMLresponse():
    return HTMLResponse(content=indexpage, status_code=200)

@app.get("/", response_class=HTMLResponse)
async def root():
    return HTMLresponse()

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(data, websocket)
    except WebSocketDisconnect:
        manager.disconnect(websocket)