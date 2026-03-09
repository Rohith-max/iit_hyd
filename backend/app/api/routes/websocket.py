"""WebSocket endpoint for live agent streaming."""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.agents.ws_manager import ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/cases/{case_id}")
async def websocket_endpoint(websocket: WebSocket, case_id: str):
    await ws_manager.connect(case_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Client can send pings or commands
            if data == "ping":
                await websocket.send_text('{"type":"pong"}')
    except WebSocketDisconnect:
        ws_manager.disconnect(case_id, websocket)
