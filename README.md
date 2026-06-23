# Outcome-as-a-Service (OaaS)

![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688)
![License](https://img.shields.io/badge/license-MIT-green)
![Stack](https://img.shields.io/badge/stack-LangChain%20%7C%20Prometheus%20%7C%20Redis-blue)

Modular AI service framework that wraps complex multi-step LLM workflows behind a **single API endpoint**, with built-in SLA tracking, outcome contracts, and retry policies — so consumers get a guaranteed result, not a model response.

> The core insight: callers shouldn't care *how* an AI result is produced. They should define *what* a valid result looks like, and the platform handles model selection, retries, validation, and SLA enforcement.

---

## Problem

Multi-step AI workflows (extract → validate → enrich → summarize) are typically glued together in application code, making them:

- **Brittle** — one failed step breaks the whole pipeline with no recovery
- **Unobservable** — no SLA visibility per workflow step
- **Hard to reuse** — each team reimplements the same patterns

OaaS separates **outcome definition** (schema, confidence threshold, latency SLA) from **workflow execution** (model calls, retries, validation), making AI workflows composable infrastructure.

---

## Architecture

```
  POST /outcomes/{template}
           │
           ▼
  ┌────────────────────────────────────────────────┐
  │               OaaS Platform                    │
  │                                                │
  │  Template Engine                               │
  │  └── load template definition (name, steps,   │
  │       SLA, output schema, retry policy)        │
  │              │                                 │
  │  Step Runner (sequential / parallel)           │
  │  ┌──────────────────────────────────┐          │
  │  │  Step 1: LLM call / Tool call    │          │
  │  │  Step 2: Validator               │──retry──►│
  │  │  Step 3: Enrichment              │          │
  │  │  Step N: ...                     │          │
  │  └──────────────────────────────────┘          │
  │              │                                 │
  │  Outcome Contract Checker                      │
  │  ├── JSON schema validation                    │
  │  ├── confidence threshold check                │
  │  └── retry if contract not met (max_retries)   │
  │              │                                 │
  │  SLA Tracker (Prometheus)                      │
  │  └── P50 / P95 / P99 per template              │
  └────────────────────────────────────────────────┘
           │
           ▼
  {result, sla_metadata, contract_met, attempts}
```

---

## Key Concepts

### Outcome Contract

Defines what a *valid* result looks like — not just schema, but quality gates:

```python
contract = OutcomeContract(
    output_schema={"score": float, "reasons": list[str], "confidence": float},
    confidence_threshold=0.8,   # retry if model confidence < 0.8
    max_retries=3,
    fallback="cloud_full",      # escalate model tier on retry
)
```

### Workflow Template

A named, reusable pipeline that users invoke by name:

```python
template = OutcomeTemplate(
    name="risk_score",
    sla_p95_ms=2000,
    contract=contract,
    steps=[
        Step(name="extract_entities", fn=extract_entities),
        Step(name="score_risk",       fn=score_risk),
        Step(name="format_output",    fn=format_for_contract),
    ],
)
```

---

## Quick Start

```bash
git clone https://github.com/Shriniwas410/outcome-as-a-service
cd outcome-as-a-service
pip install -r requirements.txt

uvicorn oaas.server:app --reload
```

### Built-in Templates

| Template | Description | Steps | Typical P95 |
|---|---|---|---|
| `summarize` | Extractive + abstractive summarization | 2 | < 3s |
| `extract` | Structured entity/field extraction with schema | 3 | < 2s |
| `classify` | Multi-label classification with confidence gating | 2 | < 1s |
| `qa` | RAG-backed question answering with citation | 4 | < 4s |

### Run a Built-in Template

```bash
# Summarization
curl -X POST http://localhost:8000/outcomes/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "Long document...", "max_length": 200}'

# Response
{
  "result": {
    "summary": "...",
    "confidence": 0.91
  },
  "contract_met": true,
  "attempts": 1,
  "latency_ms": 1840,
  "sla": {"p95_ms": 3000, "within_sla": true}
}

# Extraction with custom schema
curl -X POST http://localhost:8000/outcomes/extract \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Invoice from Acme Corp, total $4,200, due 2025-02-15",
    "schema": {"vendor": "str", "amount": "float", "due_date": "str"}
  }'
```

### Define a Custom Template

```python
from oaas import OutcomeTemplate, OutcomeContract, Step

# Define the outcome contract
contract = OutcomeContract(
    output_schema={"risk_level": str, "score": float, "flags": list[str]},
    confidence_threshold=0.85,
    max_retries=2,
    fallback="cloud_full",
)

# Define the workflow
template = OutcomeTemplate(
    name="credit_risk",
    sla_p95_ms=2500,
    contract=contract,
    steps=[
        Step(name="parse_financials",  fn=parse_financials),
        Step(name="run_risk_model",    fn=run_risk_model),
        Step(name="validate_output",   fn=validate_against_contract),
    ],
)

# Register and deploy
app.register_template(template)
```

---

## SLA Dashboard

```http
GET /sla/summarize
→ {
    "template": "summarize",
    "p50_ms": 920,
    "p95_ms": 2100,
    "p99_ms": 3800,
    "breach_rate": 0.003,
    "contract_pass_rate": 0.97,
    "calls_24h": 8412
  }

GET /sla
→ [per-template SLA summary for all registered templates]
```

---

## Retry and Escalation Policy

When a step fails or the outcome contract is not met:

1. **Retry same model** (attempt ≤ `max_retries / 2`)
2. **Escalate model tier** — route to `fallback` model (e.g., cloud_full)
3. **Return partial result** with `contract_met: false` if all retries exhausted

This means callers always get a response — they can decide whether to use a partial result or surface an error based on `contract_met`.

---

## Module Overview

```
oaas/
├── server.py          # FastAPI app — /outcomes/{template} and /sla endpoints
├── template_engine.py # Template loading, step orchestration, retry logic
├── contracts.py       # OutcomeContract definition and validation
├── step_runner.py     # Sequential and parallel step execution with timeout
├── sla_tracker.py     # Prometheus histograms for P50/P95/P99 per template
└── templates/         # Built-in template definitions (summarize, extract, qa…)
```

---

## Design Decisions

- **Outcome contracts, not model contracts** — the SLA is on the final result, not on any individual LLM call; retries and escalation are invisible to callers
- **Prometheus for SLA** — histograms give true percentiles, not averages; breach alerting fires when P95 exceeds the declared SLA
- **Step runner is async** — parallel steps run concurrently via `asyncio.gather`; sequential dependencies declared explicitly in template definition
- **Templates are code, not config** — defining steps as Python functions keeps IDE support, type checking, and testability; no YAML DSL to learn

---

## Tech Stack

| Layer | Technology |
|---|---|
| API server | FastAPI + Uvicorn |
| Workflow orchestration | Custom step runner (asyncio) |
| LLM backends | LangChain + OpenAI / Gemini |
| SLA monitoring | Prometheus + Grafana |
| State / caching | Redis |
| Schema validation | Pydantic v2 |

---

## License

MIT
