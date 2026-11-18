# Apex Churn Defense System

An LLM-powered retention agent that ingests churn signals — TMF621 bill grievances, billing disputes, and cancellation requests — and enriches each case from billing, charging, competitor, and catalog systems via tool calling.

The agent recommends retention actions (targeted offers, refunds, one-time credits) with the evidence behind each recommendation, ranked by churn risk and subscriber value. Every monetary action requires **human-in-the-loop approval**, keeping the agent advisory-only and each decision audit-ready with a full record of the signals and tools used.

Typed **Pydantic contracts and guardrails** are enforced across every model and tool boundary, making each recommendation reproducible and traceable.

---

## Architecture

```
                           ┌────────────────────────────────┐
                           │   Apex Churn Defense System     │
 Grievance ───────────────►│                                │
 (TMF621 Trouble Ticket)   │   FastAPI  ·  Python 3.11      │
                           │                                │
                           │   ┌──────────────────────────┐ │
                           │   │   LLM Retention Agent    │ │
                           │   │   (tool-calling workflow) │ │
                           │   └────┬────┬────┬────┬──────┘ │
                           │        │    │    │    │         │
                           └────────┼────┼────┼────┼────────┘
                                    │    │    │    │
                    ┌───────────────┘    │    │    └───────────────┐
                    ▼                    ▼    ▼                    ▼
             ┌────────────┐    ┌──────────┐ ┌──────────┐   ┌────────────┐
             │  TMF676    │    │ TMF677   │ │ TMF635   │   │ Competitor │
             │  Payment   │    │ Usage    │ │ Product  │   │ Pricing    │
             │  History   │    │ Consump. │ │ Usage    │   │            │
             └────────────┘    └──────────┘ └──────────┘   └────────────┘
              Billing Sys.     Charging Sys. Usage Hist.    External
```

## Key Design Decisions

| Principle | Implementation |
|---|---|
| **Advisory-only** | Monetary actions (refunds, credits) require human approval before execution |
| **Typed contracts** | Pydantic models at every boundary — API request/response, upstream client, and tool interface |
| **TMF-compliant** | Implements TM Forum Open APIs (TMF621, TMF635, TMF676, TMF677) |
| **Audit-ready** | Full signal-and-tool trace attached to each recommendation |
| **Stub-first dev** | Local stubs for every upstream integration; no external dependencies to run tests |

## Project Structure

```
apex-churn-defense-system/
├── src/
│   ├── main.py                          # FastAPI app entrypoint
│   ├── routes.py                        # TMF621 Trouble Ticket endpoints (exposed)
│   ├── errors.py                        # TMF-shaped error responses
│   ├── store.py                         # In-memory ticket store
│   ├── models/
│   │   └── trouble_ticket_models.py     # TMF621 Pydantic models
│   ├── payment/
│   │   ├── payment_client.py            # TMF676 upstream client (billing)
│   │   ├── payment_models.py            # TMF676 Pydantic models
│   │   └── payment_service.py           # Payment history enrichment
│   ├── usage/
│   │   ├── usage_client.py              # TMF677 upstream client (charging)
│   │   ├── usage_models.py              # TMF677 Pydantic models
│   │   └── usage_service.py             # Consumption & balance enrichment
│   └── product_usage/
│       ├── product_usage_client.py      # TMF635 upstream client (usage history)
│       ├── product_usage_models.py      # TMF635 Pydantic models
│       └── product_usage_service.py     # Usage history enrichment
├── stubs/
│   ├── billing.py                       # Fake TMF676 Payment server (:9001)
│   ├── charging.py                      # Fake TMF677 Usage Consumption server (:9002)
│   └── usage_history.py                 # Fake TMF635 Product Usage server (:9003)
├── tests/
│   ├── test_trouble_ticket.py           # TMF621 endpoint tests
│   ├── test_payment_service.py          # Payment enrichment tests
│   ├── test_usage_service.py            # Usage consumption tests
│   └── test_product_usage_service.py    # Product usage tests
├── tmf-api-yamls/                       # TMF OAS/Swagger contracts (source of truth)
├── pyproject.toml                       # Dependencies (uv-managed)
└── uv.lock
```

## TMF API Coverage

| Package | API | Direction | Purpose |
|---|---|---|---|
| **P1.1** | TMF621 Trouble Ticket v5 | Exposed | Accept bill grievances; each ticket starts the retention workflow |
| **P1.2** | TMF676 Payment v4 | Consumed | Retrieve subscriber payment history from the billing system |
| **P1.3** | TMF677 Usage Consumption v5 | Consumed | Query consumption and remaining balances from the charging system |
| **P1.4** | TMF635 Product Usage v5 | Consumed | Retrieve rated/unrated usage events from the usage history system |
| **P1.5** | TMF676 Refund (planned) | Consumed | Issue TMF676-backed refund (human approval required) |

## Getting Started

### Prerequisites

- **Python 3.11+**
- **[uv](https://docs.astral.sh/uv/)** — fast Python package manager

### Install

```bash
uv sync
```

### Run the Server

```bash
uv run uvicorn src.main:app --reload --port 8080
```

### Run Tests

```bash
uv run pytest -q
```

Tests run against in-process stubs — no external services required.

### Run Stubs Standalone

```bash
uv run uvicorn stubs.billing:app       --port 9001   # TMF676 Payment
uv run uvicorn stubs.charging:app      --port 9002   # TMF677 Usage Consumption
uv run uvicorn stubs.usage_history:app --port 9003   # TMF635 Product Usage
```

## Configuration

| Variable | Default | Purpose |
|---|---|---|
| `BILLING_BASE_URL` | `http://127.0.0.1:9001` | TMF676 Payment upstream |
| `CHARGING_BASE_URL` | `http://127.0.0.1:9002/tmf-api/usageConsumption/v5` | TMF677 Usage Consumption upstream |
| `USAGE_HISTORY_BASE_URL` | `http://127.0.0.1:9003/tmf-api/productUsageManagement/v5` | TMF635 Product Usage upstream |
| `COMPETITOR_BASE_URL` | — | Competitor pricing API (Phase 1.5) |
| `CATALOG_BASE_URL` | — | Product catalog API (future) |

## Roadmap

- [x] **Phase 1** — Overage bill grievance
  - [x] P1.1 · TMF621 Trouble Ticket (exposed)
  - [x] P1.2 · TMF676 Payment history (consumed)
  - [x] P1.3 · TMF677 Usage Consumption (consumed)
  - [x] P1.4 · TMF635 Product Usage history (consumed)
  - [ ] P1.5 · Competitor pricing + TMF676 refund tool (human approval)
- [ ] **Phase 2** — Bill dispute
  - [ ] P2.1 · TMF654 one-time credit tool

## Tech Stack

| Layer | Technology |
|---|---|
| Language | Python 3.11 |
| Framework | FastAPI |
| HTTP client | httpx |
| Validation | Pydantic v2 |
| Testing | pytest |
| Package manager | uv |

## License

Private — all rights reserved.
