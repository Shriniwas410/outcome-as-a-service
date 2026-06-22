from fastapi import FastAPI, HTTPException
from .templates import get_template
from .runner import WorkflowRunner
from .sla import SLATracker

app = FastAPI(title="Outcome-as-a-Service", version="0.1.0")
sla = SLATracker()
runner = WorkflowRunner(sla)


@app.post("/outcomes/{template_name}")
async def run_outcome(template_name: str, payload: dict):
    template = get_template(template_name)
    if not template:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    try:
        return await runner.run(template, payload)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sla/{template_name}")
def get_sla(template_name: str):
    return sla.stats(template_name)


@app.get("/templates")
def list_templates():
    from .templates import BUILTIN_TEMPLATES
    return [{"name": t.name, "sla_p95_ms": t.sla_p95_ms} for t in BUILTIN_TEMPLATES.values()]
