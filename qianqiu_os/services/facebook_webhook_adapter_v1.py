# ================================================================
# Copyright (c) 2026 程特峰 (Tefeng Cheng)
# All Rights Reserved.
#
# Project: AgentOS / Wolong Agent System
# This source code is proprietary and confidential.
# Unauthorized copying, modification, distribution or use
# of this software, in whole or in part, is strictly prohibited.
# ================================================================

from __future__ import annotations

import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

VERIFY_TOKEN = "wolong_facebook_verify_20260316"

BASE_DIR = Path(__file__).resolve().parents[1]
RUNTIME_DIR = BASE_DIR / "runtime_sessions" / "facebook"
RUNTIME_DIR.mkdir(parents=True, exist_ok=True)


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class FacebookWebhookHandler(BaseHTTPRequestHandler):
    def _send_text(self, status: int, text: str):
        body = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: int, payload):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != "/webhook/facebook":
            self._send_text(404, "not found")
            return

        query = parse_qs(parsed.query)
        mode = query.get("hub.mode", [""])[0]
        token = query.get("hub.verify_token", [""])[0]
        challenge = query.get("hub.challenge", [""])[0]

        if mode == "subscribe" and token == VERIFY_TOKEN:
            self._send_text(200, challenge or "")
            return

        self._send_text(403, "verification failed")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/webhook/facebook":
            self._send_text(404, "not found")
            return

        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length > 0 else b""

        try:
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception:
            payload = {"raw_text": raw.decode("utf-8", errors="ignore")}

        file_path = RUNTIME_DIR / f"facebook_inbound_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        _write_json(
            file_path,
            {
                "received_at": _now_str(),
                "source": "facebook_webhook",
                "payload": payload,
            },
        )

        self._send_json(200, {"success": True, "stored_at": str(file_path)})

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", 8008), FacebookWebhookHandler)
    print("Facebook webhook server running on http://127.0.0.1:8008")
    server.serve_forever()
