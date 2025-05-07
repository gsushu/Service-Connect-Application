from fastapi import APIRouter, WebSocket, Depends, WebSocketDisconnect, Query, HTTPException, status
from sqlalchemy.orm import Session
from dependencies import get_db
from auth import SECRET_KEY, ALGORITHM # Import auth constants
from jose import jwt, JWTError
from typing import Dict, List
import asyncio

router = APIRouter(prefix="/user", tags=["User Notifications"])

# Store active user connections: {user_id: [WebSocket]}
active_user_connections: Dict[int, List[WebSocket]] = {}

async def get_user_id_from_token(token: str = Query(...)):
    """Dependency to validate token from query param and get user ID."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("id")
        if user_id is None:
            raise credentials_exception
        return user_id
    except JWTError:
        raise credentials_exception

async def notify_user(user_id: int, message: dict):
    """Sends a JSON message to all active connections for a specific user."""
    if user_id in active_user_connections:
        connections = active_user_connections[user_id]
        print(f"Notifying user {user_id} ({len(connections)} connections): {message}")
        # Use gather to send messages concurrently
        results = await asyncio.gather(
            *[conn.send_json(message) for conn in connections],
            return_exceptions=True
        )
        # Optional: Handle exceptions during send (e.g., connection closed)
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error sending to user {user_id} connection {i}: {result}")
                # Consider removing the failed connection here if needed

@router.websocket("/notifications")
async def user_notifications_ws(
    websocket: WebSocket,
    token: str = Query(...) # Get token from query parameter
    # db: Session = Depends(get_db) # Uncomment if DB access is needed here
):
    try:
        user_id = await get_user_id_from_token(token) # Validate token and get user_id
    except HTTPException as e:
        await websocket.accept() # Accept before closing with error code
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        print(f"WebSocket connection failed: {e.detail}")
        return

    await websocket.accept()
    print(f"User {user_id} connected via WebSocket.")

    # Add connection to the pool
    if user_id not in active_user_connections:
        active_user_connections[user_id] = []
    active_user_connections[user_id].append(websocket)

    try:
        # Keep the connection alive, maybe listen for pings or specific messages
        while True:
            # You could implement a ping/pong mechanism or listen for client messages
            data = await websocket.receive_text()
            print(f"Received from user {user_id}: {data}") # Example: echo back or process
            # await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        print(f"User {user_id} disconnected.")
    except Exception as e:
        print(f"Error with user {user_id} WebSocket: {e}")
    finally:
        # Remove connection on disconnect or error
        if user_id in active_user_connections:
            active_user_connections[user_id].remove(websocket)
            if not active_user_connections[user_id]: # Remove user ID if list is empty
                del active_user_connections[user_id]
        print(f"User {user_id} connection closed. Remaining for user: {len(active_user_connections.get(user_id, []))}")
