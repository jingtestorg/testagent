# Product Requirements Document (PRD)

**Title:** Finance Controller Cost Center Agent
**Date:** 2026-09-07
**Owner:** Finance Controlling
**Solution Category:** AI Agent

## Product Purpose & Value Proposition

**Elevator Pitch:**
Finance Controllers spend valuable time running manual SAP transactions to answer simple cost center questions from department heads. This agent lets them ask those questions in plain language and get instant, accurate answers — without opening a SAP GUI.

**Business Need:**
Controllers regularly need to answer questions like "how many cost centers do we have?" or "which are our top cost centers?" These require manual navigation of SAP S/4HANA Controlling transactions, taking 10–15 minutes per query. A conversational AI agent connected directly to the cost center OData APIs eliminates this friction.

**Expected Value:**
- Cost center lookup time reduced from ~15 minutes to under 1 minute
- Controllers can self-serve answers without SAP transaction knowledge
- Department questions answered in real time during meetings

**Product Objectives (Prioritized):**
1. Enable natural language querying of cost center master data from SAP S/4HANA
2. Deliver total cost center count and top 5 cost centers in a single interaction
3. Maintain session context to support follow-up questions without re-querying

## Business Metrics

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Time to answer cost center questions | ~15 min (manual SAP transaction) | < 1 min via agent | — | Cost Center Reporting / Controlling | agent-derived |
| Controller adoption of agent for cost center queries | 0% | 80% of daily queries via agent | — | Finance Self-Service | agent-derived |

## Requirements

### Must-Have Requirements

**R1**: Query Total Count of Cost Centers

- **Problem to Solve**: Controllers cannot quickly determine the total number of active cost centers without running a manual SAP report.
- **User Story**: As a Finance Controller, I need to ask "how many cost centers do we have?" in plain language so that I can answer department questions instantly.
- **Acceptance Criteria**:
  - Given the agent is running, when the controller asks for the total count of cost centers, then the agent returns the correct count from SAP S/4HANA within 60 seconds.
- **Maps to Objective**: Objective 1
- **Priority Rank**: 1

**R2**: Retrieve Top 5 Cost Centers

- **Problem to Solve**: Controllers need to identify the most significant cost centers quickly for reporting and department discussions.
- **User Story**: As a Finance Controller, I need to ask for the top 5 cost centers so that I can prioritize departmental discussions and budget reviews.
- **Acceptance Criteria**:
  - Given the agent is running, when the controller asks for the top 5 cost centers, then the agent returns a ranked list with cost center IDs and names from SAP S/4HANA.
- **Maps to Objective**: Objective 1, 2
- **Priority Rank**: 2

**R3**: Natural Language Interface

- **Problem to Solve**: Controllers are not SAP transaction experts and need a way to query data without knowing transaction codes or OData syntax.
- **User Story**: As a Finance Controller, I need to interact with the agent in plain English so that I can get answers without SAP expertise.
- **Acceptance Criteria**:
  - Given a natural language question about cost centers, when the agent processes it, then the agent correctly interprets the intent and returns a structured business-friendly response.
- **Maps to Objective**: Objective 1
- **Priority Rank**: 3

**R4**: SAP S/4HANA Integration via Cost Center OData API

- **Problem to Solve**: The agent must retrieve live, accurate data from SAP S/4HANA, not from cached or static sources.
- **User Story**: As a Finance Controller, I need the agent to query live SAP data so that my answers are accurate and current.
- **Acceptance Criteria**:
  - Given a user query, when the agent calls the backend, then it invokes the `CE_COSTCENTER_0001` OData API and returns real-time data.
- **Maps to Objective**: Objective 1, 2
- **Priority Rank**: 4

**R5**: Follow-up Question Support

- **Problem to Solve**: Controllers often ask follow-up questions in the same session and expect the agent to retain context.
- **User Story**: As a Finance Controller, I need the agent to remember what I asked before so that I don't have to repeat context in each question.
- **Acceptance Criteria**:
  - Given a prior query in the session, when the controller asks a follow-up, then the agent uses session context to resolve the follow-up correctly without re-fetching unchanged data.
- **Maps to Objective**: Objective 3
- **Priority Rank**: 5

## Solution Architecture

**Architecture Overview:**
A Python-based AI agent built on the A2A protocol connects to SAP S/4HANA via an MCP server generated from the `CE_COSTCENTER_0001` OData API spec. The agent interprets natural language, selects the appropriate MCP tools, and returns formatted answers to the controller.

**Key Components:**

- **Python A2A Agent**: Core reasoning engine; interprets user intent, orchestrates MCP tool calls, formats responses
- **MCP Translation File**: Auto-generated from `CE_COSTCENTER_0001` EDMX spec; exposes cost center OData operations as MCP tools
- **SAP S/4HANA Controlling**: Source of truth for cost center master data

**Integration Points:**

- SAP S/4HANA `CE_COSTCENTER_0001` OData API: read cost center entities, filter and sort for top 5 ranking

### Agent Extensibility & Instrumentation

**Agent Extensibility:**
- The agent is designed with extension points to support additional Controlling queries (e.g., cost center budgets, actuals) in future iterations
- MCP tool definitions are decoupled from agent logic, allowing new OData-backed tools to be added without changing core agent code

**Business Step Instrumentation:**
- All key business steps emit structured log statements for observability
- Log pattern: `[MILESTONE_ID].[achieved|missed]: [description]`
- See Milestones section for full definitions

### Automation & Agent Behaviour

**Automation Level:** Autonomous agent (read-only queries only)

**Actions the system performs without human approval:**
- Query cost center count from SAP S/4HANA
- Retrieve and rank top 5 cost centers
- Format and return natural language response

**Actions that require human review or approval:**
- None (agent is read-only; no write operations)

**Model or engine used:** SAP Generative AI Hub (GPT-4o or equivalent)

**Knowledge & data sources accessed:**
- SAP S/4HANA: Cost Center master data via `CE_COSTCENTER_0001` OData API

**Tools or connectors invoked:**
- `list_cost_centers`: reads cost center entities from S/4HANA (read-only)
- `get_cost_center_count`: returns total count of cost centers (read-only)

**Guardrails & fail-safes:**
- Agent performs read-only operations; no create, update, or delete is permitted
- If the OData API is unavailable, the agent returns a graceful error message to the controller
- Responses are scoped to cost center data only; out-of-scope queries are declined politely

## Milestones

### M1: Cost Center Data Retrieved

- **Description**: The agent successfully calls the SAP S/4HANA OData API and receives cost center data
- **Achieved when**: A valid response with at least one cost center record is returned from the API
- **Log on achievement**: `M1.achieved: cost center data retrieved from SAP S/4HANA`
- **Log on miss**: `M1.missed: cost center data retrieval failed or returned empty`

### M2: Top 5 Cost Centers Identified

- **Description**: The agent ranks and selects the top 5 cost centers from the retrieved data set
- **Achieved when**: A ranked list of 5 cost centers is produced
- **Log on achievement**: `M2.achieved: top 5 cost centers identified and ranked`
- **Log on miss**: `M2.missed: insufficient data to rank top 5 cost centers`

### M3: Natural Language Response Delivered

- **Description**: The agent formats the result into a clear, business-friendly natural language answer
- **Achieved when**: A formatted response is returned to the controller
- **Log on achievement**: `M3.achieved: natural language response delivered to controller`
- **Log on miss**: `M3.missed: response formatting failed`

### M4: Session Context Maintained

- **Description**: The agent retains prior query context to correctly handle follow-up questions
- **Achieved when**: A follow-up question is resolved correctly using session history without re-querying unchanged data
- **Log on achievement**: `M4.achieved: session context used successfully for follow-up`
- **Log on miss**: `M4.missed: session context not available or not applied`
