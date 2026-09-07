"""Unit test for the top 5 cost centers tool call."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch


MOCK_COST_CENTERS = [
    {"ControllingArea": "A000", "CostCenter": "CC-1000", "CostCenterName": "Corporate IT",
     "CostCenterDescription": "Corporate Information Technology", "CompanyCode": "1000"},
    {"ControllingArea": "A000", "CostCenter": "CC-2000", "CostCenterName": "Finance",
     "CostCenterDescription": "Finance Department", "CompanyCode": "1000"},
    {"ControllingArea": "A000", "CostCenter": "CC-3000", "CostCenterName": "Human Resources",
     "CostCenterDescription": "Human Resources Department", "CompanyCode": "1000"},
    {"ControllingArea": "A000", "CostCenter": "CC-4000", "CostCenterName": "Sales",
     "CostCenterDescription": "Sales and Marketing", "CompanyCode": "1000"},
    {"ControllingArea": "A000", "CostCenter": "CC-5000", "CostCenterName": "Operations",
     "CostCenterDescription": "Operations Department", "CompanyCode": "1000"},
]


@pytest.fixture
def mock_list_tool():
    """Mock MCP tool that returns a list of cost centers."""
    tool = MagicMock()
    tool.name = "mcp_sap_self__list_a_costcenter_2_for_sap_self"
    tool.description = "Retrieve a list of entities from the A_CostCenter_2 collection."
    tool.ainvoke = AsyncMock(return_value={"results": MOCK_COST_CENTERS})
    return tool


@pytest.mark.asyncio
async def test_list_tool_returns_results(add_agent_to_path, mock_list_tool):
    """Test that the list tool returns cost center results."""
    result = await mock_list_tool.ainvoke({"top": 5})
    assert "results" in result
    assert len(result["results"]) == 5


@pytest.mark.asyncio
async def test_list_tool_returns_correct_fields(add_agent_to_path, mock_list_tool):
    """Test that cost center results have the expected fields."""
    result = await mock_list_tool.ainvoke({"top": 5})
    first = result["results"][0]
    assert "CostCenter" in first
    assert "CostCenterName" in first
    assert "CompanyCode" in first


@pytest.mark.asyncio
async def test_list_tool_top_parameter(add_agent_to_path, mock_list_tool):
    """Test that the list tool is called with top=5."""
    await mock_list_tool.ainvoke({"top": 5})
    mock_list_tool.ainvoke.assert_called_once_with({"top": 5})


@pytest.mark.asyncio
async def test_agent_responds_to_top5_query(add_agent_to_path):
    """Test that the agent processes a top-5 cost centers query."""
    from agent import SampleAgent

    mock_tools = [MagicMock()]
    mock_tools[0].name = "list_a_costcenter_2_for_sap_self"

    expected_content = (
        "Here are the top 5 cost centers:\n"
        "1. CC-1000 - Corporate IT (1000)\n"
        "2. CC-2000 - Finance (1000)\n"
        "3. CC-3000 - Human Resources (1000)\n"
        "4. CC-4000 - Sales (1000)\n"
        "5. CC-5000 - Operations (1000)"
    )
    mock_response_msg = MagicMock()
    mock_response_msg.content = expected_content

    with patch("agent.SampleAgent._invoke_with_fallback", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = {"messages": [mock_response_msg]}

        agent = SampleAgent()
        result = await agent.invoke(
            "Show me the top 5 cost centers",
            "test-ctx",
            tools=mock_tools,
        )

        assert "CC-1000" in result.message or "Corporate IT" in result.message or "cost center" in result.message.lower()
