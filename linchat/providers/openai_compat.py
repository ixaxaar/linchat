"""OpenAI-compatible chat-completions client (OpenAI, Groq, OpenRouter,
DeepSeek, Mistral, xAI, LM Studio, llama.cpp, vLLM, Ollama-compat, ...)."""
from __future__ import annotations

import json
from typing import Iterator

import requests

from .base import (
    Done, ErrorEvent, Event, Message, TextDelta, ToolCall, Usage, iter_sse,
)


def messages_to_openai(messages: list[Message]) -> list[dict]:
    out: list[dict] = []
    for m in messages:
        if m.role == "tool":
            out.append({"role": "tool", "tool_call_id": m.tool_call_id or "", "content": str(m.content)})
        elif m.role == "assistant" and m.tool_calls:
            out.append({
                "role": "assistant",
                "content": m.content or "",
                "tool_calls": [{
                    "id": tc["id"], "type": "function",
                    "function": {"name": tc["name"], "arguments": json.dumps(tc["args"])},
                } for tc in m.tool_calls],
            })
        else:
            msg: dict = {"role": m.role, "content": m.content}
            if m.images:
                parts = [{"type": "text", "text": str(m.content) or ""}]
                for png in m.images:
                    import base64
                    parts.append({"type": "image_url",
                                  "image_url": {"url": "data:image/png;base64," + base64.b64encode(png).decode()}})
                msg["content"] = parts
            out.append(msg)
    return out


class OpenAICompatProvider:
    def __init__(self, name: str, api_key: str = "",
                 base_url: str = "https://api.openai.com/v1",
                 model: str = "", timeout: int = 60):
        self.name = name
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def _headers(self) -> dict:
        h = {"Content-Type": "application/json"}
        if self.api_key:
            h["Authorization"] = f"Bearer {self.api_key}"
        return h

    def list_models(self) -> list[str]:
        try:
            r = requests.get(f"{self.base_url}/models", headers=self._headers(), timeout=self.timeout)
            r.raise_for_status()
            return sorted(m["id"] for m in r.json().get("data", []))
        except Exception:
            return []

    def stream(self, messages: list[Message], tools: list[dict] | None = None) -> Iterator[Event]:
        payload: dict = {
            "model": self.model,
            "messages": messages_to_openai(messages),
            "stream": True,
            "stream_options": {"include_usage": True},
        }
        if tools:
            payload["tools"] = tools
        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions", headers=self._headers(),
                json=payload, timeout=self.timeout, stream=True,
            )
        except requests.RequestException as e:
            yield ErrorEvent(f"Connection error: {e.__class__.__name__}")
            return
        if resp.status_code != 200:
            yield ErrorEvent(f"HTTP {resp.status_code}: {resp.text[:300]}")
            return

        tool_acc: dict[int, dict] = {}  # index -> {id, name, args_str}
        saw_tool_calls = False

        def flush_tool_calls() -> list[ToolCall]:
            nonlocal saw_tool_calls
            calls: list[ToolCall] = []
            for idx in sorted(tool_acc):
                acc = tool_acc[idx]
                try:
                    args = json.loads(acc["args"] or "{}")
                except json.JSONDecodeError:
                    args = {"_raw": acc["args"]}
                calls.append(ToolCall(acc["id"], acc["name"], args))
            if calls:
                saw_tool_calls = True
            tool_acc.clear()
            return calls

        try:
            for data in iter_sse(resp):
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                if chunk.get("usage"):
                    u = chunk["usage"]
                    yield Usage(u.get("prompt_tokens", 0), u.get("completion_tokens", 0))
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                ch = choices[0]
                delta = ch.get("delta") or {}
                if delta.get("content"):
                    yield TextDelta(delta["content"])
                for tc in delta.get("tool_calls") or []:
                    idx = tc.get("index", 0)
                    acc = tool_acc.setdefault(idx, {"id": "", "name": "", "args": ""})
                    fn = tc.get("function") or {}
                    if tc.get("id"):
                        acc["id"] = tc["id"]
                    if fn.get("name"):
                        acc["name"] = fn["name"]
                    if fn.get("arguments"):
                        acc["args"] += fn["arguments"]
                if ch.get("finish_reason") == "tool_calls":
                    yield from flush_tool_calls()
            # Compat servers (llama.cpp, LM Studio, vLLM) may end the stream
            # ([DONE] or finish_reason stop/null) without a tool_calls finish
            # chunk — flush anything accumulated so those calls don't vanish.
            yield from flush_tool_calls()
            yield Done("tool_calls" if saw_tool_calls else "stop")
        except requests.RequestException as e:
            yield ErrorEvent(f"Stream error: {e.__class__.__name__}")
