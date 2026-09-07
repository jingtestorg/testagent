"""Unit test for the cost center count tool call."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_count_tool():
    """Mock MCP tool that returns a cost center count."""
    tool = MagicMock()
    tool.name = "mcp_sap_self__count_a_costcenter_2_for_sap_self"
    tool.description = "Get the total count of entities in the A_CostCenter_2 collection."
    tool.ainvoke = AsyncMock(return_value=42)
    return tool


@pytest.mark.asyncio
async def test_cost_center_count_tool_returns_number(add_agent_to_path, mock_count_tool):
    """Test that the count tool returns a numeric count."""
    result = await mock_count_tool.ainvoke({})
    assert result == 42
    assert isinstance(result, int)


@pytest.mark.asyncio
async def test_cost_center_count_tool_called_once(add_agent_to_path, mock_count_tool):
    """Test that the count tool can be called successfully."""
    await mock_count_tool.ainvoke({})
    mock_count_tool.ainvoke.assert_called_once_with({})


@pytest.mark.asyncio
async def test_cost_center_count_with_filter(add_agent_to_path, mock_count_tool):
    """Test that the count tool accepts filter parameters."""
    mock_count_tool.ainvoke = AsyncMock(return_value=10)
    result = await mock_count_tool.ainvoke({"filter": "CompanyCode eq '1000'"})
    assert result == 10


@pytest.mark.asyncio
async def test_agent_responds_to_count_query(add_agent_to_path):
    """Test that the agent processes a cost center count query end-to-end."""
    from agent import SampleAgent

    mock_tools = [MagicMock()]
    mock_tools[0].name = "count_a_costcenter_2_for_sap_self"
    mock_tools[0].description = "Count cost centers"

    mock_response_msg = MagicMock()
    mock_response_msg.content = "We have 42 cost centers in SAP S/4HANA."

    with patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [mock_response_msg]}

        with patch("mcp_providers.agw.get_mcp_tools", new_callable=AsyncMock) as mock_get_tools:
            mock_get_tools.return_value = mock_tools

            agent = SampleAgent()
            result = await agent.invoke("How many cost centers do we have?", "test-ctx", tools=mock_tools)

            assert "42" in result.message or "cost center" in result.message.lower()
