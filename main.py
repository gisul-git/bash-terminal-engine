from __future__ import annotations

import asyncio
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from execution_engine import CommandExecutionEngine
from session_manager import SessionManager


app = FastAPI(title="Terminal Engine Service")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
engine = CommandExecutionEngine(required_paths=["/home/user/project"])
sessions = SessionManager()


@app.get("/health")
async def health() -> JSONResponse:
    return JSONResponse({"status": "ok", "sessions": len(sessions.sessions)})


def command_delay(command: str) -> float:
    command = command.strip().split(" ", 1)[0]
    if command == "find":
        return 0.3
    if command in {"ls", "pwd", "cd"}:
        return 0.1
    return 0.2


def format_response(session: Any, result: dict[str, Any]) -> dict[str, Any]:
    output = "\n".join(
        part for part in (result.get("output", ""), result.get("error", "")) if part
    )
    if output is None:
        output = ""

    return {
        "type": "response",
        "data": {
            "output": output,
            "prompt": sessions.generate_prompt(session),
        },
    }


def build_terminal_history(session: Any) -> str:
    lines: list[str] = []
    for entry in session.history:
        lines.append(f"{entry['prompt']}{entry['command']}")
        if entry["output"]:
            lines.append(entry["output"])
    return "\n".join(lines)


@app.websocket("/terminal")
async def terminal(websocket: WebSocket) -> None:
    print("Client connected")
    await websocket.accept()
    session = sessions.create()
    print("Sending init")

    await websocket.send_json(
        {
            "type": "init",
            "data": {
                "banner": "Welcome to Terminal\n\n",
                "prompt": sessions.generate_prompt(session),
            },
        }
    )

    try:
        while True:
            message: dict[str, Any] = await websocket.receive_json()
            print("Received:", message)
            message_type = message.get("type")

            if message_type == "command":
                command = str(message.get("data", ""))
                prompt_before = sessions.generate_prompt(session)
                result = engine.execute(session, command)
                visible_output = "\n".join(
                    part for part in (result.get("output", ""), result.get("error", "")) if part
                )
                if visible_output is None:
                    visible_output = ""
                session.history.append(
                    {
                        "prompt": prompt_before,
                        "command": command,
                        "output": visible_output,
                    }
                )
                await asyncio.sleep(command_delay(command))

                print("Sending response")
                await websocket.send_json(format_response(session, result))
                continue

            if message_type == "mode":
                mode = str(message.get("data", "")).lower()
                if mode in {"exam", "learning"}:
                    session.mode = mode
                    result = {
                        "output": f"Mode set to {mode}" if mode == "learning" else "",
                    "error": "",
                    "message": f"Mode set to {mode}",
                    "status": "success",
                    "exit_code": 0,
                    "duration_ms": 0,
                    }
                else:
                    result = {
                        "output": "",
                        "error": "mode: expected exam or learning",
                    "message": "",
                    "status": "error",
                    "exit_code": 1,
                    "duration_ms": 0,
                }
                print("Sending response")
                await websocket.send_json(format_response(session, result))
                continue

            if message_type == "submit":
                session.result = engine.evaluate(session)
                history_output = build_terminal_history(session)
                if history_output is None:
                    history_output = ""
                print("Sending response")
                await websocket.send_json(
                    {
                        "type": "response",
                        "data": {
                            "output": history_output,
                            "prompt": sessions.generate_prompt(session),
                        },
                    }
                )
                continue

            print("Sending response")
            await websocket.send_json(
                {
                    "type": "response",
                    "data": {
                        "output": f"Unsupported message type: {message_type}",
                        "prompt": sessions.generate_prompt(session),
                    },
                }
            )

    except WebSocketDisconnect:
        print("Client disconnected")
        sessions.delete(session.session_id)
