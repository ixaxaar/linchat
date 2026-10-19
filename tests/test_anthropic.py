import requests

from linchat.providers import anthropic
from linchat.providers.base import Done, Message, TextDelta, ToolCall, Usage


def test_messages_to_anthropic_tool_roundtrip():
    msgs = [
        Message(role="user", content="run ls"),
        Message(role="assistant", content="", tool_calls=[{"id": "tu_1", "name": "shell.run", "args": {"cmd": "ls"}}]),
        Message(role="tool", tool_call_id="tu_1", name="shell.run", content="a\nb"),
    ]
    out = anthropic.messages_to_anthropic(msgs)
    assert out[0] == {"role": "user", "content": [{"type": "text", "text": "run ls"}]}
    assert out[1]["content"][0]["type"] == "tool_use"
    assert out[1]["content"][0]["input"] == {"cmd": "ls"}
    assert out[2]["role"] == "user"
    assert out[2]["content"] == [{"type": "tool_result", "tool_use_id": "tu_1", "content": "a\nb"}]


def test_stream_parses_blocks_and_tool_use(monkeypatch, fx):
    fixture = (fx / "sse_anthropic.txt").read_text().splitlines()
    sent = {}

    class FakeResp:
        status_code = 200

        def iter_lines(self, decode_unicode=True):
            return iter(fixture)

    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        sent["url"] = url
        sent["json"] = json
        sent["headers"] = headers
        return FakeResp()

    monkeypatch.setattr(requests, "post", fake_post)
    p = anthropic.AnthropicProvider(name="anthropic", api_key="sk-ant-test", model="claude-sonnet-4")
    events = list(p.stream([Message(role="user", content="run ls")]))

    assert sent["url"] == "https://api.anthropic.com/v1/messages"
    assert sent["headers"]["x-api-key"] == "sk-ant-test"
    assert sent["headers"]["anthropic-version"] == "2023-06-01"
    texts = [e.text for e in events if isinstance(e, TextDelta)]
    assert texts == ["Hi ", "there"]
    tc = [e for e in events if isinstance(e, ToolCall)][0]
    assert tc.id == "tu_1" and tc.name == "shell.run" and tc.args == {"cmd": "ls"}
    usage = [e for e in events if isinstance(e, Usage)][0]
    assert usage.input_tokens == 25 and usage.output_tokens == 7
    done = [e for e in events if isinstance(e, Done)][0]
    assert done.reason == "tool_calls"


def test_stream_http_error(monkeypatch):
    class FakeResp:
        status_code = 429
        text = "rate limited"

        def iter_lines(self, decode_unicode=True):
            return iter([])

    monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResp())
    p = anthropic.AnthropicProvider(name="anthropic", api_key="k", model="m")
    events = list(p.stream([Message(role="user", content="x")]))
    assert "429" in events[0].message
