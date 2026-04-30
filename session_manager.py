from __future__ import annotations

from dataclasses import dataclass, field
import time
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
    last_seen: float = field(default_factory=time.monotonic)
    processes: list[dict[str, str]] = field(
        default_factory=lambda: [
            {"pid": "101", "name": "nginx"},
            {"pid": "102", "name": "node"},
            {"pid": "103", "name": "postgres"},
        ]
    )


class SessionManager:
    def __init__(self, idle_ttl_seconds: int = 7200) -> None:
        self.sessions: dict[str, TerminalSession] = {}
        self.idle_ttl_seconds = idle_ttl_seconds

    def create(self, session_id: str | None = None) -> TerminalSession:
        session = TerminalSession(session_id=session_id) if session_id else TerminalSession()
        self.sessions[session.session_id] = session
        return session

    def get_or_create(self, session_id: str | None = None) -> TerminalSession:
        if session_id:
            session = self.get(session_id)
            if session is not None:
                self.touch(session)
                return session
            return self.create(session_id=session_id)
        return self.create()

    def get(self, session_id: str) -> TerminalSession | None:
        return self.sessions.get(session_id)

    def delete(self, session_id: str) -> None:
        self.sessions.pop(session_id, None)

    def touch(self, session: TerminalSession) -> None:
        session.last_seen = time.monotonic()

    def cleanup_idle(self) -> int:
        now = time.monotonic()
        expired = [
            session_id
            for session_id, session in self.sessions.items()
            if now - session.last_seen > self.idle_ttl_seconds
        ]
        for session_id in expired:
            self.delete(session_id)
        return len(expired)

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
