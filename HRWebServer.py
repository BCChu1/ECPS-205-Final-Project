import asyncio
import websockets
import threading
import http.server
import socketserver
from max30102.heartrate_monitor import HeartRateMonitor
import json
import time

HTTP_PORT = 8888
WS_PORT = 8765
CLIENTS = set()

# ---------------- HTTP SERVER ----------------
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/":
            self.path = "index.html"
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

threading.Thread(
    target=lambda: socketserver.TCPServer(("", HTTP_PORT), MyHandler).serve_forever(),
    daemon=True
).start()
print(f"HTTP server running at http://localhost:{HTTP_PORT}")

# ---------------- MAX30102 SENSOR ----------------
hrm = HeartRateMonitor(print_raw=False, print_result=False)

def sensor_thread():
    hrm.start_sensor()  # blocking loop
    print("MAX30102 sensor started")

threading.Thread(target=sensor_thread, daemon=True).start()

# ---------------- WEBSOCKET ----------------
async def ws_handler(websocket):
    CLIENTS.add(websocket)
    print("WebSocket client connected")
    try:
        await websocket.wait_closed()  # keep connection open
    finally:
        CLIENTS.remove(websocket)
        print("WebSocket client disconnected")

async def sensor_stream():
    while True:
        bpm = hrm.bpm or 0
        spo2 = hrm.sp02 or 0
        ir = hrm.rawIR or 0
        red = hrm.rawRed or 0
        data = {"bpm": bpm, "spo2": spo2, "ir": ir, "red": red, "timestamp": time.time()}

        if CLIENTS:
            msg = json.dumps(data)
            await asyncio.gather(*(ws.send(msg) for ws in CLIENTS))

        await asyncio.sleep(1)

async def main():
    print(f"WebSocket running on ws://0.0.0.0:{WS_PORT}")
    async with websockets.serve(ws_handler, "0.0.0.0", WS_PORT):
        await sensor_stream()

asyncio.run(main())
