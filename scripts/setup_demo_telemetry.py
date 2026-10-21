
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Preserve the current September demo files.
for folder, filename in [
    ("metrics", "payment-api.json"),
    ("logs", "payment-api.log"),
    ("deployments", "payment-api.json"),
]:
    path = ROOT / "data" / folder / filename
    if path.exists():
        backup = path.with_name(path.name + ".sept-backup")
        if not backup.exists():
            shutil.copy2(path, backup)

metrics = [
    ("14:15:00", 178, 88, 0.07, 38, 51),
    ("14:20:00", 185, 95, 0.08, 38, 51),
    ("14:30:00", 190, 96, 0.08, 39, 51),
    ("14:35:00", 360, 240, 0.12, 40, 52),
    ("14:40:00", 740, 680, 0.20, 41, 52),
    ("14:45:00", 910, 910, 0.25, 41, 53),
    ("14:50:00", 1200, 1000, 0.31, 42, 53),
    ("14:55:00", 1460, 1120, 0.64, 41, 53),
]

observations = []
for timestamp, p95, db, error, cpu, memory in metrics:
    observations.append({
        "timestamp": f"2026-10-19T{timestamp}Z",
        "p50_ms": round(p95 * 0.45, 2),
        "p95_ms": p95,
        "p99_ms": round(p95 * 1.5, 2),
        "requests_per_second": 820,
        "error_rate_percent": error,
        "cpu_percent": cpu,
        "memory_percent": memory,
        "database_latency_ms": db,
    })

(ROOT / "data/metrics/payment-api.json").write_text(
    json.dumps({"service": "payment-api", "metrics": observations}, indent=2),
    encoding="utf-8",
)

logs = [
    "2026-10-19T14:34:10Z INFO payment-api deployment version=v2.4.1",
    "2026-10-19T14:38:22Z WARN request endpoint=/payments latency=740ms",
    "2026-10-19T14:41:07Z WARN database query latency=680ms query=payment_lookup",
    "2026-10-19T14:44:36Z WARN database query latency=910ms query=payment_lookup",
    "2026-10-19T14:48:12Z ERROR payment request timed out request_id=req-10482",
    "2026-10-19T14:52:49Z WARN database query latency=1340ms query=payment_lookup",
]
(ROOT / "data/logs/payment-api.log").write_text(
    "\n".join(logs) + "\n", encoding="utf-8"
)

deployment = {
    "service": "payment-api",
    "deployment_id": "deploy-2026-10-19-004",
    "version": "v2.4.1",
    "previous_version": "v2.4.0",
    "deployed_at": "2026-10-19T14:34:10Z",
    "status": "successful",
    "changes": [
        "Updated payment lookup query filtering",
        "Added transaction status validation",
        "Modified payment metadata retrieval",
    ],
}
(ROOT / "data/deployments/payment-api.json").write_text(
    json.dumps(deployment, indent=2), encoding="utf-8"
)

print("October 19 demo telemetry created.")
print("All values are simulated; they are not live production data.")
