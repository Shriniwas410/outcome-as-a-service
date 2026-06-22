# Outcome-as-a-Service (OaaS)

Modular AI service templates for single-API deployments of monitored, SLA-backed workflows.

## Overview

OaaS packages complex multi-step AI workflows behind a single endpoint with built-in:

- **SLA Monitoring**: P50/P95/P99 latency tracking, alerting on breach
- **Outcome Contracts**: Define what "done" means — schema, confidence threshold, retry policy
- **Workflow Templates**: Pre-built templates for summarization, extraction, classification, and generation
- **Single-API Deployment**: One `POST /outcomes/{template}` call, full workflow handled internally

## Architecture

```
POST /outcomes/{template}
         ↓
  Template Engine → Step Runner → [LLM / Tool calls / Validators]
         ↓               ↓
   SLA Tracker     Outcome Contract Checker
         ↓
  Response + SLA metadata
```

## Quick Start

```bash
pip install -r requirements.txt

# Start server
uvicorn oaas.server:app --reload

# Run a summarization workflow
curl -X POST http://localhost:8000/outcomes/summarize \
  -H "Content-Type: application/json" \
  -d '{"text": "Long document...", "max_length": 200}'
```

## Built-in Templates

| Template | Description | Typical P95 |
|---|---|---|
| `summarize` | Extractive + abstractive summarization | < 3s |
| `extract` | Structured entity/field extraction | < 2s |
| `classify` | Multi-label classification with confidence | < 1s |
| `qa` | RAG-backed question answering | < 4s |

## Custom Templates

```python
from oaas import OutcomeTemplate, Step

my_template = OutcomeTemplate(
    name="risk_score",
    sla_p95_ms=2000,
    steps=[
        Step(name="extract_entities", fn=extract_entities),
        Step(name="score_risk", fn=score_risk),
    ],
    output_schema={"score": float, "reasons": list[str]},
)
```

## SLA Dashboard

```http
GET /sla/{template}
→ {"p50_ms": 420, "p95_ms": 1100, "p99_ms": 1850, "breach_rate": 0.002}
```

## Tech Stack

Python · FastAPI · Pydantic · LangChain · OpenAI/Gemini · Prometheus · Redis
