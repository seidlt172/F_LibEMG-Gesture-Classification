import socket


def send_gesture_to_middleware(gesture: str,
                               host: str = "127.0.0.1",
                               port: int = 65432,
                               timeout: float = 3.0) -> bool:
    payload = str(gesture or "NONE").encode("utf-8")
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.sendall(payload)
        return True
    except ConnectionRefusedError:
        print("[Middleware] Verbindung abgelehnt: Middleware läuft nicht.")
    except socket.timeout:
        print("[Middleware] Timeout beim Verbinden.")
    except OSError as exc:
        print(f"[Middleware] Socket-Fehler: {exc}")
    return False
