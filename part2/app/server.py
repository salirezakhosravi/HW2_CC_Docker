"""HTTP API for the lab queue.

Bodies are plain text, not JSON:
  GET  /health                  200  ok
  POST /join   {"name": "..."}  200  ticket number, or 400 if the name is rejected
  POST /next                    200  name, or 404 empty

Listen on PORT (default 8000). The queue file is DATA_DIR/queue.txt
(DATA_DIR defaults to /data). main() must bind 0.0.0.0 so the published
port is reachable. serve() must use the host it is given.
"""

import os


def serve(host: str, port: int, data_dir: str) -> None:
    """Listen until the process is stopped. Use join and take from app.queue."""
    raise NotImplementedError("TODO: serve the queue API")


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    data_dir = os.environ.get("DATA_DIR", "/data")
    serve("0.0.0.0", port, data_dir)


if __name__ == "__main__":
    main()
