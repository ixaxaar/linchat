import configparser

from linchat import config as cfg


def write(tmp_path, text):
    p = tmp_path / "config.ini"
    p.write_text(text)
    return str(p)


def test_creates_default_when_missing(tmp_path):
    c = cfg.load_config(str(tmp_path / "config.ini"), env={})
    assert c.data["Tools"]["shell"] == "ask"
    assert c.data["Tools"]["launch"] == "ask"
    assert c.data["General"]["max_tool_hops"] == "8"


def test_migrates_v1_api_section(tmp_path):
    path = write(tmp_path, (
        "[API]\n"
        "endpoint = https://api.openai.com/v1/chat/completions\n"
        "api_key = sk-old\n"
        "model = gpt-4o\n\n"
        "[Colors]\nbackground = #1e1e1e\n"
    ))
    c = cfg.load_config(path, env={})
    provs = c.providers()
    assert provs["openai"]["api_key"] == "sk-old"
    assert provs["openai"]["base_url"] == "https://api.openai.com/v1"
    assert provs["openai"]["model"] == "gpt-4o"
    assert (tmp_path / "config.ini.v1.bak").exists()
    assert c.data["Colors"]["background"] == "#1e1e1e"


def test_migrate_strips_compat_suffix_from_custom_endpoints(tmp_path):
    path = write(tmp_path, "[API]\nendpoint = https://x/v1/chat/completions\n")
    c = cfg.load_config(path, env={})
    assert c.providers()["openai"]["base_url"] == "https://x/v1"


def test_env_discovery(tmp_path):
    c = cfg.load_config(str(tmp_path / "config.ini"), env={
        "ANTHROPIC_API_KEY": "ak", "GROQ_API_KEY": "gk", "OPENAI_API_KEY": "ok",
    })
    found = {p["name"]: p for p in c.env_discovered()}
    assert found["anthropic"]["api_key"] == "ak"
    assert found["groq"]["base_url"] == "https://api.groq.com/openai/v1"
    assert found["openai"]["type"] == "openai"


def test_config_section_overrides_env(tmp_path):
    path = write(tmp_path, "[provider:groq]\ntype = openai\nmodel = llama-3.3-70b-versatile\n")
    c = cfg.load_config(path, env={"GROQ_API_KEY": "gk"})
    provs = c.providers()
    assert provs["groq"]["model"] == "llama-3.3-70b-versatile"


def test_tools_policy_and_agent_overrides(tmp_path):
    path = write(tmp_path, (
        "[Tools]\nshell = always\n\n"
        "[Agents]\ndisabled = crush, pi\ncodex_args = exec --full-auto\n"
    ))
    c = cfg.load_config(path, env={})
    assert c.tools_policy("shell") == "always"
    assert c.tools_policy("launch") == "ask"
    ov = c.agent_overrides()
    assert ov["disabled"] == ["crush", "pi"]
    assert ov["codex_args"] == "exec --full-auto"
