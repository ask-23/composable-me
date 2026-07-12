"""Tests for the opt-in HYDRA_DIRECT_LLM seam in BaseHydraAgent.

These verify the *direct* path (bypassing CrewAI) assembles messages that carry the
same instruction content the CrewAI path relies on, and that the flag defaults OFF so
production behavior is unchanged. Byte-equivalence to CrewAI's own prompt assembly is
NOT asserted here — that needs a live-model capture (scripts/capture_crewai_transcript.py).
"""

import json
from unittest.mock import patch

import pytest

from runtime.crewai.base_agent import BaseHydraAgent


class _GapAgent(BaseHydraAgent):
    role = "Gap Analyzer"
    goal = "Map requirements to experience"
    expected_output = "JSON gap analysis"

    def execute(self, context):  # pragma: no cover - not used in these tests
        raise NotImplementedError


@pytest.fixture
def agent():
    # A real crewai LLM (crewai validates the `llm` field); no network call happens
    # because litellm.completion / Crew are patched in the tests below.
    from crewai import LLM

    return _GapAgent(LLM(model="gpt-4o-mini", api_key="test-key", temperature=0.3))


def _canned_response(role):
    payload = json.dumps({"agent": role, "timestamp": "t", "confidence": 0.9, "result": "ok"})
    return {"choices": [{"message": {"content": payload, "role": "assistant"}}]}


def test_direct_path_used_when_flag_set(agent, monkeypatch):
    monkeypatch.setenv("HYDRA_DIRECT_LLM", "1")
    captured = {}

    def fake_completion(**kwargs):
        captured.update(kwargs)
        return _canned_response(agent.role)

    with patch("litellm.completion", side_effect=fake_completion):
        task = agent.create_task("Analyze the gaps for this Senior Platform Engineer role.")
        out = agent.execute_with_retry(task, max_retries=0)

    assert out["result"] == "ok"
    # Model + credentials are taken from the CrewAI LLM object unchanged.
    assert captured["model"] == "gpt-4o-mini"
    assert captured["temperature"] == 0.3
    assert captured["api_key"] == "test-key"

    system, user = captured["messages"][0]["content"], captured["messages"][1]["content"]
    # System message carries role, goal, and the injected truth rules.
    assert "Gap Analyzer" in system
    assert "Map requirements to experience" in system
    assert "TRUTH RULES" in system or "fabricate" in system.lower()
    # User message carries the task, the JSON-only instruction, and the output contract.
    assert "Analyze the gaps" in user
    assert "valid JSON" in user
    assert "JSON gap analysis" in user


def test_default_off_uses_crew_not_direct(agent, monkeypatch):
    monkeypatch.delenv("HYDRA_DIRECT_LLM", raising=False)

    with (
        patch("runtime.crewai.base_agent.Crew") as mock_crew,
        patch.object(agent, "_execute_direct") as mock_direct,
    ):
        mock_crew.return_value.kickoff.return_value = _canned_response(agent.role)["choices"][0][
            "message"
        ]["content"]
        task = agent.create_task("desc")
        agent.execute_with_retry(task, max_retries=0)

    mock_direct.assert_not_called()
    mock_crew.return_value.kickoff.assert_called_once()


def test_build_messages_shape(agent):
    task = agent.create_task("Do the thing.")
    messages = agent._build_messages(task)
    assert [m["role"] for m in messages] == ["system", "user"]
    assert messages[0]["content"].startswith("You are Gap Analyzer.")
