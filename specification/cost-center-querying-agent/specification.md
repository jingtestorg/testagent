# Specification: cost-center-querying-agent

> **Guidelines**: Read all applicable guidelines before executing ANY tasks below:
> - [guidelines.md](../guidelines.md) — Universal execution rules
> - [guidelines-agent.md](../guidelines-agent.md) — Universal agent patterns
> - [guidelines-agent-python.md](../guidelines-agent-python.md) — Python implementation details
> - [guidelines-agent-skills.md](../guidelines-agent-skills.md) — Runtime skills patterns
> - [guidelines-agent-mcp.md](../guidelines-agent-mcp.md) — MCP integration patterns

---

## Basic Setup

- [ ] Read `product-requirements-document.md` and `intent.md` for full context
- [ ] Bootstrap agent code in `assets/cost-center-querying-agent/` using the `sap-agent-bootstrap` skill (invoke from inside `assets/cost-center-querying-agent/`, use copy commands — do NOT create files manually)
- [ ] Install dependencies: `pip install -r requirements.txt` from `assets/cost-center-querying-agent/`
- [ ] Validate the agent starts and responds at `/.well-known/agent.json`

---

## Runtime Skills

No runtime skills are required. The cost center querying logic is straightforward (single tool calls, no branching workflow), suitable for system prompt instructions only.

---

## Project-Specific Tasks

### System Prompt

- [ ] Write the agent system prompt in `assets/cost-center-querying-agent/app/agent.py` `@prompt_section` decorator:
  - Role: "You are a Finance Controller assistant for SAP S/4HANA Controlling. You answer questions about cost centers using live data from SAP."
  - Always use tools to retrieve live data — never fabricate, guess, or invent cost center data
  - When asked for total count of cost centers, call the list/count tool and return the exact number
  - When asked for top 5 cost centers, call the list tool with `$top=5` (or equivalent) sorted by CostCenter ascending, and return a formatted list with CostCenter ID, Name, and Description
  - When calling tools that support pagination, always set the page size parameter to a maximum of 100
  - If a tool returns an error, relay the error message exactly as received without adding suggestions
  - Maintain session context for follow-up questions

### MCP Translation File

- [ ] Invoke the `mcp-translation-file` skill with the EDMX file at `specification/cost-center-querying-agent/api-specs/CE_COSTCENTER_0001.edmx`
  - API ORD ID: `sap.s4:apiResource:CE_COSTCENTER_0001:v1`
  - API type: `edmx`
  - The skill outputs to `specification/cost-center-querying-agent/mcps/CE_COSTCENTER_0001/`

### MCP Server Asset Setup

- [ ] Invoke the `setup-solution` skill to create the MCP server asset for the generated translation file
  - After completion, read the generated `asset.yaml` and copy the `ordId` value exactly for use in the agent's `asset.yaml`
  - `grep '^ordId:' assets/<mcp-server-asset-name>/asset.yaml`

### Agent MCP Wiring

- [ ] Wire MCP tool loading in `assets/cost-center-querying-agent/app/agent.py`:
  - Import `get_mcp_tools` from `mcp_tools` module (bootstrap-generated)
  - Load tools lazily (not in `__init__`) — wire into the agent graph in `_get_tools()`
  - NEVER import directly from `sap_cloud_sdk.agentgateway`
  - NEVER create direct HTTP clients for SAP APIs
- [ ] Add MCP server dependency to `assets/cost-center-querying-agent/asset.yaml` under `requires`:
  ```yaml
  requires:
    - name: ce-costcenter-mcp-server
      kind: mcp-server
      ordId: <exact ordId from generated asset.yaml>
  ```

### Cost Center Query Features

- [ ] Implement handler for **total count query**: When the user asks "how many cost centers", "total count", or similar, the agent calls the list tool with `$count=true` or fetches all and counts, returning the exact integer
- [ ] Implement handler for **top 5 cost centers query**: When the user asks for "top 5 cost centers" or "top cost centers", the agent calls the list tool with `$top=5`, then formats and returns: CostCenter ID, CostCenterName, CostCenterDescription, CompanyCode
- [ ] Implement **session context**: Agent retains prior query results in LangChain memory TTL so follow-up questions (e.g. "tell me more about the first one") resolve correctly without re-querying

---

## Business Instrumentation

- [ ] Implement business step instrumentation for each milestone:
  - **M1** — Cost Center Data Retrieved: log `M1.achieved: cost center data retrieved from SAP S/4HANA` on success; `M1.missed: cost center data retrieval failed or returned empty` on failure
  - **M2** — Top 5 Cost Centers Identified: log `M2.achieved: top 5 cost centers identified and ranked`; `M2.missed: insufficient data to rank top 5 cost centers`
  - **M3** — Natural Language Response Delivered: log `M3.achieved: natural language response delivered to controller`; `M3.missed: response formatting failed`
  - **M4** — Session Context Maintained: log `M4.achieved: session context used successfully for follow-up`; `M4.missed: session context not available or not applied`
  - Use OpenTelemetry spans — decorator form `@tracer.start_as_current_span("name")` on plain async methods; context manager form inside non-generator async functions
  - **NEVER** use `with tracer.start_as_current_span(...)` inside `stream()` (async generator) — extract business logic to `_run_agent()` helper
- [ ] Verify `auto_instrument()` is called at top of `main.py` before any AI framework imports

---

## MCP Mock Configuration

- [ ] After MCP translation file and setup-solution complete, invoke `mcp-mock-config` skill to generate `mcp-mock.json` in `assets/cost-center-querying-agent/`

---

## Testing

- [ ] `conftest.py` sets only `IBD_TESTING=true` — the fixture monkey-patches `mcp_tools.get_mcp_tools`
- [ ] Write unit tests in `assets/cost-center-querying-agent/tests/`:
  - `test_cost_center_count.py` — tests the cost center count tool call; mock MCP tool returning a list of 3 cost centers; assert agent returns "3" or "3 cost centers"
  - `test_top_5_cost_centers.py` — tests top-5 query; mock MCP tool returning 5 cost center records; assert agent returns formatted list with IDs and names
  - Run each test immediately after writing it
- [ ] Write one integration test `test_integration.py` — full agent flow: mock LLM + mock MCP, query "how many cost centers?", assert response contains a count
- [ ] Run `pytest` from `assets/cost-center-querying-agent/` (no args) — if coverage < 70%, add tests
- [ ] Verify `assets/cost-center-querying-agent/app/agent.py` has exactly 9 decorated functions: run `grep -c "^@agent_model\|^@agent_config\|^@prompt_section" assets/cost-center-querying-agent/app/agent.py` and confirm it returns 9
- [ ] Run `pytest` again (no args) to produce final `test_report.json`
- [ ] Verify `test_report.json` exists in `assets/cost-center-querying-agent/`
