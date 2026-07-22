#!/usr/bin/env python3
import json
import mimetypes
import os
import queue
import re
import socket
import threading
import time
import urllib.error
import urllib.request
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

import serial


HOST = os.environ.get("PLANT_DIVA_HOST", "0.0.0.0")
PORT = int(os.environ.get("PLANT_DIVA_PORT", "8765"))
PICO_PORT = os.environ.get("PICO_PORT", "/dev/cu.usbmodem212301")
BAUDRATE = int(os.environ.get("PICO_BAUDRATE", "115200"))
NTFY_TOPIC = os.environ.get("PLANT_DIVA_NTFY_TOPIC")
NTFY_BASE_URL = os.environ.get("PLANT_DIVA_NTFY_BASE_URL", "https://ntfy.sh").rstrip("/")

DRY_THRESHOLD = 650
THIRSTY_THRESHOLD = 615

ROOT = Path(__file__).resolve().parent
STATIC_ROOT = ROOT / "static"
INDEX_HTML = STATIC_ROOT / "index.html"

state_lock = threading.Lock()
history = deque(maxlen=240)
latest = {
    "connected": False,
    "error": None,
    "raw": None,
    "reading": None,
    "status": "Waiting",
    "color": "neutral",
    "updated_at": None,
    "port": PICO_PORT,
}
subscribers = set()


def classify(reading):
    if reading >= DRY_THRESHOLD:
        return "Very thirsty", "red"
    if reading > THIRSTY_THRESHOLD:
        return "Getting thirsty", "blue"
    return "Good", "green"


def publish(payload):
    dead = []
    for subscriber in list(subscribers):
        try:
            subscriber.put_nowait(payload)
        except Exception:
            dead.append(subscriber)
    for subscriber in dead:
        subscribers.discard(subscriber)


def set_state(**updates):
    with state_lock:
        latest.update(updates)
        snapshot = dict(latest)
        snapshot["history"] = list(history)
    publish(snapshot)


def parse_line(line):
    match = re.search(r"Moisture:\s*(\d+)", line)
    if not match:
        return None
    reading = int(match.group(1))
    status, color = classify(reading)
    return {
        "raw": line,
        "reading": reading,
        "status": status,
        "color": color,
        "updated_at": time.time(),
    }


def local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except Exception:
        return "127.0.0.1"


def send_ntfy(title, message):
    if not NTFY_TOPIC:
        return {
            "ok": False,
            "error": "PLANT_DIVA_NTFY_TOPIC is not configured",
        }

    url = f"{NTFY_BASE_URL}/{NTFY_TOPIC}"
    request = urllib.request.Request(
        url,
        data=message.encode("utf-8"),
        method="POST",
        headers={
            "Title": title,
            "Priority": "high",
            "Tags": "seedling,droplet",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            body = response.read().decode("utf-8", errors="replace")
            return {
                "ok": 200 <= response.status < 300,
                "status": response.status,
                "response": body,
            }
    except urllib.error.HTTPError as error:
        return {
            "ok": False,
            "status": error.code,
            "error": error.read().decode("utf-8", errors="replace"),
        }
    except Exception as error:
        return {
            "ok": False,
            "error": str(error),
        }


def serial_reader():
    while True:
        try:
            with serial.Serial(PICO_PORT, BAUDRATE, timeout=1) as ser:
                set_state(connected=True, error=None, port=PICO_PORT)
                while True:
                    raw = ser.readline()
                    if not raw:
                        continue
                    line = raw.decode("utf-8", errors="replace").strip()
                    parsed = parse_line(line)
                    if parsed is None:
                        set_state(raw=line, connected=True, error=None)
                        continue
                    with state_lock:
                        history.append({
                            "t": parsed["updated_at"],
                            "reading": parsed["reading"],
                            "status": parsed["status"],
                            "color": parsed["color"],
                        })
                    set_state(**parsed, connected=True, error=None)
        except Exception as exc:
            set_state(connected=False, error=str(exc))
            time.sleep(2)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def do_HEAD(self):
        self.serve_path(head_only=True)

    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path, content_type=None, head_only=False):
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type or mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if not head_only:
            self.wfile.write(body)

    def serve_path(self, head_only=False):
        path = urlparse(self.path).path
        if path == "/":
            self.send_file(INDEX_HTML, "text/html; charset=utf-8", head_only=head_only)
            return True

        if path.startswith("/static/"):
            requested = (ROOT / path.lstrip("/")).resolve()
            if requested.is_file() and STATIC_ROOT in requested.parents:
                self.send_file(requested, head_only=head_only)
                return True

        for name in ("/manifest.json", "/service-worker.js"):
            if path == name:
                requested = STATIC_ROOT / name.lstrip("/")
                if requested.is_file():
                    self.send_file(requested, head_only=head_only)
                    return True

        if head_only:
            self.send_response(404)
            self.end_headers()
            return True

        return False

    def do_GET(self):
        path = urlparse(self.path).path
        if self.serve_path():
            return

        if path == "/api/latest":
            with state_lock:
                payload = dict(latest)
                payload["history"] = list(history)
            self.send_json(payload)
            return

        if path == "/api/config":
            self.send_json({
                "dry_threshold": DRY_THRESHOLD,
                "thirsty_threshold": THIRSTY_THRESHOLD,
                "host": HOST,
                "port": PORT,
                "lan_url": f"http://{local_ip()}:{PORT}",
                "ntfy_configured": bool(NTFY_TOPIC),
            })
            return

        if path == "/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Connection", "keep-alive")
            self.end_headers()

            q = queue.Queue(maxsize=20)
            subscribers.add(q)
            with state_lock:
                initial = dict(latest)
                initial["history"] = list(history)

            try:
                self.wfile.write(f"data: {json.dumps(initial)}\n\n".encode("utf-8"))
                self.wfile.flush()
                while True:
                    payload = q.get(timeout=20)
                    self.wfile.write(f"data: {json.dumps(payload)}\n\n".encode("utf-8"))
                    self.wfile.flush()
            except Exception:
                subscribers.discard(q)
            return

        self.send_json({"error": "not found"}, status=404)

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/test-alert":
            with state_lock:
                reading = latest.get("reading")
                status = latest.get("status")

            reading_text = "unknown" if reading is None else str(reading)
            result = send_ntfy(
                "Plant Diva Test",
                f"Test alert from Plant Diva. Current moisture: {reading_text}. Current status: {status}.",
            )
            self.send_json(result, status=200 if result.get("ok") else 500)
            return

        self.send_json({"error": "not found"}, status=404)


def main():
    threading.Thread(target=serial_reader, daemon=True).start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Plant Diva dashboard: http://{HOST}:{PORT}")
    print(f"Phone URL on this Wi-Fi: http://{local_ip()}:{PORT}")
    print(f"Reading Pico serial: {PICO_PORT} @ {BAUDRATE}")
    server.serve_forever()


if __name__ == "__main__":
    main()
