"""MCP tool loader.

Owned indirection layer between agent code and the Agent Gateway.
All agent code imports get_mcp_tools from here.

Behaviour is controlled by the IBD_TESTING environment variable:

  Production (IBD_TESTING not set):
      Uses Agent Gateway client directly from the SDK to connect via mTLS.
      Credentials are loaded from the UMS volume mount (/etc/ums/credentials/credentials)
      or the AGW_CREDENTIALS_JSON environment variable.

  Local / test mode (IBD_TESTING=1):
      Reads mcp-mock.json from the directory containing this file's parent
      (i.e. <asset-root>/mcp-mock.json) and returns LangChain StructuredTool
      instances built from the mock data — no network calls.
"""

import json
import logging
import os
import time
from contextvars import ContextVar, Token
from pathlib import Path
from typing import Any, Optional

from sap_cloud_sdk.agentgateway import create_client
from pydantic import create_model
from langchain_core.tools import StructuredTool

from util import enhance_tool_description, enhance_tool_name, call_mcp_tool_with_retry

logger = logging.getLogger(__name__)

# Context variable to pass user token from request to tool execution
_user_token_context: ContextVar[str | None] = ContextVar('user_token', default=None)

# Reusable AGW client for connection pooling
_agw_client: Optional[Any] = None

# mcp-mock.json lives at the asset root (one level above app/)
_MOCK_FILE = Path(__file__).parent.parent / "mcp-mock.json"


def _build_mock_tools() -> list:
    if not _MOCK_FILE.exists():
        return []
    try:
        mock_data = json.loads(_MOCK_FILE.read_text())
    except Exception:
        logger.warning("Failed to parse mcp-mock.json", exc_info=True)
        return []
    tools = []
    from langchain_core.tools import StructuredTool
    from pydantic import Field, create_model
    for _server_slug, server in mock_data.get("servers", {}).items():
        for tool_name, tool_def in server.get("tools", {}).items():
            description = tool_def.get("description", "")
            mock_response = tool_def.get("mock_response", {})
            input_schema = tool_def.get("input_schema", {})
            props = input_schema.get("properties", {})
            required_fields = set(input_schema.get("required", []))
            field_definitions: dict = {}
            for field_name, field_info in props.items():
                json_type = field_info.get("type", "string")
                python_type = int if json_type == "integer" else float if json_type == "number" else bool if json_type == "boolean" else str
                if field_name in required_fields:
                    field_definitions[field_name] = (python_type, Field(description=field_info.get("description", "")))
                else:
                    field_definitions[field_name] = (python_type, Field(default=None, description=field_info.get("description", "")))
            args_schema = create_model(f"{tool_name}_args", **field_definitions) if field_definitions else create_model(f"{tool_name}_args")
            _response = json.dumps(mock_response)
            async def _coroutine(_resp=_response, **kwargs) -> str:
                return _resp
            tools.append(StructuredTool(name=tool_name, description=description, args_schema=args_schema, coroutine=_coroutine, handle_tool_error=True))
    logger.info("Loaded %d mock MCP tool(s)", len(tools))
    return tools


def _convert_mcp_tool_to_langchain(mcp_tool, agw_client):
    if mcp_tool is None:
        raise ValueError("mcp_tool cannot be None")
    async def run(**kwargs) -> str:
        user_token = _user_token_context.get()
        from util import call_mcp_tool_with_retry
        return await call_mcp_tool_with_retry(agw_client, mcp_tool, user_token=user_token, **kwargs)
    properties = mcp_tool.input_schema.get("properties", {})
    required = set(mcp_tool.input_schema.get("required", []))
    fields = {}
    for name, prop in properties.items():
        prop_type = prop.get("type", "string")
        python_type = int if prop_type == "integer" else float if prop_type == "number" else bool if prop_type == "boolean" else str
        fields[name] = (python_type, ...) if name in required else (python_type | None, None)
    from util import enhance_tool_description, enhance_tool_name
    args_schema = create_model(f"{mcp_tool.name}_args", **fields) if fields else None
    return StructuredTool.from_function(coroutine=run, name=enhance_tool_name(mcp_tool), description=enhance_tool_description(mcp_tool), args_schema=args_schema, handle_tool_error=True)


async def get_mcp_tools(user_token: str | None = None) -> list:
    global _agw_client
    if os.environ.get("IBD_TESTING") == "1":
        return _build_mock_tools()
    if not user_token:
        raise ValueError("user_token required in production mode")
    try:
        if _agw_client is None:
            _agw_client = create_client()
        mcp_tools = await _agw_client.list_mcp_tools(user_token=user_token)
        if not mcp_tools:
            return []
        return [_convert_mcp_tool_to_langchain(t, _agw_client) for t in mcp_tools]
    except Exception:
        logger.exception("Failed to load MCP tools")
        _agw_client = None
        return []


def set_user_token(user_token: str | None) -> Token:
    return _user_token_context.set(user_token)


def get_user_token() -> str | None:
    return _user_token_context.get()
