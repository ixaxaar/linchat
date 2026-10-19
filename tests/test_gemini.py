import requests

from linchat.providers import gemini
from linchat.providers.base import Done, Message, TextDelta, ToolCall, Usage


def test_messages_to_gemini_tool_roundtrip():
    msgs = [
        Message(role="user", content="run ls"),
        Message(role="assistant", content="", tool_calls=[{"id": "g1", "name": "shell.run", "args": {"cmd": "ls"}}]),
        Message(role="tool", tool_call_id="g1", name="shell.run", content="a\nb"),
    ]
    out = gemini.messages_to_gemini(msgs)
    assert out[0] == {"role": "user", "parts": [{"text": "run ls"}]}
    assert out[1]["parts"][0]["functionCall"] == {"name": "shell.run", "args": {"cmd": "ls"}}
    assert out[2]["role"] == "user"
    assert out[2]["parts"][0]["functionResponse"]["name"] == "shell.run"
    assert out[2]["parts"][0]["functionResponse"]["response"]["result"] == "a\nb"


def test_stream_parses_text_and_function_call(monkeypatch, fx):
    fixture = (fx / "sse_gemini.txt").read_text().splitlines()
    sent = {}

    class FakeResp:
        status_code = 200  # brief defect fix: success-path fake must declare 200

        def iter_lines(self, decode_unicode=True):
            return iter(fixture)

    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        sent["url"] = url
        sent["json"] = json
        return FakeResp()

    monkeypatch.setattr(requests, "post", fake_post)
    p = gemini.GeminiProvider(name="gemini", api_key="g-key", model="gemini-2.5-flash")
    events = list(p.stream([Message(role="user", content="hi")]))

    assert "streamGenerateContent" in sent["url"] and "alt=sse" in sent["url"]
    assert sent["json"] == {"contents": [{"role": "user", "parts": [{"text": "hi"}]}]}
    assert isinstance(events[0], TextDelta) and events[0].text == "Hello"
    tc = [e for e in events if isinstance(e, ToolCall)][0]
    assert tc.name == "shell.run" and tc.args == {"cmd": "ls"} and tc.id
    usage = [e for e in events if isinstance(e, Usage)][0]
    assert usage.input_tokens == 9 and usage.output_tokens == 4
    assert [e for e in events if isinstance(e, Done)][0].reason == "tool_calls"


def test_stream_http_error(monkeypatch):
    class FakeResp:
        status_code = 400
        text = "bad"

        def iter_lines(self, decode_unicode=True):
            return iter([])

    monkeypatch.setattr(requests, "post", lambda *a, **k: FakeResp())
    p = gemini.GeminiProvider(name="gemini", api_key="k", model="m")
    events = list(p.stream([Message(role="user", content="x")]))
    assert "400" in events[0].message
