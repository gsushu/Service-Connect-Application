from fastapi import APIRouter, WebSocket
import asyncio
router = APIRouter(prefix="/worker", tags=["Worker"])

active_connections = []

async def notify_workers(request_data: dict):
    if active_connections:
        print(f"Notifying {len(active_connections)} workers: {request_data}")
        tasks = [conn.send_json(request_data) for conn in active_connections]
        await asyncio.gather(*tasks, return_exceptions=True)

@router.websocket("/notifications")
async def worker_notifications(websocket: WebSocket):
    await websocket.accept()
    
    worker = websocket.session.get("worker")
    if not worker or "id" not in worker:
        await websocket.close(code=1008)  # 1008 = Policy Violation (Unauthorized)
        print("Unauthorized worker tried to connect")
        return
    
    active_connections.append(websocket)
    print(f"A worker {worker['username']} connected! Total: {len(active_connections)}")

    # welcome_message = {"message": f"Worker {worker['username']} has joined!"}
    # for conn in active_connections:
    #     await conn.send_json(welcome_message)
    await notify_workers({"message": f"Worker {worker['username']} has joined!"})

    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received from worker {worker['id']}: {data}")
    except Exception as e:
        print(f"Worker {worker['id']} disconnected: {e}")
        active_connections.remove(websocket)