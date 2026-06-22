from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class Step:
    name: str
    fn: Callable[..., Any]
    retry: int = 1
    timeout_ms: int = 5000


@dataclass
class OutcomeTemplate:
    name: str
    steps: list[Step]
    output_schema: dict[str, Any]
    sla_p95_ms: int = 3000
    confidence_threshold: float = 0.7
    metadata: dict[str, Any] = field(default_factory=dict)


BUILTIN_TEMPLATES: dict[str, OutcomeTemplate] = {}


def register_template(template: OutcomeTemplate) -> None:
    BUILTIN_TEMPLATES[template.name] = template


def get_template(name: str) -> OutcomeTemplate | None:
    return BUILTIN_TEMPLATES.get(name)
