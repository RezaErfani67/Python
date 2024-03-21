from fastapi import FastAPI
from bson import ObjectId , json_util
import json 
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware 
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import asyncio
from typing import List
import os
app = FastAPI()

import json
import base64
import uuid
from fastapi.staticfiles import StaticFiles

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your needs
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)



UPLOAD_DIR = "uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads") 
rooms = {} 
@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await websocket.accept()
    if room_id not in rooms:
        rooms[room_id] = []
    rooms[room_id].append(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            data = json.loads(data)
            if data['type'] == 'message':
                for client in rooms[room_id]:
                    await client.send_text(json.dumps(data))
            elif data['type'] == 'image':
                # Save image to the server
                image_data = data['image'].split(",")[1]  # remove "data:image/jpeg;base64,"
                image_bytes = base64.b64decode(image_data)
                image_path = os.path.join(UPLOAD_DIR, f"image_{uuid.uuid4()}.jpeg")
                with open(image_path, "wb") as f:
                    f.write(image_bytes)
                # Send image URL to clients
                image_url = f"http://localhost:8000/{image_path}"
                data['image'] = image_url
                for client in rooms[room_id]:
                    await client.send_text(json.dumps(data))
    finally:
        rooms[room_id].remove(websocket)
