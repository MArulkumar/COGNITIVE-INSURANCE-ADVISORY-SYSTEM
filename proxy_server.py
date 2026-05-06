"""
InsureBot AI — Local Proxy Server (Python)
Relays requests to NVIDIA NIM API to bypass browser CORS restrictions.

Usage:
    pip install requests
    python proxy_server.py

Then open http://localhost:3000 in your browser.
"""

import json
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

import requests

PORT = 3000
NVIDIA_API_HOST = "https://integrate.api.nvidia.com"
HTML_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "insurebot-ai.html")

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, Authorization",
}


class ProxyHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        """Suppress default per-request logging (optional — remove to re-enable)."""
        pass

    def send_cors_headers(self):
        for key, value in CORS_HEADERS.items():
            self.send_header(key, value)

    # ── OPTIONS preflight ────────────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors_headers()
        self.end_headers()

    # ── GET ──────────────────────────────────────────────────────────────
    def do_GET(self):
        parsed = urlparse(self.path)

        # List available models
        if parsed.path == "/api/nvidia/models":
            auth = self.headers.get("Authorization", "")
            try:
                r = requests.get(
                    f"{NVIDIA_API_HOST}/v1/models",
                    headers={"Authorization": auth},
                    timeout=30,
                )
                self.send_response(r.status_code)
                self.send_header("Content-Type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(r.content)
            except Exception as e:
                self._send_error(502, str(e))
            return

        # Serve HTML at root
        if parsed.path in ("/", "/insurebot-ai.html"):
            try:
                with open(HTML_FILE, "r", encoding="utf-8") as f:
                    html = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(html.encode("utf-8"))
            except FileNotFoundError:
                self.send_response(404)
                self.end_headers()
                self.wfile.write(
                    b"insurebot-ai.html not found. "
                    b"Make sure proxy_server.py and insurebot-ai.html are in the same folder."
                )
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not found")

    # ── POST ─────────────────────────────────────────────────────────────
    def do_POST(self):
        parsed = urlparse(self.path)

        if parsed.path == "/api/nvidia":
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)
            auth = self.headers.get("Authorization", "")

            try:
                r = requests.post(
                    f"{NVIDIA_API_HOST}/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": auth,
                    },
                    data=body,
                    timeout=60,
                )
                self.send_response(r.status_code)
                self.send_header("Content-Type", "application/json")
                self.send_cors_headers()
                self.end_headers()
                self.wfile.write(r.content)
            except Exception as e:
                print(f"[Proxy Error] {e}")
                self._send_error(502, f"Proxy error: {e}")
            return

        self.send_response(405)
        self.send_header("Content-Type", "application/json")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Method not allowed"}).encode())

    # ── Helper ───────────────────────────────────────────────────────────
    def _send_error(self, code: int, message: str):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps({"error": message}).encode())


def main():
    server = HTTPServer(("", PORT), ProxyHandler)
    print()
    print("  ✅  InsureBot AI Proxy Server running")
    print(f"  🌐  Open in browser: http://localhost:{PORT}")
    print("  🔁  Proxying API calls to NVIDIA NIM (CORS-safe)")
    print()
    print("  Press Ctrl+C to stop.")
    print()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  🛑  Server stopped.")
        server.server_close()


if __name__ == "__main__":
    main()
