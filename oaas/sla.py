import time
from collections import defaultdict
from statistics import quantiles


class SLATracker:
    def __init__(self):
        self._latencies: dict[str, list[float]] = defaultdict(list)
        self._breach_counts: dict[str, int] = defaultdict(int)

    def record(self, template: str, latency_ms: float, sla_p95_ms: int) -> bool:
        self._latencies[template].append(latency_ms)
        if latency_ms > sla_p95_ms:
            self._breach_counts[template] += 1
            return True  # breached
        return False

    def stats(self, template: str) -> dict:
        data = self._latencies.get(template, [])
        if not data:
            return {"p50_ms": 0, "p95_ms": 0, "p99_ms": 0, "breach_rate": 0.0, "count": 0}
        sorted_data = sorted(data)
        n = len(sorted_data)
        return {
            "p50_ms": round(sorted_data[int(n * 0.50)], 1),
            "p95_ms": round(sorted_data[int(n * 0.95)], 1),
            "p99_ms": round(sorted_data[min(int(n * 0.99), n - 1)], 1),
            "breach_rate": round(self._breach_counts[template] / n, 4),
            "count": n,
        }
