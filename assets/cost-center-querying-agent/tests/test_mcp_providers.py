"""Tests for MCP providers module."""
import pytest
import json
import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch


def test_mock_file_exists(add_agent_to_path, agent_path):
    """Test that mcp-mock.json exists at agent root."""
    mock_file = agent_path / "mcp-mock.json"
    assert mock_file.exists(), f"mcp-mock.json not found at {mock_file}"


def test_mock_file_is_valid_json(add_agent_to_path, agent_path):
    """Test that mcp-mock.json is valid JSON."""
    mock_file = agent_path / "mcp-mock.json"
    data = json.loads(mock_file.read_text())
    assert "servers" in data
    assert "metadata" in data


def test_mock_file_has_sap_self_server(add_agent_to_path, agent_path):
    """Test that mcp-mock.json has the sap-self server."""
    mock_file = agent_path / "mcp-mock.json"
    data = json.loads(mock_file.read_text())
    assert "sap-self" in data["servers"]


def test_mock_file_has_cost_center_tools(add_agent_to_path, agent_path):
    """Test that sap-self server has cost center tools."""
    mock_file = agent_path / "mcp-mock.json"
    data = json.loads(mock_file.read_text())
    tools = data["servers"]["sap-self"]["tools"]
    assert "list_a_costcenter_2_for_sap_self" in tools
    assert "count_a_costcenter_2_for_sap_self" in tools


def test_mock_count_tool_response(add_agent_to_path, agent_path):
    """Test that count tool has numeric mock response."""
    mock_file = agent_path / "mcp-mock.json"
    data = json.loads(mock_file.read_text())
    count_tool = data["servers"]["sap-self"]["tools"]["count_a_costcenter_2_for_sap_self"]
    assert isinstance(count_tool["mock_response"], int)
    assert count_tool["mock_response"] > 0


def test_mock_list_tool_response(add_agent_to_path, agent_path):
    """Test that list tool has results array mock response."""
    mock_file = agent_path / "mcp-mock.json"
    data = json.loads(mock_file.read_text())
    list_tool = data["servers"]["sap-self"]["tools"]["list_a_costcenter_2_for_sap_self"]
    assert "results" in list_tool["mock_response"]
    assert len(list_tool["mock_response"]["results"]) > 0


def test_mock_list_tool_result_has_required_fields(add_agent_to_path, agent_path):
    """Test that mock cost center results have required fields."""
    mock_file = agent_path / "mcp-mock.json"
    data = json.loads(mock_file.read_text())
    first_result = data["servers"]["sap-self"]["tools"]["list_a_costcenter_2_for_sap_self"]["mock_response"]["results"][0]
    assert "CostCenter" in first_result
    assert "CostCenterName" in first_result
    assert "CompanyCode" in first_result
    assert "ControllingArea" in first_result


@pytest.mark.asyncio
async def test_get_mcp_tools_returns_list(add_agent_to_path):
    """Test that get_mcp_tools returns a list in test mode."""
    from mcp_providers.agw import get_mcp_tools

    tools = await get_mcp_tools()
    assert isinstance(tools, list)


@pytest.mark.asyncio
async def test_get_mcp_tools_all_callable(add_agent_to_path):
    """Test that all tools from get_mcp_tools are callable."""
    from mcp_providers.agw import get_mcp_tools

    tools = await get_mcp_tools()
    for tool in tools:
        assert hasattr(tool, "name")
        assert hasattr(tool, "description")
