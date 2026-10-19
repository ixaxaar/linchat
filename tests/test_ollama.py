import requests

from linchat.providers import ollama
from linchat.providers.base import Done, Message, TextDelta, ToolCall, Usage


def test_messages_to_ollama_tool_roundtrip():
    msgs = [
        Message(role="user", content="run ls"),
        Message(role="assistant", content="", tool_calls=[{"id": "o1", "name": "shell.run", "args": {"cmd": "ls"}}]),
        Message(role="tool", tool_call_id="o1", name="shell.run", content="a\nb"),
    ]
    out = ollama.messages_to_ollama(msgs)
    assert out[0] == {"role": "user", "content": "run ls"}
    assert out[1]["tool_calls"] == [{"function": {"name": "shell.run", "arguments": {"cmd": "ls"}}}]
    assert out[2] == {"role": "tool", "content": "a\nb"}


def test_stream_parses_ndjson(monkeypatch):
    ndjson = [
        '{"model":"llama3.2","message":{"role":"assistant","content":"Hi"},"done":false}',
        '{"model":"llama3.2","message":{"role":"assistant","content":"","tool_calls":[{"function":{"name":"shell.run","arguments":{"cmd":"ls"}}}]},"done":false}',
        '{"model":"llama3.2","message":{"role":"assistant","content":""},"done":true,'
        '"prompt_eval_count":12,"eval_count":6}',
    ]
    sent = {}

    class FakeResp:
        status_code = 200

        def iter_lines(self, decode_unicode=True):
            return iter(ndjson)

    def fake_post(url, headers=None, json=None, timeout=None, stream=None):
        sent["url"] = url
        sent["json"] = json
        return FakeResp()

    monkeypatch.setattr(requests, "post", fake_post)
    p = ollama.OllamaProvider(model="llama3.2")
    events = list(p.stream([Message(role="user", content="hi")]))

    assert sent["url"] == "http://localhost:11434/api/chat"
    assert sent["json"] == {"model": "llama3.2", "stream": True,
                            "messages": [{"role": "user", "content": "hi"}]}
    assert isinstance(events[0], TextDelta) and events[0].text == "Hi"
    tc = [e for e in events if isinstance(e, ToolCall)][0]
    assert tc.name == "shell.run" and tc.args == {"cmd": "ls"}
    usage = [e for e in events if isinstance(e, Usage)][0]
    assert usage.input_tokens == 12 and usage.output_tokens == 6
    assert [e for e in events if isinstance(e, Done)][0].reason == "tool_calls"


def test_unreachable(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("refused")

    monkeypatch.setattr(requests, "post", boom)
    p = ollama.OllamaProvider(model="m")
    events = list(p.stream([Message(role="user", content="x")]))
    assert "Connection" in events[0].message
