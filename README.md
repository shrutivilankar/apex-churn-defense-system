# Apex Churn Defense System

> **Telecom carriers lose over $65 billion annually to subscriber churn.** Most retention happens too late — after the customer has already decided to leave. What if an AI agent could intercept the earliest signals of dissatisfaction and act before that decision is made?

Apex is an **LLM-powered retention agent** that intercepts churn signals in real time — bill grievances, overage complaints, billing disputes, and cancellation requests — and autonomously enriches each case by pulling context from billing, charging, usage, competitor pricing, and catalog systems through **tool calling**.

The agent reasons over the assembled evidence to recommend retention actions — targeted offers, refunds, or one-time credits — **ranked by churn risk and subscriber lifetime value**. Every recommendation ships with a full audit trail of the signals ingested and tools invoked, making each decision traceable and reproducible.

**Monetary actions are advisory-only.** Refunds and credits require explicit human approval before execution, enforcing a human-in-the-loop boundary between AI reasoning and financial impact.

---

## Architecture

<p align="center">
  <img src="docs/architecture.png" alt="Apex Churn Defense Platform Architecture" width="700"/>
</p>

The platform receives churn signals from three event sources — **usage threshold breaches**, **cancellation requests**, and **customer grievances** — and enriches them from charging, billing, competitor pricing, and promotion systems to build a complete subscriber context before the retention agent acts.

---

## Engineering Highlights

### 🔒 Human-in-the-Loop for Monetary Actions
The agent can *recommend* a $50 credit or a plan upgrade — but it cannot execute it. Every monetary action is gated behind a human approval step, keeping the system advisory-only. This isn't just a flag; the approval boundary is enforced architecturally so the agent literally cannot bypass it.

### 📐 Typed Contracts at Every Boundary
Pydantic models enforce strict typing at every integration point — inbound API requests, upstream system responses, LLM tool inputs/outputs, and recommendation payloads. If a shape is wrong, it fails fast and loud. This makes the entire tool-calling chain reproducible: given the same inputs, the agent produces the same evidence and recommendation.

### 🔌 TM Forum Open API Compliance
The system speaks the telecom industry's standard language. Churn signals arrive as TMF621 Trouble Tickets. Enrichment pulls from TMF676 (payments), TMF677 (consumption/balances), and TMF635 (usage history). This isn't a toy wrapper — the models are built from the actual OAS/Swagger specs, with only required fields implemented to keep the surface minimal.

### 🧪 Stub-First Development
Every upstream integration has a local stub server that returns realistic data. Tests run entirely in-process against these stubs — no Docker, no external services, no network calls. This means the full test suite runs in under a second and the system is demonstrable without any infrastructure.

### 📋 Audit-Ready Recommendations
Each recommendation carries the complete chain: which signals triggered it, which tools were called, what data was returned, and how the agent weighted the evidence. This isn't just logging — it's a first-class data structure designed for compliance review.

---

## Quick Start

```bash
# Install dependencies
uv sync

# Run the server and stub one by one 
uv run uvicorn src.main:app --reload --port 8080

#Or run all servers and stubs on bash at once
(trap 'kill 0' SIGINT; \
uv run uvicorn stubs.billing:app --port 9001 & \
uv run uvicorn stubs.charging:app --port 9002 & \
uv run uvicorn stubs.usage_history:app --port 9003 & \
uv run uvicorn stubs.catalog:app --port 9005 & \
uv run uvicorn apex_churn_defense.main:app --reload --port 8080)

# Run tests
uv run pytest -q
```

> Requires **Python 3.11+** and **[uv](https://docs.astral.sh/uv/)**. Tests run against in-process stubs — no external services needed.

---

## Tech Stack

| | |
|---|---|
| **Language** | Python 3.11 |
| **Framework** | FastAPI |
| **LLM** | OpenAI SDK — tool-calling agent with structured outputs |
| **Validation** | Pydantic v2 — strict types at every boundary |
| **HTTP** | httpx (async) |
| **Testing** | pytest with in-process stub servers |
| **Standards** | TM Forum Open APIs (TMF621, TMF635, TMF676, TMF677) |

---

## Status

The core enrichment pipeline — grievance intake through payment, consumption, and usage history retrieval — is implemented and tested. The risk profiling and scoring engine computes churn risk and subscriber value from enriched signals. The LLM retention agent uses these as tool inputs to reason over recommendations, with competitor pricing and refund/credit execution (human-approved) actively in development.

---

## License

This project is shared for portfolio and discussion purposes.  
All rights reserved — not licensed for reuse or redistribution.
