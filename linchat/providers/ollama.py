"""Ollama native /api/chat client (NDJSON streaming)."""
from __future__ import annotations

import json
from typing import Iterator

import requests

from .base import Done, ErrorEvent, Event, Message, TextDelta, ToolCall, Usage


def messages_to_ollama(messages: list[Message]) -> list[dict]:
    out: list[dict] = []
    for m in messages:
        if m.role == "tool":
            out.append({"role": "tool", "content": str(m.content)})
        elif m.role == "assistant" and m.tool_calls:
            msg: dict = {"role": "assistant", "content": str(m.content or ""),
                         "tool_calls": [{"function": {"name": tc["name"], "arguments": tc["args"]}}
                                        for tc in m.tool_calls]}
            out.append(msg)
        else:
            msg = {"role": m.role, "content": m.content}
            if m.images:
                import base64
                msg["images"] = [base64.b64encode(png).decode() for png in m.images]
            out.append(msg)
    return out


class OllamaProvider:
    def __init__(self, name: str = "ollama", base_url: str = "http://localhost:11434",
                 model: str = "", timeout: int = 120):
        self.name = name
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def available(self) -> bool:
        try:
            return requests.get(f"{self.base_url}/api/version", timeout=2).ok
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=self.timeout)
            r.raise_for_status()
            return sorted(m["name"] for m in r.json().get("models", []))
        except Exception:
            return []

    def stream(self, messages: list[Message], tools: list[dict] | None = None) -> Iterator[Event]:
        payload: dict = {"model": self.model, "stream": True,
                         "messages": messages_to_ollama(messages)}
        if tools:
            payload["tools"] = tools
        try:
            resp = requests.post(f"{self.base_url}/api/chat", json=payload,
                                 timeout=self.timeout, stream=True)
        except requests.RequestException as e:
            yield ErrorEvent(f"Connection error ({self.base_url}): {e.__class__.__name__}")
            return
        if resp.status_code != 200:
            yield ErrorEvent(f"HTTP {resp.status_code}: {resp.text[:300]}")
            return
        saw_calls = False
        call_n = 0
        try:
            for line in resp.iter_lines(decode_unicode=True):
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg = chunk.get("message") or {}
                if msg.get("content"):
                    yield TextDelta(msg["content"])
                for tc in msg.get("tool_calls") or []:
                    fn = tc.get("function") or {}
                    saw_calls = True
                    yield ToolCall(f"ocall_{call_n}", fn.get("name", ""), fn.get("arguments") or {})
                    call_n += 1
                if chunk.get("done"):
                    yield Usage(chunk.get("prompt_eval_count", 0), chunk.get("eval_count", 0))
                    break
            yield Done("tool_calls" if saw_calls else "stop")
        except requests.RequestException as e:
            yield ErrorEvent(f"Stream error: {e.__class__.__name__}")
