# Calculator Stack

Simple full-stack calculator application with:

- React frontend
- FastAPI backend
- Redis queue
- Celery worker
- Postgres database
- Nginx reverse proxy
- ngrok public tunnel

## Architecture

Browser traffic goes to Nginx first.

Request flow:

1. Browser calls `http://localhost` or the ngrok URL
2. Nginx serves the React frontend
3. Nginx proxies `/api/*` to FastAPI
4. FastAPI stores users and calculation requests in Postgres
5. FastAPI pushes calculation jobs to Redis
6. Celery worker consumes jobs from Redis
7. Worker updates result status in Postgres
8. Frontend polls the backend through Nginx and shows the result

## Services

The Docker Compose stack includes:

- `nginx`
- `backend`
- `worker`
- `postgres`
- `redis`

All services use the Docker network `spr`.

## Project structure

- [docker-compose.yml](c:/Users/SPR/Desktop/project/docker-compose.yml)
- [backend](c:/Users/SPR/Desktop/project/backend)
- [frontend](c:/Users/SPR/Desktop/project/frontend)
- [nginx/nginx.conf](c:/Users/SPR/Desktop/project/nginx/nginx.conf)
- [test_stack.py](c:/Users/SPR/Desktop/project/test_stack.py)
- [start_ngrok.py](c:/Users/SPR/Desktop/project/start_ngrok.py)
- [start_stack.bat](c:/Users/SPR/Desktop/project/start_stack.bat)
- [stop_stack.bat](c:/Users/SPR/Desktop/project/stop_stack.bat)

## Environment

Main environment values are stored in [`.env`](c:/Users/SPR/Desktop/project/.env):

- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `REDIS_HOST`
- `REDIS_PORT`
- `SECRET_KEY`
- `ACCESS_TOKEN_EXPIRE_MINUTES`
- `MAX_QUEUE_SIZE`
- `CELERY_WORKER_CONCURRENCY`
- `NGROK_AUTHTOKEN`
- `NGROK_DOMAIN`

## Run

### Option 1: Batch scripts

Start:

```bat
start_stack.bat
```

This also starts the ngrok tunnel.

Stop:

```bat
stop_stack.bat
```

This also stops the ngrok tunnel.

### Option 2: Manual commands

Install Python dependencies:

```bash
uv sync
```

Install frontend dependencies:

```bash
npm --prefix frontend install
```

Build frontend:

```bash
npm --prefix frontend run build
```

Start stack:

```bash
docker compose up -d --build
```

Start ngrok tunnel:

```bash
uv run python start_ngrok.py
```

Stop stack:

```bash
docker compose down
```

## Open the app

Use:

```text
http://localhost
```

Public access:

```text
https://alfreda-unrevetted-latonya.ngrok-free.dev
```

The ngrok tunnel must be running for the public URL to work.

## Features

- user registration
- user login
- logout
- JWT bearer authentication
- queued calculator operations
- calculation history per user
- persistent storage in Postgres

## Verify the stack

Run:

```bash
uv run python test_stack.py
```

This verifies:

- Nginx is reachable
- Postgres is reachable
- Redis is reachable
- backend health works through Nginx
- ngrok public health works when the tunnel is running
- register works
- login works
- authenticated profile works
- calculation queueing works
- Celery processing works
- Postgres persistence works

## Logs

Generate a stack log snapshot:

```powershell
powershell -ExecutionPolicy Bypass -File .\frontend\refresh-logs.ps1
```

Log output file:

- [frontend/stack-status.log](c:/Users/SPR/Desktop/project/frontend/stack-status.log)

## Data persistence

Postgres data is stored in the named Docker volume `postgres_data`.

Normal stop/start does not remove data.

Data is removed only if you explicitly remove the volume, for example with:

```bash
docker compose down -v
```

## Current defaults

- Nginx: `localhost`
- Postgres: `localhost:5432`
- Redis: `localhost:6379`
- queue limit: `100`
- worker concurrency: `4`
- public URL: `alfreda-unrevetted-latonya.ngrok-free.dev`

## Production note

Before using this beyond local development:

- replace `SECRET_KEY` with a stronger value
- rotate `NGROK_AUTHTOKEN` if it has been exposed
- review CORS and auth settings
- add proper migrations
- rotate exposed tokens and secrets if needed
