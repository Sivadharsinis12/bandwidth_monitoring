from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import asyncio
import os
from traffic_monitor import device_stats, start_monitor
from database import init_db

app = FastAPI()

# Initialize database
init_db()

# Insert sample data if table is empty
from database import save_history_entry
from models import History
from datetime import datetime, timedelta
import sqlite3

conn = sqlite3.connect('bandwidth.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM history')
count = cursor.fetchone()[0]
conn.close()

if count == 0:
    # Insert sample history data
    sample_data = [
        History(datetime.now().isoformat(), "Workstation-01", "192.168.1.10", 50.5, 20.3, "Monitor", "Sample entry 1"),
        History((datetime.now() - timedelta(minutes=1)).isoformat(), "Mobile-Device", "192.168.1.15", 30.2, 15.1, "Monitor", "Sample entry 2"),
        History((datetime.now() - timedelta(minutes=2)).isoformat(), "Workstation-01", "192.168.1.10", 45.8, 18.7, "Monitor", "Sample entry 3"),
    ]
    for entry in sample_data:
        save_history_entry(entry)

# Start the background monitoring thread
start_monitor()

# Correct Pathing
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Ensure this points to where your CSS/JS actually are
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Mount static files FIRST
if os.path.exists(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# 2. Page Routes
@app.get("/")
async def serve_index():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/dashboard")
async def serve_dashboard():
    return FileResponse(os.path.join(FRONTEND_DIR, "dashboard.html"))

@app.get("/history")
async def serve_history():
    return FileResponse(os.path.join(FRONTEND_DIR, "history.html"))

# 3. API Routes
@app.get("/api/history")
async def get_history():
    from database import get_history
    return get_history()

@app.get("/api/analytics")
async def get_analytics():
    from database import get_analytics
    return get_analytics()

# 4. WebSocket - Updated to handle the dictionary correctly
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # We send a copy to avoid dictionary mutation errors during broadcast
            await websocket.send_json(device_stats.copy())
            await asyncio.sleep(1)
    except WebSocketDisconnect:
        print("Client disconnected")
