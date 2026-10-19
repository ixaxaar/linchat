"""Assemble the provider list: config sections, env discovery, agents."""
from __future__ import annotations

from typing import Iterator

from ..config import Config
from .agents import AgentDef, AgentProvider, detect_agents
from .anthropic import AnthropicProvider
from .base import ErrorEvent, Event, Message
from .gemini import GeminiProvider
from .ollama import OllamaProvider
from .openai_compat import OpenAICompatProvider


def _keyring_get(name: str) -> str | None:
    try:
        import keyring
        return keyring.get_password("linchat", name)
    except Exception:
        return None


class NullProvider:
    name = "none"

    def list_models(self) -> list[str]:
        return []

    def stream(self, messages, tools=None) -> Iterator[Event]:
        yield ErrorEvent("No providers configured — set an API key in "
                         "~/.config/linchat/config.ini or export e.g. OPENAI_API_KEY")


def _build_hosted(spec: dict, env_keys: dict[str, str], timeout: int) -> object | None:
    ptype = spec.get("type", "openai")
    key = spec.get("api_key", "") or env_keys.get(spec["name"], "") \
        or _keyring_get(spec["name"]) or ""
    base = spec.get("base_url", "")
    model = spec.get("model", "")
    if ptype == "anthropic":
        return AnthropicProvider(spec["name"], key, model, timeout) if key else None
    if ptype == "gemini":
        return GeminiProvider(spec["name"], key, model, timeout) if key else None
    if ptype == "ollama":
        return OllamaProvider(spec["name"], base or "http://localhost:11434", model, timeout)
    # openai / openai-compat
    if not key and "localhost" not in base and "127.0.0.1" not in base:
        return None  # remote endpoints need a key
    return OpenAICompatProvider(spec["name"], key, base or "https://api.openai.com/v1",
                                model, timeout)


class Registry:
    def __init__(self, config: Config):
        self.config = config
        self._providers: list | None = None

    def refresh(self) -> None:
        self._providers = None

    def providers(self) -> list:
        if self._providers is not None:
            return self._providers
        timeout = int(self.config.get("request_timeout", "60"))
        env_specs = self.config.env_discovered()
        env_keys = {s["name"]: s["api_key"] for s in env_specs}
        provs: list = []
        specs: list[dict] = []
        for name, section in self.config.providers().items():
            specs.append({"name": name, **section})
        have = {s["name"] for s in specs}
        for spec in env_specs:
            if spec["name"] not in have:
                specs.append(spec)
                have.add(spec["name"])
        for spec in specs:
            p = _build_hosted(spec, env_keys, timeout)
            if p is not None:
                provs.append(p)
        if "ollama" not in have:
            candidate = OllamaProvider("ollama", timeout=timeout)
            if candidate.available():
                provs.append(candidate)
        for d in detect_agents(self.config.agent_overrides()):
            provs.append(AgentProvider(d, timeout=600))
        self._providers = provs
        return provs

    def get(self, name: str):
        for p in self.providers():
            if p.name == name:
                return p
        return None

    def default(self):
        provs = self.providers()
        wanted = self.config.get("default_provider", "")
        if wanted:
            p = self.get(wanted)
            if p is not None:
                return p
        hosted = [p for p in provs if not isinstance(p, AgentProvider)]
        if hosted:
            return hosted[0]
        agents = [p for p in provs if isinstance(p, AgentProvider)]
        if agents:
            return agents[0]
        return NullProvider()
