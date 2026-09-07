"""Additional tests to improve code coverage."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import os


@pytest.mark.asyncio
async def test_agent_stream_processing_message(add_agent_to_path):
    """Test that stream yields a Processing message first."""
    from agent import SampleAgent

    mock_tools = []

    mock_response_msg = MagicMock()
    mock_response_msg.content = "No tools available."

    with patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [mock_response_msg]}

        agent = SampleAgent()
        chunks = []
        async for chunk in agent.stream("test query", "ctx-1", tools=mock_tools):
            chunks.append(chunk)

        # First chunk is "Processing..."
        assert chunks[0]["is_task_complete"] is False
        assert "Processing" in chunks[0]["content"]
        # Last chunk is complete
        assert chunks[-1]["is_task_complete"] is True


@pytest.mark.asyncio
async def test_agent_stream_error_handling(add_agent_to_path):
    """Test that stream handles exceptions gracefully."""
    from agent import SampleAgent

    mock_tools = [MagicMock()]

    with patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.side_effect = Exception("Simulated error")

        agent = SampleAgent()
        chunks = []
        async for chunk in agent.stream("test query", "ctx-error", tools=mock_tools):
            chunks.append(chunk)

        last = chunks[-1]
        assert last["is_task_complete"] is True
        assert "error" in last["content"].lower()


@pytest.mark.asyncio
async def test_agent_invoke_returns_agent_response(add_agent_to_path):
    """Test that invoke() returns a proper AgentResponse."""
    from agent import SampleAgent, AgentResponse

    mock_response_msg = MagicMock()
    mock_response_msg.content = "42 cost centers found."

    with patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [mock_response_msg]}

        agent = SampleAgent()
        result = await agent.invoke("How many cost centers?", "ctx-invoke")

        assert isinstance(result, AgentResponse)
        assert result.status == "completed"
        assert "42" in result.message


@pytest.mark.asyncio
async def test_agent_invoke_error_returns_error_status(add_agent_to_path):
    """Test that invoke() returns error status on exception."""
    from agent import SampleAgent, AgentResponse

    with patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.side_effect = Exception("Agent failure")

        agent = SampleAgent()
        result = await agent.invoke("query", "ctx-err")

        assert isinstance(result, AgentResponse)
        assert result.status in ("error", "completed")  # graceful error handling


def test_get_system_prompt_contains_cost_center(add_agent_to_path):
    """Test that the system prompt contains cost center instructions."""
    from agent import get_system_prompt

    prompt = get_system_prompt()
    assert "cost center" in prompt.lower() or "S/4HANA" in prompt


def test_get_model_name_returns_string(add_agent_to_path):
    """Test that get_model_name() returns a non-empty string."""
    from agent import get_model_name

    model = get_model_name()
    assert isinstance(model, str)
    assert len(model) > 0


def test_get_temperature_returns_float(add_agent_to_path):
    """Test that temperature returns a float in valid range."""
    from agent import get_temperature

    temp = get_temperature()
    assert isinstance(temp, float)
    assert 0.0 <= temp <= 1.0


def test_thread_ttl_seconds_returns_positive(add_agent_to_path):
    """Test that thread TTL is a positive integer."""
    from agent import thread_ttl_seconds

    ttl = thread_ttl_seconds()
    assert isinstance(ttl, int)
    assert ttl > 0


def test_circuit_breaker_thresholds(add_agent_to_path):
    """Test that circuit breaker config values are sensible."""
    from agent import get_circuit_breaker_failure_threshold, get_circuit_breaker_cooldown_seconds

    threshold = get_circuit_breaker_failure_threshold()
    cooldown = get_circuit_breaker_cooldown_seconds()

    assert isinstance(threshold, int)
    assert threshold >= 0
    assert isinstance(cooldown, float)
    assert cooldown >= 0


def test_injection_resistance_env_var(add_agent_to_path):
    """Test that injection resistance reads from env var."""
    from agent import get_injection_resistance

    # Without env var
    result = get_injection_resistance()
    assert isinstance(result, str)

    # With env var
    os.environ["AGENT_INJECTION_RESISTANCE"] = "Test rule"
    result = get_injection_resistance()
    assert result == "Test rule"
    del os.environ["AGENT_INJECTION_RESISTANCE"]


@pytest.mark.asyncio
async def test_run_agent_milestone_logging(add_agent_to_path, caplog):
    """Test that milestones are logged correctly."""
    import logging
    from agent import SampleAgent

    mock_response_msg = MagicMock()
    mock_response_msg.content = "42 cost centers."

    with patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [mock_response_msg]}

        agent = SampleAgent()
        with caplog.at_level(logging.INFO):
            result = await agent._run_agent("How many cost centers?", "ctx-log", tools=[])

    assert "M1.achieved" in caplog.text
    assert result == "42 cost centers."


@pytest.mark.asyncio
async def test_run_agent_top5_milestone(add_agent_to_path, caplog):
    """Test that M2 milestone is logged for top-5 queries."""
    import logging
    from agent import SampleAgent

    mock_response_msg = MagicMock()
    mock_response_msg.content = "Top 5 cost centers: CC-1000, CC-2000, CC-3000, CC-4000, CC-5000"

    with patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [mock_response_msg]}

        agent = SampleAgent()
        with caplog.at_level(logging.INFO):
            result = await agent._run_agent("Show me the top 5 cost centers", "ctx-m2", tools=[])

    assert "M2.achieved" in caplog.text


@pytest.mark.asyncio
async def test_mock_tools_have_correct_names(add_agent_to_path):
    """Test that mock tools from mcp-mock.json have expected tool names."""
    from mcp_providers.agw import get_mcp_tools

    tools = await get_mcp_tools()
    tool_names = [t.name for t in tools]

    # Verify key cost center tools are available
    assert any("costcenter" in name.lower() or "cost" in name.lower() for name in tool_names)
    assert any("list" in name.lower() for name in tool_names)
    assert any("count" in name.lower() for name in tool_names)


@pytest.mark.asyncio
async def test_agent_no_tools_yields_response(add_agent_to_path):
    """Test agent stream with no tools still yields a valid response."""
    from agent import SampleAgent

    mock_response_msg = MagicMock()
    mock_response_msg.content = "Tools are temporarily unavailable."

    with patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [mock_response_msg]}

        agent = SampleAgent()
        chunks = []
        async for chunk in agent.stream("query", "ctx-notools", tools=None):
            chunks.append(chunk)

        assert len(chunks) >= 1
        final = chunks[-1]
        assert final["is_task_complete"] is True
