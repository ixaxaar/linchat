"""Google Gemini generateContent client (thin, requests-only)."""
from __future__ import annotations

import base64
import json
from typing import Iterator

import requests

from .base import (
    Done, ErrorEvent, Event, Message, TextDelta, ToolCall, Usage, iter_sse,
)

BASE = "https://generativelanguage.googleapis.com/v1beta"


def messages_to_gemini(messages: list[Message]) -> list[dict]:
    contents: list[dict] = []
    for m in messages:
        if m.role == "tool":
            part = {"functionResponse": {"name": m.name or m.tool_call_id or "tool",
                                         "response": {"result": str(m.content)}}}
            if contents and contents[-1]["role"] == "user" and \
                    contents[-1]["parts"] and "functionResponse" in contents[-1]["parts"][-1]:
                contents[-1]["parts"].append(part)
            else:
                contents.append({"role": "user", "parts": [part]})
        elif m.role == "assistant" and m.tool_calls:
            parts = []
            if m.content:
                parts.append({"text": str(m.content)})
            for i, tc in enumerate(m.tool_calls):
                parts.append({"functionCall": {"name": tc["name"], "args": tc["args"]}})
            contents.append({"role": "model", "parts": parts})
        else:
            role = "model" if m.role == "assistant" else "user"
            parts = [{"text": str(m.content) or ""}]
            for png in m.images or []:
                parts.append({"inlineData": {"mimeType": "image/png",
                                             "data": base64.b64encode(png).decode()}})
            contents.append({"role": role, "parts": parts})
    return contents


class GeminiProvider:
    def __init__(self, name: str, api_key: str, model: str = "", timeout: int = 60):
        self.name = name
        self.api_key = api_key
        self.model = model or "gemini-2.5-flash"
        self.timeout = timeout

    def list_models(self) -> list[str]:
        try:
            r = requests.get(f"{BASE}/models", params={"key": self.api_key}, timeout=self.timeout)
            r.raise_for_status()
            names = [m["name"].split("/")[-1] for m in r.json().get("models", [])
                     if "generateContent" in (m.get("supportedGenerationMethods") or [])]
            return sorted(names)
        except Exception:
            return []

    def stream(self, messages: list[Message], tools: list[dict] | None = None) -> Iterator[Event]:
        url = f"{BASE}/models/{self.model}:streamGenerateContent?alt=sse&key={self.api_key}"
        payload: dict = {"contents": messages_to_gemini(messages)}
        if tools:
            # Convert OpenAI-style tool specs to Gemini functionDeclarations.
            decls = []
            for t in tools:
                fn = t.get("function", t)
                decls.append({"name": fn["name"], "description": fn.get("description", ""),
                              "parameters": fn.get("parameters", {"type": "object", "properties": {}})})
            payload["tools"] = [{"functionDeclarations": decls}]
        try:
            resp = requests.post(url, json=payload, timeout=self.timeout, stream=True)
        except requests.RequestException as e:
            yield ErrorEvent(f"Connection error: {e.__class__.__name__}")
            return
        if resp.status_code != 200:
            yield ErrorEvent(f"HTTP {resp.status_code}: {resp.text[:300]}")
            return

        usage = Usage()
        saw_calls = False
        call_idx = 0
        try:
            for data in iter_sse(resp):
                try:
                    chunk = json.loads(data)
                except json.JSONDecodeError:
                    continue
                meta = chunk.get("usageMetadata") or {}
                if meta:
                    usage = Usage(meta.get("promptTokenCount", 0), meta.get("candidatesTokenCount", 0))
                for cand in chunk.get("candidates", []):
                    for part in (cand.get("content") or {}).get("parts", []):
                        if "text" in part:
                            yield TextDelta(part["text"])
                        if "functionCall" in part:
                            fc = part["functionCall"]
                            saw_calls = True
                            yield ToolCall(f"gcall_{call_idx}", fc["name"], fc.get("args") or {})
                            call_idx += 1
            yield usage
            yield Done("tool_calls" if saw_calls else "stop")
        except requests.RequestException as e:
            yield ErrorEvent(f"Stream error: {e.__class__.__name__}")
