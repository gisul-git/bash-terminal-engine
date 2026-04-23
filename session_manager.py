from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TypedDict
from uuid import uuid4


FileSystem = dict[str, Any]


class HistoryEntry(TypedDict):
    prompt: str
    command: str
    output: str


def default_filesystem() -> FileSystem:
    return {
        "type": "dir",
        "children": {
            "home": {
                "type": "dir",
                "children": {
                    "user": {
                        "type": "dir",
                        "children": {},
                        "permissions": "755",
                    },
                },
                "permissions": "755",
            },
        },
        "permissions": "755",
    }


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class TerminalSession:
    session_id: str = field(default_factory=lambda: str(uuid4()))
    cwd: str = "/home/user"
    fs: FileSystem = field(default_factory=default_filesystem)
    history: list[HistoryEntry] = field(default_factory=list)
    username: str = "user"
    hostname: str = "server"
    created_at: str = field(default_factory=utc_now_iso)
    home: str = "/home/user"
    mode: str = "learning"
    env: dict[str, str] = field(default_factory=dict)
    result: dict[str, Any] = field(default_factory=dict)
    processes: list[dict[str, str]] = field(
        default_factory=lambda: [
            {"pid": "101", "name": "nginx"},
            {"pid": "102", "name": "node"},
            {"pid": "103", "name": "postgres"},
        ]
    )


class SessionManager:
    def __init__(self) -> None:
        self.sessions: dict[str, TerminalSession] = {}

    def create(self) -> TerminalSession:
        session = TerminalSession()
        self.sessions[session.session_id] = session
        return session

    def get(self, session_id: str) -> TerminalSession | None:
        return self.sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def generate_prompt(self, session: TerminalSession) -> str:
        display_path = self._display_path(session)
        return f"{session.username}@{session.hostname}:{display_path}$ "

    def prompt(self, session: TerminalSession) -> str:
        return self.generate_prompt(session)

    def _display_path(self, session: TerminalSession) -> str:
        if session.cwd == session.home:
            return "~"
        if session.cwd.startswith(f"{session.home}/"):
            return "~" + session.cwd[len(session.home) :]
        return session.cwd
