# telemetry.py

import csv
import os
from datetime import datetime

TELEMETRY_FILE = "telemetry.csv"
FIELDNAMES = [
    "timestamp",
    "pathway",
    "latency_ms",
    "tokens_in",
    "tokens_out",
    "cost_usd",
    "error",
]


def log_telemetry(
    pathway: str,
    latency_ms: int | None,
    tokens_in: int | None,
    tokens_out: int | None,
    cost: float | None,
    error: str | None,
) -> None:
    exists = os.path.exists(TELEMETRY_FILE)

    with open(TELEMETRY_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)

        if not exists:
            writer.writeheader()

        writer.writerow({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "pathway": pathway,
            "latency_ms": latency_ms,
            "tokens_in": tokens_in,
            "tokens_out": tokens_out,
            "cost_usd": cost,
            "error": error,
        })
