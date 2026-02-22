"""
PiTV - Display server for Raspberry Pi
Serves the frontend and handles image push + WebSocket broadcast.
"""

import base64
import json
import logging
from pathlib import Path
from typing import Optional

import aiofiles
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("pitv")

app = FastAPI(title="PiTV", version="1.0.0")

# ── State ──────────────────────────────────────────────────────────────────────
current_app: str = "clock"
last_image_path: Optional[str] = None
connected_clients: list[WebSocket] = []

# ── WebSocket helpers ──────────────────────────────────────────────────────────

async def broadcast(message: dict):
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_json(message)
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_clients.remove(ws)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    logger.info(f"Client connected. Total: {len(connected_clients)}")
    # Send current state on connect
    await websocket.send_json({"type": "switch_app", "app": current_app})
    try:
        while True:
            await websocket.receive_text()  # Keep alive
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        logger.info(f"Client disconnected. Total: {len(connected_clients)}")


# ── API routes ─────────────────────────────────────────────────────────────────

@app.post("/push/image")
async def push_image(
    file: Optional[UploadFile] = File(default=None),
    path: Optional[str] = Form(default=None),
):
    """Push an image to the display. Accepts file upload or local path."""
    global current_app, last_image_path

    if file:
        data = await file.read()
        img_b64 = base64.b64encode(data).decode()
        mime = file.content_type or "image/jpeg"
        last_image_path = file.filename
    elif path:
        p = Path(path)
        if not p.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {path}")
        async with aiofiles.open(p, "rb") as f:
            data = await f.read()
        img_b64 = base64.b64encode(data).decode()
        suffix = p.suffix.lower()
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}.get(suffix.lstrip("."), "image/jpeg")
        last_image_path = str(path)
    else:
        raise HTTPException(status_code=400, detail="Provide file upload or path field")

    current_app = "photo"
    await broadcast({
        "type": "show_image",
        "data": f"data:{mime};base64,{img_b64}",
    })
    logger.info(f"Image pushed ({len(data)//1024}KB), {len(connected_clients)} client(s) notified")
    return {"ok": True, "clients": len(connected_clients)}


class AppSwitch(BaseModel):
    app: str


@app.post("/push/app")
async def push_app(body: AppSwitch):
    """Switch the active app on the display."""
    global current_app
    valid = {"clock", "weather", "crypto", "photo"}
    if body.app not in valid:
        raise HTTPException(status_code=400, detail=f"Unknown app. Choose from: {valid}")
    current_app = body.app
    await broadcast({"type": "switch_app", "app": current_app})
    return {"ok": True, "app": current_app}


@app.get("/status")
async def status():
    return {
        "app": current_app,
        "last_image": last_image_path,
        "clients": len(connected_clients),
    }


# ── Frontend ───────────────────────────────────────────────────────────────────

static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    index = static_dir / "index.html"
    if not index.exists():
        return HTMLResponse("<h1>index.html not found</h1>", status_code=500)
    async with aiofiles.open(index) as f:
        return HTMLResponse(await f.read())


# ── Entrypoint ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8765, reload=False)
