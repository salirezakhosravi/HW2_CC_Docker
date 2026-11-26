"""HTTP API for the lab queue.

Bodies are plain text, not JSON:
  GET  /health                  200  ok
  POST /join   {"name": "..."}  200  ticket number, or 400 if the name is rejected
  POST /next                    200  name, or 404 empty

Listen on PORT (default 8000). The queue file is DATA_DIR/queue.txt
(DATA_DIR defaults to /data). main() must bind 0.0.0.0 so the published
port is reachable. serve() must use the host it is given.
"""

##HELLO

import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json

from app.queue import join, take

def handle_join(queue_file: Path):

    class Handler(BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def _send(self, status: int, text: str) -> None:
            body = text.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _read_body(self) -> bytes:
            try:
                length = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                length = 0
            return self.rfile.read(length) if length > 0 else b""

        def do_GET(self) -> None:
            if self.path == "/health":
                self._send(200, "ok")
            else:
                self._send(404, "not found")

        def do_POST(self) -> None:
            body = self._read_body()
            if self.path == "/join":
                try:
                    data = json.loads(body.decode("utf-8"))
                    name = data["name"]
                    if not isinstance(name, str):
                        raise ValueError("name must be a string")
                    ticket = join(queue_file, name)
                except (ValueError, KeyError, TypeError, UnicodeDecodeError):
                    self._send(400, "bad request")
                    return
                self._send(200, str(ticket))
            elif self.path == "/next":
                try:
                    name = take(queue_file)
                except LookupError:
                    self._send(404, "empty")
                    return
                self._send(200, name)
            else:
                self._send(404, "not found")

        def log_message(self, format, *args):
            super().log_message(format, *args)

    return Handler

def serve(host: str, port: int, data_dir: str) -> None:
    """Listen until the process is stopped. Use join and take from app.queue."""
    queue_file  = Path(data_dir) / "queue.txt"

    server = ThreadingHTTPServer((host, port), handle_join(queue_file))

    try:
        server.serve_forever()
    finally: 
        server.server_close()


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    data_dir = os.environ.get("DATA_DIR", "/data")
    serve("0.0.0.0", port, data_dir)


if __name__ == "__main__":
    main()
