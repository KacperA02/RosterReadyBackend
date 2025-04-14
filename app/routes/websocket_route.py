# app/routes/websocket_routes.py
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from app.services.websocket_manager import manager
from app.dependencies.auth import decode_access_token  # Make sure this exists in your auth file
from app.models import User

# Create an APIRouter instance
router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    token = websocket.query_params.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")

    try:
        decoded_token = decode_access_token(token)
        if not decoded_token:
            raise HTTPException(status_code=401, detail="Invalid token")
        user_id = decoded_token["id"]
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Prevent duplicate connections for the same user
    if manager.is_connected(str(user_id)):
        print(f"[WS] User {user_id} is already connected. Rejecting new connection.")
        await websocket.close()
        return

    print(f"[WS] User {user_id} connected.")
    await manager.connect(str(user_id), websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(str(user_id), websocket)
