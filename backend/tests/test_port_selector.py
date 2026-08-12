from __future__ import annotations

import socket
from pathlib import Path

import pytest

from app.tools.select_port import find_available_port


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def test_find_available_port_skips_an_occupied_port() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        occupied_port = int(occupied.getsockname()[1])
        fallback_port = _free_port()

        assert find_available_port("127.0.0.1", [occupied_port, fallback_port]) == fallback_port


def test_find_available_port_fails_when_every_candidate_is_unavailable() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as occupied:
        occupied.bind(("127.0.0.1", 0))
        occupied.listen(1)
        occupied_port = int(occupied.getsockname()[1])

        with pytest.raises(RuntimeError, match="没有可用端口"):
            find_available_port("127.0.0.1", [occupied_port])


def test_launchers_use_the_selected_port() -> None:
    project_root = Path(__file__).resolve().parents[2]

    for launcher_name in ("start.bat", "启动项目.bat"):
        launcher_path = project_root / launcher_name
        launcher_bytes = launcher_path.read_bytes()
        assert not launcher_bytes.startswith(b"\xef\xbb\xbf")
        assert b"\r\n" in launcher_bytes
        launcher = launcher_bytes.decode("utf-8")
        assert "select_port.py" in launcher
        assert "selected_port.txt" in launcher
        assert "set /p APP_PORT=" in launcher
        assert "for /f" not in launcher.lower()
        assert "--port %APP_PORT%" in launcher
        assert "127.0.0.1:%APP_PORT%/materials" in launcher
