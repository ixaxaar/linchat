import json
import pathlib

import requests

from linchat.providers import openai_compat
from linchat.providers.base import Done, Message, TextDelta, ToolCall, Usage


def collect(events):
    return list(events)


def test_messages_to_openai_plain_and_tool_roundtrip():
    msgs = [
        Message(role="user", content="hi"),
        Message(role="assistant", content="", tool_calls=[{"id": "c1", "name": "shell.run", "args": {"cmd": "ls"}}]),
        Message(role="tool", tool_call_id="c1", name="shell.run", content="file_a\nfile_b"),
        Message(role="user", content="thanks"),
    ]
    out = openai_compat.messages_to_openai(msgs)
    assert out[0] == {"role": "user", "content": "hi"}
    assert out[1]["tool_calls"] == [{
        "id": "c1", "type": "function",
        "function": {"name": "shell.run", "arguments": json.dumps({"cmd": "ls"})},
    }]
    assert out[2] == {"role": "tool", "tool_call_id": "c1", "content": "file_a\nfile_b"}
    assert out[3] == {"role": "user", "content": "thanks"}


def test_stream_emits_text_toolcall_usage_done(monkeypatch, fx):
    fixture = (fx / "sse_openai.txt").read_text().splitlines()
    sent = {}

    class FakeResp:
        status_code = 200

        def iter_lines(self, decode_unicode=True):
            return iter(fixture)

    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        sent["url"] = url
        sent["json"] = json
        return FakeResp()

    monkeypatch.setattr(requests, "post", fake_post)
    p = openai_compat.OpenAICompatProvider(name="openai", api_key="sk-test", model="gpt-5")
    events = collect(p.stream([Message(role="user", content="run ls")]))

    assert sent["url"] == "https://api.openai.com/v1/chat/completions"
    assert sent["json"]["stream"] is True
    assert sent["json"]["model"] == "gpt-5"
    assert isinstance(events[0], TextDelta) and events[0].text == "Hel"
    tc = [e for e in events if isinstance(e, ToolCall)][0]
    assert tc.id == "call_1" and tc.name == "shell.run" and tc.args == {"cmd": "ls -la"}
    usage = [e for e in events if isinstance(e, Usage)][0]
    assert usage.input_tokens == 10 and usage.output_tokens == 5
    done = [e for e in events if isinstance(e, Done)][0]
    assert done.reason == "tool_calls"


def test_stream_error_yields_errorevent(monkeypatch):
    class FakeResp:
        status_code = 401
        text = '{"error": "bad key"}'

        def iter_lines(self, decode_unicode=True):
            return iter([])

    def fake_post(*a, **k):
        return FakeResp()

    monkeypatch.setattr(requests, "post", fake_post)
    p = openai_compat.OpenAICompatProvider(name="openai", api_key="sk-leak-check", model="m")
    events = collect(p.stream([Message(role="user", content="x")]))
    assert isinstance(events[0], openai_compat.ErrorEvent)
    assert "401" in events[0].message and "sk-leak-check" not in events[0].message
