"""Reporte de llamadas al LLM a partir de logs/llm_calls.jsonl.

Uso:
    uv run scripts/report.py [ruta/al/archivo.jsonl]
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

DEFAULT_PATH = Path("logs/llm_calls.jsonl")


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    path = Path(argv[0]) if argv else DEFAULT_PATH

    if not path.exists():
        print(f"Archivo no encontrado: {path}")
        return 1

    lines = path.read_text(encoding="utf-8").splitlines()
    events = [json.loads(line) for line in lines if line.strip()]

    if not events:
        print(f"El archivo está vacío: {path}")
        return 1

    print(f"Llamadas registradas: {len(events)}")

    # Calcula costo total en USD.
    total_cost = sum(float(event.get("cost_usd", event.get("cost", 0.0))) for event in events)

    # Latencia p50 y p95 solo para llamadas exitosas.
    succeeded = [
        float(event["latency_ms"])
        for event in events
        if event.get("success") is True and "latency_ms" in event
    ]
    if len(succeeded) == 1:
        p50 = p95 = succeeded[0]
    elif succeeded:
        p50 = statistics.quantiles(succeeded, n=100, method="inclusive")[49]
        p95 = statistics.quantiles(succeeded, n=100, method="inclusive")[94]
    else:
        p50 = p95 = 0.0

    # % de llamadas con fallback.
    fallback_events = sum(1 for event in events if event.get("fallback") is True)
    fallback_pct = (fallback_events / len(events)) * 100 if events else 0.0

    # Número de llamadas por proveedor.
    provider_counts = {}
    for event in events:
        provider = event.get("provider", "unknown")
        provider_counts[provider] = provider_counts.get(provider, 0) + 1

    print(f"Costo total (USD): ${total_cost:.4f}")
    print(f"Latencia p50: {p50:.2f} ms")
    print(f"Latencia p95: {p95:.2f} ms")
    print(f"Llamadas con fallback: {fallback_pct:.2f}%")
    print("Llamadas por proveedor:")
    for provider, count in sorted(provider_counts.items()):
        print(f"  - {provider}: {count}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
