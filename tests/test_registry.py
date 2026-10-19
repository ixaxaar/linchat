from linchat.providers import registry
from linchat.providers.base import ErrorEvent, Message


class FakeConfig:
    def __init__(self, provs, env=None, agents_ov=None, default=""):
        self._provs = provs
        self._env = env or {}
        self._agents = agents_ov or {"disabled": []}
        self._default = default

    def providers(self):
        return self._provs

    def env_discovered(self):
        from linchat.config import ENV_PROVIDERS
        out = []
        for var, name, ptype, base_url in ENV_PROVIDERS:
            if var in self._env:
                out.append({"name": name, "type": ptype, "base_url": base_url,
                            "api_key": self._env[var], "model": ""})
        return out

    def get(self, key, default=""):
        return self._default if key == "default_provider" else default

    def agent_overrides(self):
        return self._agents


def test_config_and_env_providers_merge(monkeypatch):
    monkeypatch.setattr(registry, "_keyring_get", lambda name: None)
    monkeypatch.setattr("linchat.providers.registry.detect_agents", lambda ov, which=None: [])
    cfg = FakeConfig({"openai": {"type": "openai", "api_key": "cfg-key", "model": "gpt-5"}},
                     env={"ANTHROPIC_API_KEY": "ak"})
    reg = registry.Registry(cfg)
    names = [p.name for p in reg.providers()]
    assert names == ["openai", "anthropic"]


def test_missing_api_key_omits_provider(monkeypatch):
    monkeypatch.setattr(registry, "_keyring_get", lambda name: None)
    monkeypatch.setattr("linchat.providers.registry.detect_agents", lambda ov, which=None: [])
    cfg = FakeConfig({"openai": {"type": "openai", "api_key": ""}}, env={})
    reg = registry.Registry(cfg)
    assert [p.name for p in reg.providers()] == []


def test_keyring_fallback(monkeypatch):
    monkeypatch.setattr(registry, "_keyring_get", lambda name: "kr-key" if name == "openai" else None)
    monkeypatch.setattr("linchat.providers.registry.detect_agents", lambda ov, which=None: [])
    cfg = FakeConfig({"openai": {"type": "openai", "api_key": ""}}, env={})
    reg = registry.Registry(cfg)
    assert [p.name for p in reg.providers()] == ["openai"]


def test_env_key_fills_config_section_without_key(monkeypatch):
    monkeypatch.setattr(registry, "_keyring_get", lambda name: None)
    monkeypatch.setattr("linchat.providers.registry.detect_agents", lambda ov, which=None: [])
    cfg = FakeConfig({"groq": {"type": "openai", "model": "llama-3.3-70b-versatile"}},
                     env={"GROQ_API_KEY": "env-key"})
    reg = registry.Registry(cfg)
    provs = reg.providers()
    assert [p.name for p in provs] == ["groq"]        # config section, not env duplicate
    assert provs[0].api_key == "env-key"              # key resolved from env
    assert provs[0].model == "llama-3.3-70b-versatile"  # model from config section


def test_default_prefers_configured_then_hosted(monkeypatch):
    monkeypatch.setattr(registry, "_keyring_get", lambda name: None)
    monkeypatch.setattr("linchat.providers.registry.detect_agents", lambda ov, which=None: [])

    class FakeAgent:
        name = "opencode"

        def list_models(self):
            return []

    monkeypatch.setattr("linchat.providers.registry.detect_agents", lambda ov, which=None: [FakeAgent()])
    cfg = FakeConfig({}, env={"ANTHROPIC_API_KEY": "ak"})
    reg = registry.Registry(cfg)
    assert reg.default().name == "anthropic"

    reg2 = registry.Registry(FakeConfig({}, env={}, default="opencode"))
    assert reg2.default().name == "opencode"


def test_null_provider_when_empty(monkeypatch):
    monkeypatch.setattr(registry, "_keyring_get", lambda name: None)
    monkeypatch.setattr("linchat.providers.registry.detect_agents", lambda ov, which=None: [])
    reg = registry.Registry(FakeConfig({}, env={}))
    ev = list(reg.default().stream([Message(role="user", content="x")]))
    assert isinstance(ev[0], ErrorEvent)
