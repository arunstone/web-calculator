# Session Notes

## What was built

This project was set up as a Docker-based full-stack calculator application with:

- React frontend
- FastAPI backend
- Redis for queue transport
- Celery worker for background jobs
- Postgres for users and calculation history
- Nginx as the single browser-facing entry point
- ngrok as the public tunnel

## Containers

The stack currently runs with 5 containers:

- `local-nginx`
- `local-backend`
- `local-worker`
- `local-postgres`
- `local-redis`

All containers are attached to the Docker network `spr`.

## Database and queue setup

Postgres was added through Docker Compose and configured with:

- database: `appdb`
- user: `appuser`
- password: `REMOVED_SECRET`

Redis was added as the queue broker for Celery.

Queue and worker limits were added to `.env`:

- `MAX_QUEUE_SIZE=100`
- `CELERY_WORKER_CONCURRENCY=4`

## Python setup

The project was initialized with `uv`.

Important Python files:

- `pyproject.toml`
- `uv.lock`
- `test_stack.py`

The old `requirements.txt` was removed to keep `uv` as the single dependency source.

## Frontend and backend

Frontend:

- React app created under `frontend/`
- built with Vite
- served by Nginx

Backend:

- FastAPI app created under `backend/`
- JWT-based login/register flow
- users stored in Postgres
- calculation requests stored in Postgres
- Celery worker processes queued calculations

## Routing

Nginx was configured so that:

- `/` serves the React app
- `/api/*` proxies to FastAPI

This keeps browser traffic going through Nginx.

Current local access:

- `http://localhost`

Current public access:

- `https://alfreda-unrevetted-latonya.ngrok-free.dev`

## Logging and verification

A stack log snapshot script was added:

- `frontend/refresh-logs.ps1`

It writes:

- `frontend/stack-status.log`

A broader end-to-end verification script was also added:

- `test_stack.py`

It checks:

- Nginx reachability
- Postgres reachability
- Redis reachability
- backend health through Nginx
- register
- login
- authenticated profile fetch
- calculator queueing
- Celery processing
- Postgres persistence

## Utility scripts

Two batch files were added in the project root:

- `start_stack.bat`
- `stop_stack.bat`

`start_stack.bat`:

- starts Docker Desktop
- waits for Docker
- installs frontend packages
- builds frontend
- starts the stack
- starts the ngrok tunnel

`stop_stack.bat`:

- stops the ngrok tunnel
- stops the Compose stack
- stops Docker Desktop processes

There is also an ngrok runner:

- `start_ngrok.py`

## Notes

- Postgres data persists across normal stop/start because it uses the named volume `postgres_data`
- removing the volume would delete the stored data
- the JWT secret currently works, but should be replaced with a longer production-grade value
- ngrok is the current public access method for this project
- Namecheap/DDNS setup was removed from the project files
- the app was verified through browser access on both localhost and the ngrok URL
