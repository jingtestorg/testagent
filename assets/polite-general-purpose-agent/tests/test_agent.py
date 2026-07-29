"""Unit and integration tests for the polite-general-purpose agent."""
import sys
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Ensure app/ is on sys.path for peer-level imports
_app_dir = str(Path(__file__).parent.parent / "app")
if _app_dir not in sys.path:
    sys.path.insert(0, _app_dir)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

POLITE_PREFIX = "Dear user, I am sorry, but "


def make_mock_llm_result(content: str):
    """Build a fake graph ainvoke result with the given content."""
    mock_message = MagicMock()
    mock_message.content = content
    return {"messages": [mock_message]}


# ---------------------------------------------------------------------------
# Test: prefix enforcement safeguard
# ---------------------------------------------------------------------------


class TestPrefixEnforcement:
    """Unit tests for the mandatory polite prefix safeguard."""

    @pytest.mark.asyncio
    async def test_prefix_prepended_when_missing(self):
        """When the LLM returns a response WITHOUT the prefix, it must be prepended."""
        from agent import SampleAgent

        agent = SampleAgent()
        llm_response_without_prefix = "The capital of France is Paris."

        with patch("agent.create_agent") as mock_create_agent:
            mock_graph = AsyncMock()
            mock_graph.ainvoke.return_value = make_mock_llm_result(
                llm_response_without_prefix
            )
            mock_create_agent.return_value = mock_graph

            response = await agent._run_agent("What is the capital of France?", "ctx-1")

        assert response.startswith(POLITE_PREFIX), (
            f"Expected response to start with '{POLITE_PREFIX}', got: {response[:80]}"
        )
        assert "Paris" in response

    @pytest.mark.asyncio
    async def test_prefix_not_duplicated_when_present(self):
        """When the LLM already includes the prefix, it must NOT be added again."""
        from agent import SampleAgent

        agent = SampleAgent()
        llm_response_with_prefix = POLITE_PREFIX + "the capital of France is Paris."

        with patch("agent.create_agent") as mock_create_agent:
            mock_graph = AsyncMock()
            mock_graph.ainvoke.return_value = make_mock_llm_result(
                llm_response_with_prefix
            )
            mock_create_agent.return_value = mock_graph

            response = await agent._run_agent("What is the capital of France?", "ctx-2")

        assert response.count(POLITE_PREFIX) == 1, (
            "Prefix should appear exactly once, not be duplicated."
        )


# ---------------------------------------------------------------------------
# Test: milestone logging
# ---------------------------------------------------------------------------


class TestMilestoneLogging:
    """Verify that milestone log statements are emitted during a successful run."""

    @pytest.mark.asyncio
    async def test_all_milestones_logged_on_success(self, caplog):
        """M1–M5 achieved messages must appear in the logs for a normal run."""
        import logging
        from agent import SampleAgent

        agent = SampleAgent()
        with patch("agent.create_agent") as mock_create_agent:
            mock_graph = AsyncMock()
            mock_graph.ainvoke.return_value = make_mock_llm_result(
                POLITE_PREFIX + "here is your answer."
            )
            mock_create_agent.return_value = mock_graph

            with caplog.at_level(logging.INFO, logger="agent"):
                # Consume the full stream
                async for _ in agent.stream("Tell me something", "ctx-milestones"):
                    pass

        log_text = caplog.text
        assert "M1.achieved" in log_text, "M1.achieved not found in logs"
        assert "M2.achieved" in log_text, "M2.achieved not found in logs"
        assert "M3.achieved" in log_text, "M3.achieved not found in logs"
        assert "M4.achieved" in log_text, "M4.achieved not found in logs"
        assert "M5.achieved" in log_text, "M5.achieved not found in logs"

    @pytest.mark.asyncio
    async def test_m1_missed_logged_for_empty_input(self, caplog):
        """M1.missed must be logged when query is empty."""
        import logging
        from agent import SampleAgent

        agent = SampleAgent()
        with caplog.at_level(logging.INFO, logger="agent"):
            response = await agent._run_agent("", "ctx-empty")

        assert "M1.missed" in caplog.text
        assert response.startswith(POLITE_PREFIX)


# ---------------------------------------------------------------------------
# Integration test
# ---------------------------------------------------------------------------


class TestIntegration:
    """End-to-end agent flow with mocked LLM."""

    @pytest.mark.asyncio
    async def test_full_stream_returns_polite_response(self):
        """Full stream from input → output must include the polite prefix."""
        from agent import SampleAgent

        agent = SampleAgent()
        with patch("agent.create_agent") as mock_create_agent:
            mock_graph = AsyncMock()
            mock_graph.ainvoke.return_value = make_mock_llm_result(
                POLITE_PREFIX + "I can help you with that."
            )
            mock_create_agent.return_value = mock_graph

            final_response = None
            async for chunk in agent.stream("Help me with something", "ctx-integration"):
                if chunk["is_task_complete"]:
                    final_response = chunk["content"]

        assert final_response is not None, "No final response received from stream"
        assert final_response.startswith(POLITE_PREFIX), (
            f"Final response does not start with polite prefix: {final_response[:100]}"
        )
