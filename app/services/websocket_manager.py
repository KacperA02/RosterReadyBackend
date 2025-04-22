from typing import Dict, List
from fastapi import WebSocket
from starlette.websockets import WebSocketState

class WebSocketManager:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        if user_id not in self.connections:
            self.connections[user_id] = []
        self.connections[user_id].append(websocket)

    def disconnect(self, user_id: str, websocket: WebSocket):
        if user_id in self.connections:
            self.connections[user_id].remove(websocket)
            if not self.connections[user_id]:
                del self.connections[user_id]

    async def send_to_user(self, user_id: str, message: str):
        connections = self.connections.get(user_id, [])
        if not connections:
            print(f"[WS] No connections found for user {user_id}. Cannot send message.")
            return

        for connection in connections:
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_text(message)
                    print(f"[WS] Message sent to user {user_id}.")
                else:
                    print(f"[WS] WebSocket for user {user_id} is not connected.")
            except Exception as e:
                print(f"[WS] Error sending message to {user_id}: {e}")
                if connection.client_state != WebSocketState.CONNECTED:
                    self.disconnect(user_id, connection)

    # Add this method to check if the user is connected
    def is_connected(self, user_id: str) -> bool:
        return user_id in self.connections and bool(self.connections[user_id])

# Create a global instance of WebSocketManager
manager = WebSocketManager()
