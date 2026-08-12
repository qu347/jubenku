from __future__ import annotations

import socket
import sys
from collections.abc import Iterable


def find_available_port(host: str, candidates: Iterable[int]) -> int:
    for port in candidates:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.bind((host, port))
        except OSError:
            continue
        return port
    raise RuntimeError("没有可用端口")


def main() -> int:
    try:
        port = find_available_port("127.0.0.1", range(8000, 8021))
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
