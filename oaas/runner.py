import time
from .templates import OutcomeTemplate
from .sla import SLATracker


class WorkflowRunner:
    def __init__(self, sla_tracker: SLATracker):
        self.sla = sla_tracker

    async def run(self, template: OutcomeTemplate, payload: dict) -> dict:
        start = time.perf_counter()
        context = dict(payload)

        for step in template.steps:
            for attempt in range(step.retry):
                try:
                    result = await step.fn(context)
                    context.update(result if isinstance(result, dict) else {"result": result})
                    break
                except Exception as e:
                    if attempt == step.retry - 1:
                        raise RuntimeError(f"Step '{step.name}' failed after {step.retry} attempts: {e}")

        latency_ms = (time.perf_counter() - start) * 1000
        breached = self.sla.record(template.name, latency_ms, template.sla_p95_ms)

        return {
            "outcome": {k: context[k] for k in template.output_schema if k in context},
            "latency_ms": round(latency_ms, 2),
            "sla_breached": breached,
            "template": template.name,
        }
