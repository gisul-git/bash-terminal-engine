from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from execution_engine import CommandExecutionEngine
from session_manager import SessionManager


logging.basicConfig(
    level="INFO",
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("terminal-engine")

WEBSOCKET_IDLE_TIMEOUT = 300

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
    return JSONResponse({"status": "ok", "active_sessions": len(sessions.sessions)})


def command_delay(command: str) -> float:
    command = command.strip().split(" ", 1)[0]
    if command == "find":
        return 0.3
    if command in {"ls", "pwd", "cd"}:
        return 0.1
    return 0.2


def format_response(session: Any, result: dict[str, Any]) -> dict[str, Any]:
    output = result.get("output") or ""
    error = result.get("error") or ""
    combined_output = "\n".join(part for part in (output, error) if part)

    return {
        "type": "response",
        "data": {
            "output": combined_output,
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


async def send_error_response(session: Any, websocket: WebSocket, output: str) -> None:
    await websocket.send_json(
        {
            "type": "response",
            "data": {
                "output": output,
                "prompt": sessions.generate_prompt(session),
            },
        }
    )


@app.websocket("/terminal")
async def terminal(websocket: WebSocket) -> None:
    logger.info("WebSocket handler triggered")
    origin = websocket.headers.get("origin")
    await websocket.accept()
    session = sessions.create()
    logger.info("WebSocket accepted for session_id=%s origin=%s", session.session_id, origin)

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
            try:
                message = await asyncio.wait_for(
                    websocket.receive_json(), timeout=WEBSOCKET_IDLE_TIMEOUT
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "WebSocket idle timeout for session_id=%s after %ss",
                    session.session_id,
                    WEBSOCKET_IDLE_TIMEOUT,
                )
                await send_error_response(session, websocket, "Connection timed out")
                await websocket.close(code=1000, reason="Idle timeout")
                break
            except WebSocketDisconnect:
                raise
            except Exception as exc:
                logger.warning(
                    "Invalid JSON for session_id=%s error=%s",
                    session.session_id,
                    str(exc),
                )
                await send_error_response(session, websocket, "Invalid input format")
                continue

            if not isinstance(message, dict):
                logger.warning(
                    "Invalid message payload type for session_id=%s payload_type=%s",
                    session.session_id,
                    type(message).__name__,
                )
                await send_error_response(session, websocket, "Invalid input format")
                continue

            logger.info("Received: %s", message)
            if "type" not in message:
                logger.warning("Missing message type for session_id=%s", session.session_id)
                await send_error_response(session, websocket, "Missing message type")
                continue

            message_type = message.get("type")

            if message_type == "command":
                command = str(message.get("data", ""))
                prompt_before = sessions.generate_prompt(session)
                result = engine.execute(session, command)
                output = result.get("output") or ""
                error = result.get("error") or ""
                visible_output = "\n".join(part for part in (output, error) if part)
                session.history.append(
                    {
                        "prompt": prompt_before,
                        "command": command,
                        "output": visible_output,
                    }
                )
                await asyncio.sleep(command_delay(command))

                logger.info("Sending response")
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
                logger.info("Sending response")
                await websocket.send_json(format_response(session, result))
                continue

            if message_type == "submit":
                session.result = engine.evaluate(session)
                history_output = build_terminal_history(session)
                logger.info("Sending response")
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

            logger.info("Sending response")
            await send_error_response(
                session, websocket, f"Unsupported message type: {message_type}"
            )

    except WebSocketDisconnect:
        logger.info("Client disconnected session_id=%s", session.session_id)
    except Exception as exc:
        logger.exception("Unhandled error in session_id=%s error=%s", session.session_id, str(exc))
        try:
            await send_error_response(session, websocket, "Internal server error")
        except Exception:
            logger.debug(
                "Failed to send internal error response for session_id=%s",
                session.session_id,
            )
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            logger.debug("WebSocket already closed for session_id=%s", session.session_id)
    finally:
        sessions.delete(session.session_id)
