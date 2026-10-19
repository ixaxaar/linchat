"""Config v2: INI schema, v1 migration, env-based provider discovery."""
from __future__ import annotations

import configparser
import os

DEFAULT_DIR = os.path.expanduser("~/.config/linchat")
DEFAULT_PATH = os.path.join(DEFAULT_DIR, "config.ini")

ENV_PROVIDERS = [
    # (env var, name, type, base_url)
    ("OPENAI_API_KEY", "openai", "openai", "https://api.openai.com/v1"),
    ("ANTHROPIC_API_KEY", "anthropic", "anthropic", ""),
    ("GEMINI_API_KEY", "gemini", "gemini", ""),
    ("GOOGLE_API_KEY", "gemini", "gemini", ""),
    ("GROQ_API_KEY", "groq", "openai", "https://api.groq.com/openai/v1"),
    ("OPENROUTER_API_KEY", "openrouter", "openai", "https://openrouter.ai/api/v1"),
    ("XAI_API_KEY", "xai", "openai", "https://api.x.ai/v1"),
    ("DEEPSEEK_API_KEY", "deepseek", "openai", "https://api.deepseek.com/v1"),
    ("MISTRAL_API_KEY", "mistral", "openai", "https://api.mistral.ai/v1"),
]

DEFAULTS = {
    "General": {"default_provider": "", "max_tool_hops": "8", "request_timeout": "60"},
    "Tools": {"shell": "ask", "launch": "ask", "screenshot_cmd": "auto"},
    "Agents": {"disabled": ""},
}


class Config:
    def __init__(self, path: str, data: configparser.ConfigParser):
        self.path = path
        self.data = data

    def providers(self) -> dict[str, dict]:
        out = {}
        for section in self.data.sections():
            if section.startswith("provider:"):
                name = section.split(":", 1)[1]
                out[name] = dict(self.data[section])
        return out

    def env_discovered(self) -> list[dict]:
        env = self._env
        found = []
        for var, name, ptype, base_url in ENV_PROVIDERS:
            if env.get(var) and not any(p == name for p in self.providers()):
                found.append({"name": name, "type": ptype, "base_url": base_url,
                              "api_key": env[var], "model": ""})
        ollama_host = env.get("OLLAMA_HOST")
        if ollama_host and "ollama" not in self.providers():
            found.append({"name": "ollama", "type": "ollama",
                          "base_url": ollama_host, "api_key": "", "model": ""})
        return found

    def get(self, key: str, default: str = "") -> str:
        return self.data.get("General", key, fallback=default)

    def tools_policy(self, tool: str) -> str:
        val = self.data.get("Tools", tool, fallback="ask")
        return val if val in ("ask", "always", "never") else "ask"

    def agent_overrides(self) -> dict:
        section = {k: v for k, v in self.data["Agents"].items()} if self.data.has_section("Agents") else {}
        out = {"disabled": [s.strip() for s in section.pop("disabled", "").split(",") if s.strip()]}
        out.update(section)
        return out

    def set_default_provider(self, name: str) -> None:
        self.data["General"]["default_provider"] = name
        self.save()

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "w") as f:
            self.data.write(f)

    _env: dict = {}


def _migrate_v1(data: configparser.ConfigParser, path: str) -> None:
    if not data.has_section("API"):
        return
    backup = path + ".v1.bak"
    if os.path.exists(path) and not os.path.exists(backup):
        with open(path) as src, open(backup, "w") as dst:
            dst.write(src.read())
    api = data["API"]
    base_url = api.get("endpoint", "https://api.openai.com/v1/chat/completions").strip()
    if base_url.endswith("/chat/completions"):
        base_url = base_url[: -len("/chat/completions")]
    data["provider:openai"] = {
        "type": "openai",
        "api_key": api.get("api_key", "").strip(),
        "base_url": base_url,
        "model": api.get("model", "").strip(),
    }
    data.remove_section("API")


def load_config(path: str | None = None, env: dict | None = None) -> Config:
    path = path or DEFAULT_PATH
    data = configparser.ConfigParser()
    for section, values in DEFAULTS.items():
        data[section] = dict(values)
    if os.path.exists(path):
        data.read(path)
        _migrate_v1(data, path)
    cfg = Config(path, data)
    cfg._env = env if env is not None else dict(os.environ)
    if data.get("General", "default_provider", fallback="") == "":
        pass  # registry picks first discovered; written lazily on user choice
    return cfg
