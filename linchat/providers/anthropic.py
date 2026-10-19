"""Anthropic Messages API client (thin, requests-only)."""
from __future__ import annotations

import base64
import json
from typing import Iterator

import requests

from .base import (
    Done, ErrorEvent, Event, Message, TextDelta, ToolCall, Usage, iter_sse,
)

API_URL = "https://api.anthropic.com/v1"
VERSION = "2023-06-01"


def messages_to_anthropic(messages: list[Message]) -> list[dict]:
    out: list[dict] = []
    for m in messages:
        if m.role == "tool":
            block = {"type": "tool_result", "tool_use_id": m.tool_call_id or "", "content": str(m.content)}
            if out and out[-1]["role"] == "user" and isinstance(out[-1]["content"], list) \
                    and out[-1]["content"] and out[-1]["content"][-1]["type"] == "tool_result":
                out[-1]["content"].append(block)
            else:
                out.append({"role": "user", "content": [block]})
        elif m.role == "assistant" and m.tool_calls:
            blocks = []
            if m.content:
                blocks.append({"type": "text", "text": str(m.content)})
            for tc in m.tool_calls:
                blocks.append({"type": "tool_use", "id": tc["id"], "name": tc["name"], "input": tc["args"]})
            out.append({"role": "assistant", "content": blocks})
        else:
            blocks = [{"type": "text", "text": str(m.content) or ""}]
            for png in m.images or []:
                blocks.append({"type": "image", "source": {
                    "type": "base64", "media_type": "image/png",
                    "data": base64.b64encode(png).decode()}})
            out.append({"role": "user", "content": blocks})
    return out


class AnthropicProvider:
    def __init__(self, name: str, api_key: str, model: str = "", timeout: int = 60):
        self.name = name
        self.api_key = api_key
        self.model = model or "claude-sonnet-4"
        self.timeout = timeout

    def _post(self, payload: dict) -> requests.Response:
        return requests.post(
            f"{API_URL}/messages",
            headers={"x-api-key": self.api_key, "anthropic-version": VERSION,
                     "Content-Type": "application/json"},
            json=payload, timeout=self.timeout, stream=True,
        )

    def list_models(self) -> list[str]:
        try:
            r = requests.get(f"{API_URL}/models",
                             headers={"x-api-key": self.api_key, "anthropic-version": VERSION},
                             timeout=self.timeout)
            r.raise_for_status()
            return sorted(m["id"] for m in r.json().get("data", []))
        except Exception:
            return []

    def stream(self, messages: list[Message], tools: list[dict] | None = None) -> Iterator[Event]:
        payload: dict = {"model": self.model, "max_tokens": 8192, "stream": True,
                         "messages": messages_to_anthropic(messages)}
        if tools:
            payload["tools"] = tools
        try:
            resp = self._post(payload)
        except requests.RequestException as e:
            yield ErrorEvent(f"Connection error: {e.__class__.__name__}")
            return
        if resp.status_code != 200:
            yield ErrorEvent(f"HTTP {resp.status_code}: {resp.text[:300]}")
            return

        # index -> {type, id, name, args_json}
        blocks: dict[int, dict] = {}
        usage = Usage()
        stop_reason = "stop"
        try:
            for data in iter_sse(resp):
                try:
                    ev = json.loads(data)
                except json.JSONDecodeError:
                    continue
                et = ev.get("type")
                if et == "message_start":
                    usage.input_tokens = ev["message"].get("usage", {}).get("input_tokens", 0)
                elif et == "content_block_start":
                    cb = ev["content_block"]
                    if cb["type"] == "tool_use":
                        blocks[ev["index"]] = {"type": "tool_use", "id": cb["id"], "name": cb["name"], "json": ""}
                elif et == "content_block_delta":
                    d = ev["delta"]
                    if d["type"] == "text_delta":
                        yield TextDelta(d["text"])
                    elif d["type"] == "input_json_delta" and ev["index"] in blocks:
                        blocks[ev["index"]]["json"] += d.get("partial_json", "")
                elif et == "message_delta":
                    stop_reason = ev.get("delta", {}).get("stop_reason") or stop_reason
                    usage.output_tokens = ev.get("usage", {}).get("output_tokens", usage.output_tokens)
                elif et == "message_stop":
                    break
            yield usage
            for b in blocks.values():
                try:
                    args = json.loads(b["json"] or "{}")
                except json.JSONDecodeError:
                    args = {"_raw": b["json"]}
                yield ToolCall(b["id"], b["name"], args)
            yield Done("tool_calls" if blocks else "stop")
        except requests.RequestException as e:
            yield ErrorEvent(f"Stream error: {e.__class__.__name__}")
