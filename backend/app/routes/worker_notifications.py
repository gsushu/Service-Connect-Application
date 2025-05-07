from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, List
import asyncio

router = APIRouter(prefix="/worker", tags=["Worker Notifications"]) # Changed tag

# Store active worker connections: {worker_id: [WebSocket]}
active_worker_connections: Dict[int, List[WebSocket]] = {}

async def notify_all_workers(message: dict):
    """Sends a JSON message to ALL connected workers."""
    if active_worker_connections:
        print(f"Notifying ALL {sum(len(conns) for conns in active_worker_connections.values())} workers: {message}")
        all_connections = [conn for conns in active_worker_connections.values() for conn in conns]
        tasks = [conn.send_json(message) for conn in all_connections]
        await asyncio.gather(*tasks, return_exceptions=True) # Handle exceptions if needed

async def notify_specific_worker(worker_id: int, message: dict):
    """Sends a JSON message to all active connections for a specific worker."""
    if worker_id in active_worker_connections:
        connections = active_worker_connections[worker_id]
        print(f"Notifying worker {worker_id} ({len(connections)} connections): {message}")
        results = await asyncio.gather(
            *[conn.send_json(message) for conn in connections],
            return_exceptions=True
        )
        # Optional: Handle exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error sending to worker {worker_id} connection {i}: {result}")

@router.websocket("/notifications")
async def worker_notifications_ws(websocket: WebSocket):
    await websocket.accept()

    # --- Authentication/Identification using Session ---
    # This relies on the session being correctly populated *before* the WS upgrade.
    # Consider sending a token in the first message as a more robust alternative.
    worker_session = websocket.session.get("worker")
    if not worker_session or "id" not in worker_session:
        await websocket.close(code=1008)  # 1008 = Policy Violation (Unauthorized)
        print("Unauthorized worker tried to connect via WebSocket")
        return

    worker_id = worker_session["id"]
    worker_username = worker_session.get("username", "Unknown") # Get username if available
    # --- End Authentication ---

    print(f"Worker {worker_id} ({worker_username}) connected via WebSocket.")

    # Add connection to the pool
    if worker_id not in active_worker_connections:
        active_worker_connections[worker_id] = []
    active_worker_connections[worker_id].append(websocket)

    # Optional: Send a welcome message or confirmation
    # await websocket.send_json({"type": "status", "message": "Connected successfully"})

    try:
        while True:
            # Keep connection alive, listen for messages if needed
            data = await websocket.receive_text()
            print(f"Received from worker {worker_id}: {data}")
            # Process incoming data if necessary
    except WebSocketDisconnect:
        print(f"Worker {worker_id} disconnected.")
    except Exception as e:
        print(f"Error with worker {worker_id} WebSocket: {e}")
    finally:
        # Remove connection on disconnect or error
        if worker_id in active_worker_connections:
            active_worker_connections[worker_id].remove(websocket)
            if not active_worker_connections[worker_id]: # Remove worker ID if list is empty
                del active_worker_connections[worker_id]
        print(f"Worker {worker_id} connection closed. Remaining for worker: {len(active_worker_connections.get(worker_id, []))}")