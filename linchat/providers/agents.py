"""CLI agents (opencode, claude-code, codex, gemini, pi, crush) as providers.

Headless invocations verified on 2026-10-19:
  opencode run <msg> | claude -p <msg> --output-format stream-json |
  codex exec <prompt> | gemini -p <prompt> | crush run <prompt...>
`pi` detection uses a --help marker because /usr/bin/pi may be GNU pi
(the constant calculator).
"""
from __future__ import annotations

import dataclasses
import json
import shlex
import subprocess
import threading
from typing import Iterator

from .base import Done, ErrorEvent, Event, Message, TextDelta


@dataclasses.dataclass
class AgentDef:
    name: str
    binary: str
    args: list[str]
    parser: str = "plain"       # plain | claude-json
    help_marker: str = ""       # required substring of `<binary> --help`


AGENTS: list[AgentDef] = [
    AgentDef("opencode", "opencode", ["run", "{prompt}"]),
    AgentDef("claude-code", "claude", ["-p", "{prompt}", "--output-format", "stream-json"],
             parser="claude-json"),
    AgentDef("codex", "codex", ["exec", "{prompt}"]),
    AgentDef("gemini", "gemini", ["-p", "{prompt}"]),
    AgentDef("pi", "pi", ["{prompt}"], help_marker="agent"),
    AgentDef("crush", "crush", ["run", "{prompt}"]),
]


def _run_help(binary: str) -> str:
    try:
        return subprocess.run([binary, "--help"], capture_output=True, text=True,
                              timeout=15).stdout
    except Exception:
        return ""


def detect_agents(overrides: dict | None = None, which=None) -> list[AgentDef]:
    import shutil
    which = which or shutil.which
    ov = overrides or {}
    disabled = ov.get("disabled", [])
    found = []
    for d in AGENTS:
        if d.name in disabled:
            continue
        binary = ov.get(f"{d.name}_bin", d.binary)
        path = which(binary)
        if not path:
            continue
        if d.help_marker and d.help_marker not in _run_help(path):
            continue
        args = shlex.split(ov[f"{d.name}_args"]) if f"{d.name}_args" in ov else d.args
        found.append(dataclasses.replace(d, binary=path, args=args))
    return found


class AgentProvider:
    def __init__(self, defn: AgentDef, timeout: int = 600):
        self.name = defn.name
        self.defn = defn
        self.timeout = timeout

    def list_models(self) -> list[str]:
        return []

    def stream(self, messages: list[Message], tools: list[dict] | None = None) -> Iterator[Event]:
        prompt = "\n".join(str(m.content) for m in messages if m.role == "user")
        cmd = [self.defn.binary] + [a.replace("{prompt}", prompt) for a in self.defn.args]
        try:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                    text=True, start_new_session=True)
        except OSError as e:
            yield ErrorEvent(f"Failed to start {self.defn.name}: {e}")
            return
        # Drain stderr concurrently: a child writing >64KB to stderr with a
        # quiet stdout would otherwise block the pipe buffer and deadlock the
        # stdout read loop below forever.
        err_chunks: list[str] = []

        def _drain_stderr() -> None:
            if proc.stderr is not None:
                err_chunks.append(proc.stderr.read())

        stderr_thread = threading.Thread(target=_drain_stderr, daemon=True)
        stderr_thread.start()
        try:
            for line in proc.stdout:
                if self.defn.parser == "claude-json":
                    yield from self._claude_line(line)
                elif line.strip():
                    yield TextDelta(line)
            proc.wait(timeout=self.timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            yield ErrorEvent(f"{self.defn.name}: timed out after {self.timeout}s")
            return
        finally:
            # Reap/kill the child even if the consumer abandons the generator
            # (GeneratorExit/exception) so it can't run detached forever.
            if proc.poll() is None:
                try:
                    proc.kill()
                except ProcessLookupError:
                    pass
            proc.wait()
            stderr_thread.join(timeout=5)
            for pipe in (proc.stdout, proc.stderr):
                if pipe is not None:
                    try:
                        pipe.close()
                    except OSError:
                        pass
        stderr = "".join(err_chunks)
        if proc.returncode != 0:
            yield ErrorEvent(f"{self.defn.name} (exit {proc.returncode}): "
                             f"{shlex.join(cmd)}\n{stderr.strip()[-500:]}")
            return
        yield Done("stop")

    def _claude_line(self, line: str) -> Iterator[Event]:
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            return
        if ev.get("type") == "assistant":
            for block in ev.get("message", {}).get("content", []):
                if block.get("type") == "text" and block.get("text"):
                    yield TextDelta(block["text"])
