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
requirements.txt
README.md
```

## Install

```bash
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --host 127.0.0.1 --port 4041
```

The WebSocket client connects to:

```text
ws://localhost:4041/terminal
```

## Backend

- FastAPI WebSocket endpoint: `/terminal`
- One isolated session per WebSocket connection
- Session fields:
  - `cwd`
  - virtual file system
  - `history`
  - `env`
  - `processes`
  - `mode`
- Virtual root starts at `/home/user`
- Dict-backed filesystem
- Session is deleted on disconnect

## Commands

Supported simulated bash commands:

```text
pwd
ls
cd
mkdir
touch
echo
cat
```

Also supported:

- Relative and absolute paths
- `..` and `~`
- Chaining with `&&`
- `echo text > file`
- `echo text >> file`
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
    "banner": "Welcome to Linux Terminal\n",
    "prompt": "user@server:~$ "
  }
}
```

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
