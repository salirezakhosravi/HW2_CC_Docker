"""Contract for the lab queue. Do not weaken these tests."""

from __future__ import annotations

import socket
import threading
import time
from http.client import HTTPConnection
from pathlib import Path

import pytest

from app.queue import join, take
from app.server import serve


@pytest.mark.parametrize("name", ["", "   ", "a" * 41, "ali\n", "\n"])
def test_rejected_name_does_not_change_file(tmp_path: Path, name: str) -> None:
    path = tmp_path / "queue.txt"
    path.write_text("kept\n", encoding="utf-8")
    before = path.read_bytes()
    with pytest.raises(ValueError):
        join(path, name)
    assert path.read_bytes() == before


def test_rejected_name_does_not_create_file(tmp_path: Path) -> None:
    path = tmp_path / "queue.txt"
    with pytest.raises(ValueError):
        join(path, "")
    assert not path.exists()


def test_join_take_and_ticket_number(tmp_path: Path) -> None:
    path = tmp_path / "queue.txt"
    assert join(path, "  Ali  ") == 1
    assert join(path, "ب" * 40) == 2
    assert path.read_text(encoding="utf-8").splitlines() == ["Ali", "ب" * 40]
    assert take(path) == "Ali"
    assert join(path, "Sara") == 2
    assert take(path) == "ب" * 40
    assert take(path) == "Sara"


def test_take_missing_or_empty(tmp_path: Path) -> None:
    path = tmp_path / "queue.txt"
    with pytest.raises(LookupError):
        take(path)
    path.write_text("", encoding="utf-8")
    with pytest.raises(LookupError):
        take(path)


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _start(tmp_path: Path) -> int:
    port = _free_port()
    thread = threading.Thread(
        target=serve,
        args=("127.0.0.1", port, str(tmp_path)),
        daemon=True,
    )
    thread.start()
    deadline = time.time() + 3
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.2):
                return port
        except OSError:
            time.sleep(0.05)
    raise AssertionError("server did not start")


def _request(port: int, method: str, path: str, body: str | None = None) -> tuple[int, str]:
    connection = HTTPConnection("127.0.0.1", port, timeout=2)
    data = None
    headers = {}
    if body is not None:
        data = body.encode("utf-8")
        headers["Content-Type"] = "application/json"
        headers["Content-Length"] = str(len(data))
    connection.request(method, path, body=data, headers=headers)
    response = connection.getresponse()
    payload = response.read().decode("utf-8")
    connection.close()
    return response.status, payload


def test_http_health_join_and_next(tmp_path: Path) -> None:
    port = _start(tmp_path)
    status, body = _request(port, "GET", "/health")
    assert (status, body) == (200, "ok")

    status, body = _request(port, "POST", "/join", '{"name": "نگار"}')
    assert (status, body) == (200, "1")
    status, body = _request(port, "POST", "/join", '{"name": "Sara"}')
    assert (status, body) == (200, "2")

    status, body = _request(port, "POST", "/next")
    assert (status, body) == (200, "نگار")
    status, body = _request(port, "POST", "/next")
    assert (status, body) == (200, "Sara")
    status, body = _request(port, "POST", "/next")
    assert (status, body) == (404, "empty")


def test_http_invalid_name_keeps_file(tmp_path: Path) -> None:
    port = _start(tmp_path)
    status, body = _request(port, "POST", "/join", '{"name": "Ali"}')
    assert (status, body) == (200, "1")
    before = (tmp_path / "queue.txt").read_bytes()

    for payload in ('{"name": ""}', '{"name": "   "}', '{"name": "' + ("x" * 41) + '"}', "{}", "not-json"):
        status, _body = _request(port, "POST", "/join", payload)
        assert status == 400
        assert (tmp_path / "queue.txt").read_bytes() == before
