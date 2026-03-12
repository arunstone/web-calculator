import json
import os
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4

import psycopg


def load_env(env_path: Path) -> None:
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def tcp_check(name: str, host: str, port: int) -> None:
    print(f"[check] {name} TCP {host}:{port}")
    with socket.create_connection((host, port), timeout=5):
        print(f"[ok] {name} is reachable")


def http_json(method: str, url: str, payload: dict | None = None, token: str | None = None) -> dict:
    body = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def main() -> int:
    load_env(Path(".env"))

    postgres_host = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port = int(os.getenv("POSTGRES_PORT", "5432"))
    postgres_db = os.getenv("POSTGRES_DB", "appdb")
    postgres_user = os.getenv("POSTGRES_USER", "appuser")
    postgres_password = os.getenv("POSTGRES_PASSWORD", "REMOVED_SECRET")
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    app_url = os.getenv("APP_BASE_URL", "http://localhost")
    ngrok_domain = os.getenv("NGROK_DOMAIN", "").strip()

    test_id = uuid4().hex[:8]
    username = f"user_{test_id}"
    email = f"{username}@example.com"
    password = "password123"

    try:
        tcp_check("nginx", "localhost", 80)
        tcp_check("postgres", postgres_host, postgres_port)
        tcp_check("redis", redis_host, redis_port)

        print("[check] GET /api/health through nginx")
        health = http_json("GET", f"{app_url}/api/health")
        if health.get("status") != "ok":
            raise RuntimeError(f"Unexpected health response: {health}")
        print("[ok] nginx -> backend routing works")

        if ngrok_domain:
            public_url = f"https://{ngrok_domain}"
            print(f"[check] GET /api/health through ngrok {public_url}")
            public_health = http_json("GET", f"{public_url}/api/health")
            if public_health.get("status") != "ok":
                raise RuntimeError(f"Unexpected ngrok health response: {public_health}")
            print("[ok] ngrok -> nginx -> backend routing works")

        print(f"[check] register {email}")
        register_response = http_json(
            "POST",
            f"{app_url}/api/auth/register",
            {"username": username, "email": email, "password": password},
        )
        print(f"[ok] registered user id={register_response['id']}")

        print(f"[check] login {email}")
        login_response = http_json(
            "POST",
            f"{app_url}/api/auth/login",
            {"email": email, "password": password},
        )
        token = login_response["access_token"]
        print("[ok] login returned bearer token")

        print("[check] GET /api/auth/me")
        me = http_json("GET", f"{app_url}/api/auth/me", token=token)
        if me["email"] != email:
            raise RuntimeError(f"Unexpected profile response: {me}")
        print("[ok] authenticated profile lookup works")

        print("[check] queue calculator request")
        queue_response = http_json(
            "POST",
            f"{app_url}/api/calculate",
            {"operand_a": 9, "operand_b": 3, "operation": "divide"},
            token=token,
        )
        request_id = queue_response["request_id"]
        print(f"[ok] calculation queued request_id={request_id}")

        print("[check] wait for celery to process request")
        deadline = time.time() + 20
        latest_item = None
        while time.time() < deadline:
            history = http_json("GET", f"{app_url}/api/calculations", token=token)
            latest_item = next((item for item in history if item["id"] == request_id), None)
            if latest_item and latest_item["status"] == "completed":
                break
            time.sleep(1)

        if not latest_item or latest_item["status"] != "completed":
            raise RuntimeError(f"Calculation did not complete in time: {latest_item}")
        if float(latest_item["result"]) != 3.0:
            raise RuntimeError(f"Unexpected calculation result: {latest_item}")
        print("[ok] celery consumed the redis queue and stored the result")

        print("[check] verify persisted rows in postgres")
        with psycopg.connect(
            host=postgres_host,
            port=postgres_port,
            dbname=postgres_db,
            user=postgres_user,
            password=postgres_password,
            connect_timeout=5,
        ) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, username, email FROM users WHERE email = %s", (email,))
                user_row = cur.fetchone()
                cur.execute(
                    """
                    SELECT id, operation, status, result
                    FROM calculation_requests
                    WHERE id = %s
                    """,
                    (request_id,),
                )
                calc_row = cur.fetchone()

        if not user_row:
            raise RuntimeError("Registered user was not found in postgres")
        if not calc_row:
            raise RuntimeError("Calculation request was not found in postgres")
        print("[ok] postgres contains the user and calculation rows")

        print("")
        print("Stack verification passed.")
        print(f"User: {email}")
        print(f"Calculation request: {request_id}")
        return 0
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print(f"[error] HTTP {exc.code}: {body}")
        return 1
    except Exception as exc:
        print(f"[error] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
