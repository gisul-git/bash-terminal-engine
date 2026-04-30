# Production Terminal Engine

FastAPI + WebSockets terminal simulator with a fully in-memory bash-like
environment. No command is ever executed on the host OS.

## Files

```text
main.py
execution_engine.py
session_manager.py
Dockerfile
docker-compose.yml
gunicorn_conf.py
uvicorn_worker.py
nginx-terminal.conf
requirements.txt
README.md
```

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --host 127.0.0.1 --port 4041 --ws-ping-interval 20 --ws-ping-timeout 120
```

Production Docker runs Gunicorn with Uvicorn workers:

```bash
docker compose up --build
```

The WebSocket client connects to:

```text
ws://localhost:4041/terminal
```

To reconnect to an existing in-memory session, pass the previous `session_id`:

```text
ws://localhost:4041/terminal?session_id=<session-id>
```

## Backend

- FastAPI WebSocket endpoint: `/terminal`
- One isolated session per `session_id`
- Session fields:
  - `cwd`
  - virtual file system
  - `history`
  - `env`
  - `processes`
  - `mode`
- Virtual root starts at `/home/user`
- Dict-backed filesystem
- Session is preserved across reconnects
- Idle sessions are cleaned up after 2 hours
- Server sends `{ "type": "ping" }` every 20 seconds
- Client should reply with `{ "type": "pong" }`

## Commands

Supported simulated bash commands:

```text
pwd
ls
cd
mkdir
touch
rm
echo
cat
grep
wc
head
tail
sort
uniq
cut
tr
chmod
find
ps
kill
env
export
ping
mode
```

Also supported:

- Relative and absolute paths
- `..` and `~`
- Chaining with `&&`
- Pipelines with `|`
- `echo text > file`
- `echo text >> file`
- Output redirection with `>` and `>>`
- Bash-style errors such as `No such file or directory`

## WebSocket Protocol

Client command:

```json
{ "type": "command", "data": "mkdir test" }
```

Client submit:

```json
{ "type": "submit" }
```

Server init:

```json
{
  "type": "init",
  "data": {
    "session_id": "session-id",
    "prompt": "user@server:~$ "
  }
}
```

Server heartbeat:

```json
{ "type": "ping" }
```

Client heartbeat response:

```json
{ "type": "pong" }
```

## Production Notes

- Default Docker log level is `WARNING`.
- `WEB_CONCURRENCY` controls Gunicorn workers. The default formula is `(2 x CPU cores) + 1`; `docker-compose.yml` pins it to `4`.
- `timeout` is `3600`, `keepalive` is `120`, and WebSocket ping timeout is `120`.
- Use `nginx-terminal.conf` when deploying behind Nginx so idle WebSockets are not closed early.
- If you run multiple containers, add sticky sessions at the load balancer or move sessions to Redis.

Server command response:

```json
{
  "type": "response",
  "data": {
    "output": "file.txt",
    "prompt": "user@server:~/test$ "
  }
}
```

Server submit response:

```json
{ "type": "response", "data": { "output": "user@server:~$ pwd", "prompt": "user@server:~$ " } }
```

## Evaluation

The default evaluation checks whether this path exists:

```text
/home/user/project
```

Try:

```bash
mkdir project
\submit
```
