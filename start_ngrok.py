import os
import signal
import sys
import time
from pathlib import Path

import ngrok


def load_env(env_path: Path) -> None:
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def main() -> int:
    load_env(Path(".env"))

    auth_token = os.getenv("NGROK_AUTHTOKEN")
    domain = os.getenv("NGROK_DOMAIN")
    if not auth_token:
        print("Missing NGROK_AUTHTOKEN in .env")
        return 1

    ngrok.set_auth_token(auth_token)
    options = {}
    if domain:
        options["domain"] = domain
    listener = ngrok.forward("http://localhost:80", **options)
    url = listener.url()
    print(f"ngrok tunnel started: {url}")
    print("Press Ctrl+C to stop the tunnel.")

    def shutdown(*_args):
        ngrok.disconnect(url)
        print("ngrok tunnel stopped")
        raise SystemExit(0)

    signal.signal(signal.SIGINT, shutdown)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, shutdown)

    while True:
        time.sleep(60)


if __name__ == "__main__":
    raise SystemExit(main())
