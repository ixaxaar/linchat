"""Slash-command parsing and autocomplete (execution lives in the tools layer)."""
from __future__ import annotations

import dataclasses


@dataclasses.dataclass
class Command:
    name: str
    args: str    # usage hint shown in autocomplete
    description: str


COMMANDS: list[Command] = [
    Command("run", "cmd", "execute a shell command"),
    Command("open", "name", "launch an app"),
    Command("steam", "query", "search Steam library and store"),
    Command("games", "query", "search all game libraries"),
    Command("find", "pattern", "search files"),
    Command("read", "path", "read a file"),
    Command("clip", "", "read clipboard into context"),
    Command("snap", "", "capture a screen region for the next prompt"),
]

_NAMES = {c.name for c in COMMANDS}


def parse(text: str) -> tuple[str, str] | None:
    if not text.startswith("/"):
        return None
    body = text[1:]
    name, sep, argstr = body.partition(" ")
    if name not in _NAMES:
        return None
    if sep and not argstr.strip() and name != "clip":
        return (name, "")
    return (name, argstr)


def complete(prefix: str) -> list[Command]:
    p = prefix.lstrip("/")
    return [c for c in COMMANDS if c.name.startswith(p)]
