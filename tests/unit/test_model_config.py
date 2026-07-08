"""Unit tests for provider key resolution in model_config."""

from runtime.crewai import model_config
from runtime.crewai.model_config import (
    PROVIDER_ENV_KEYS,
    get_agent_model_info,
    get_provider_env_vars,
    resolve_api_key,
)


def test_resolve_api_key_reads_env(monkeypatch):
    monkeypatch.setenv("TOGETHER_API_KEY", "tok-123")
    assert resolve_api_key("together") == "tok-123"


def test_resolve_api_key_missing_is_none(monkeypatch):
    monkeypatch.delenv("CHUTES_API_KEY", raising=False)
    assert resolve_api_key("chutes") is None


def test_resolve_api_key_unknown_provider_is_none():
    assert resolve_api_key("does-not-exist") is None


def test_provider_env_keys_cover_every_agent_provider():
    # Every provider referenced by the matrix must have a known env var.
    for config in model_config.AGENT_MODELS.values():
        assert config["provider"] in PROVIDER_ENV_KEYS
        if config.get("fallback_provider"):
            assert config["fallback_provider"] in PROVIDER_ENV_KEYS


def test_get_provider_env_vars_matches_matrix():
    env_vars = get_provider_env_vars()
    # The current matrix uses these four providers (primary or fallback).
    assert set(env_vars) == {"anthropic", "chutes", "openai", "together"}
    assert env_vars["openai"] == "OPENAI_API_KEY"


def test_get_agent_model_info_known_and_unknown():
    info = get_agent_model_info("auditor_suite")
    assert info["provider"] == "openai"
    assert info["model"] == "gpt-4o-mini"

    unknown = get_agent_model_info("no_such_agent")
    assert unknown["provider"] == "unknown"
