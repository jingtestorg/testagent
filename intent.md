# Finance Controller Cost Center Agent

Natural language querying of SAP S/4HANA cost center data for Finance Controllers

## Business challenge

Finance Controllers need instant answers on cost center data — total count and top 5 cost centers — without running manual SAP transactions. The agent enables natural language querying of SAP S/4HANA Controlling data.

## Business Goals & Success Criteria

| Metric | Baseline | Target | Timeline | Process / Capability | Source |
|--------|----------|--------|----------|----------------------|--------|
| Time to answer cost center questions | ~15 min (manual SAP transaction) | < 1 min via agent | — | Cost Center Reporting / Controlling | agent-derived |
| Controller adoption of agent for cost center queries | 0% | 80% of daily queries via agent | — | Finance Self-Service | agent-derived |

## Key Milestones

1. **Cost Center Data Retrieved** — Agent successfully queries SAP S/4HANA and returns total count of cost centers
2. **Top 5 Cost Centers Identified** — Agent ranks and surfaces top 5 cost centers based on user query
3. **Natural Language Response Delivered** — Agent formats and returns a business-friendly answer to the controller
4. **Session Context Maintained** — Agent retains context for follow-up questions within a session

## Business Architecture (RBA)

### End-to-End Process

Finance (Corporate)

### Process Hierarchy

```
Finance (Corporate)
└── Plan to Report
    └── Cost Center Management
        └── Query cost center master data
        └── Analyze cost center distribution
        └── Report cost center KPIs to department heads
```

### Summary

The challenge maps to the Finance E2E process, specifically Cost Center Management under Controlling. The agent replaces manual SAP transaction execution with conversational AI for data retrieval and reporting.

## Fit Gap Analysis

| Requirement (business) | Standard asset(s) found | API ORD ID | MCP Server ORD ID | MCP Server Version | Data Product ORD ID | Gap? | Notes / assumptions |
| ---------------------- | ----------------------- | ---------- | ----------------- | ------------------ | ------------------- | ---- | ------------------- |
| Read cost center master data | Cost Center OData API | `sap.s4:apiResource:CE_COSTCENTER_0001:v1` | — | — | — | No | OData API available; MCP server to be generated via translation file |
| Read cost center hierarchy | Cost Center Hierarchy OData API | `sap.s4:apiResource:CE_COSTCENTERHIERARCHY_0001:v1` | — | — | — | No | OData API available |
| Read controlling area | Controlling Area OData API | `sap.s4:apiResource:API_CONTROLLINGAREA_SRV:v1` | — | — | — | No | OData API available |
| Natural language interface | Custom AI Agent | — | — | — | — | Yes | No standard NL interface; custom Python A2A agent required |

### Key findings
- SAP S/4HANA provides OData APIs for cost center data (CE_COSTCENTER_0001) — no pre-built MCP server found, so an MCP translation file must be generated
- The primary API `CE_COSTCENTER_0001:v1` covers cost center master data reads sufficient for count and ranking queries
- A custom Python AI agent (A2A protocol) is the right approach for natural language understanding and tool orchestration
- No LeanIX landscape data available; S/4HANA is assumed as the target system based on user input
- Controllers will interact via chat; agent connects to S/4HANA via MCP-translated OData calls

## Recommendations

### AI Agent for Cost Center Natural Language Querying

#### Executive Summary

Python A2A agent with MCP tools over S/4HANA Cost Center OData APIs

#### Recommended Solution

Build a Python-based AI agent (A2A protocol) that exposes natural language querying of SAP S/4HANA Controlling cost center data. The agent uses MCP tools backed by the `CE_COSTCENTER_0001` OData API to fetch cost center master data, compute total counts, and rank top cost centers. An MCP translation file will be generated from the OData spec.

#### Recommended solution category

AI Agent

#### Intent fit
92%
