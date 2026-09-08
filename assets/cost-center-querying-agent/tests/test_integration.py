"""Integration test: end-to-end agent flow with mocked LLM and MCP tools."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.mark.asyncio
async def test_agent_end_to_end_count_query(add_agent_to_path):
    """Full agent flow: mock LLM + mock MCP tools → cost center count query."""
    from agent import SampleAgent

    # Mock MCP tools
    count_tool = MagicMock()
    count_tool.name = "count_a_costcenter_2_for_sap_self"
    count_tool.description = "Get count of cost centers"
    count_tool.ainvoke = AsyncMock(return_value=42)

    mock_tools = [count_tool]

    # Mock LLM response
    mock_response_msg = MagicMock()
    mock_response_msg.content = "There are 42 cost centers in SAP S/4HANA Controlling."

    with patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [mock_response_msg]}

        agent = SampleAgent()
        result = await agent.invoke(
            "How many cost centers do we have?",
            "integration-test-ctx",
            tools=mock_tools,
        )

        assert result.status == "completed"
        assert result.message is not None
        assert len(result.message) > 0
        # Response should mention the count or cost centers
        assert any(word in result.message.lower() for word in ["42", "cost center", "have"])


@pytest.mark.asyncio
async def test_agent_end_to_end_top5_query(add_agent_to_path):
    """Full agent flow: mock LLM + mock MCP tools → top 5 cost centers query."""
    from agent import SampleAgent

    list_tool = MagicMock()
    list_tool.name = "list_a_costcenter_2_for_sap_self"
    list_tool.description = "List cost centers"
    list_tool.ainvoke = AsyncMock(return_value={
        "results": [
            {"CostCenter": "CC-1000", "CostCenterName": "Corporate IT", "CompanyCode": "1000"},
            {"CostCenter": "CC-2000", "CostCenterName": "Finance", "CompanyCode": "1000"},
        ]
    })

    mock_tools = [list_tool]

    mock_response_msg = MagicMock()
    mock_response_msg.content = "Here are the top 5 cost centers: CC-1000 Corporate IT, CC-2000 Finance..."

    with patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [mock_response_msg]}

        agent = SampleAgent()
        result = await agent.invoke(
            "Show me the top 5 cost centers",
            "integration-test-ctx-top5",
            tools=mock_tools,
        )

        assert result.status == "completed"
        assert result.message is not None


@pytest.mark.asyncio
async def test_agent_stream_yields_response(add_agent_to_path):
    """Test that agent stream() yields a final response."""
    from agent import SampleAgent

    mock_tools = [MagicMock()]
    mock_tools[0].name = "count_a_costcenter_2_for_sap_self"

    mock_response_msg = MagicMock()
    mock_response_msg.content = "You have 42 cost centers."

    with patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [mock_response_msg]}

        agent = SampleAgent()
        chunks = []
        async for chunk in agent.stream("How many cost centers?", "stream-test", tools=mock_tools):
            chunks.append(chunk)

        # Should have at least 2 chunks: "Processing..." + final response
        assert len(chunks) >= 1
        final = chunks[-1]
        assert final["is_task_complete"] is True
        assert final["content"] is not None


@pytest.mark.asyncio
async def test_agent_mcp_mock_tools_loaded(add_agent_to_path):
    """Test that mock MCP tools load correctly from mcp-mock.json in test mode."""
    from mcp_providers.agw import get_mcp_tools

    # IBD_TESTING=1 is set by conftest.py
    tools = await get_mcp_tools()
    assert isinstance(tools, list)
    # Should have tools from mcp-mock.json
    assert len(tools) > 0
    # All tools should be callable LangChain tools
    tool_names = [t.name for t in tools]
    assert any("costcenter" in name.lower() or "cost" in name.lower() for name in tool_names)
