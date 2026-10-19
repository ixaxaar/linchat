import os
import stat

from linchat.providers import agents
from linchat.providers.base import Done, ErrorEvent, Message, TextDelta


def make_fake_agent(tmp_path, name, stdout_lines, exit_code=0):
    import shlex
    d = tmp_path / name
    d.mkdir(parents=True, exist_ok=True)
    script = d / name
    body = "#!/bin/sh\n" + "".join(f"printf '%s\\n' {shlex.quote(l)}\n" for l in stdout_lines)
    if exit_code:
        body += f"printf '%s\\n' 'boom' >&2\nexit {exit_code}\n"
    script.write_text(body)
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return str(script)


def fake_which(bins):
    def which(b):
        return bins.get(b)
    return which


def test_detect_filters_and_uses_help_marker(tmp_path, monkeypatch):
    opencode = make_fake_agent(tmp_path, "opencode", [])
    pi_agent = make_fake_agent(tmp_path, "pi", [])
    monkeypatch.setattr(agents, "_run_help", lambda binary: "pi - your coding agent" if binary == pi_agent else "")
    found = agents.detect_agents({}, which=fake_which({"opencode": opencode, "pi": pi_agent, "crush": None}))
    names = [a.name for a in found]
    assert names == ["opencode", "pi"]


def test_overrides_disable_and_args(tmp_path, monkeypatch):
    codex = make_fake_agent(tmp_path, "codex", [])
    monkeypatch.setattr(agents, "_run_help", lambda b: "")
    found = agents.detect_agents(
        {"disabled": ["codex"], "codex_args": "exec --full-auto {prompt}"},
        which=fake_which({"codex": codex}),
    )
    assert found == []


def test_plain_parser_streams_lines(tmp_path, monkeypatch):
    binpath = make_fake_agent(tmp_path, "opencode", ["part one", "part two"])
    monkeypatch.setattr(agents, "_run_help", lambda b: "")
    d = agents.AgentDef(name="opencode", binary=binpath, args=["run", "{prompt}"], parser="plain")
    p = agents.AgentProvider(d)
    events = list(p.stream([Message(role="user", content="hello")]))
    texts = [e.text for e in events if isinstance(e, TextDelta)]
    assert texts == ["part one\n", "part two\n"]
    assert isinstance(events[-1], Done) and events[-1].reason == "stop"


def test_claude_json_parser_extracts_text(tmp_path, monkeypatch):
    import json as j
    lines = [
        j.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "Hi "}]}}),
        j.dumps({"type": "assistant", "message": {"content": [{"type": "text", "text": "there"}]}}),
        j.dumps({"type": "result", "result": "done"}),
    ]
    binpath = make_fake_agent(tmp_path, "claude", lines)
    monkeypatch.setattr(agents, "_run_help", lambda b: "")
    d = agents.AgentDef(name="claude-code", binary=binpath, args=["-p", "{prompt}"], parser="claude-json")
    p = agents.AgentProvider(d)
    events = list(p.stream([Message(role="user", content="hello")]))
    texts = [e.text for e in events if isinstance(e, TextDelta)]
    assert texts == ["Hi ", "there"]
    assert isinstance(events[-1], Done)


def test_failure_yields_error_with_invocation(tmp_path, monkeypatch):
    binpath = make_fake_agent(tmp_path, "codex", [], exit_code=3)
    monkeypatch.setattr(agents, "_run_help", lambda b: "")
    d = agents.AgentDef(name="codex", binary=binpath, args=["exec", "{prompt}"], parser="plain")
    p = agents.AgentProvider(d)
    events = list(p.stream([Message(role="user", content="hi")]))
    err = [e for e in events if isinstance(e, ErrorEvent)][0]
    assert "exit 3" in err.message and "boom" in err.message
    assert "exec" in err.message
