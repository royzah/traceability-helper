
import json, os, csv, pathlib, datetime as dt

outdir = pathlib.Path("dashboard/out")
outdir.mkdir(parents=True, exist_ok=True)

evt_path = os.environ.get("GITHUB_EVENT_PATH", "")
if not evt_path or not os.path.exists(evt_path):
    print("No event payload; skipping metrics export.")
    raise SystemExit(0)

with open(evt_path) as f:
    evt = json.load(f)

pr = evt.get("pull_request") or {}
created = pr.get("created_at")
closed = pr.get("closed_at")
merged = pr.get("merged_at")

def parse(ts):
    if not ts: return None
    return dt.datetime.fromisoformat(ts.replace("Z","+00:00"))

created_dt, closed_dt, merged_dt = map(parse, (created, closed, merged))
lead_time_hours = None
if created_dt and merged_dt:
    lead_time_hours = (merged_dt - created_dt).total_seconds() / 3600.0

data = {
    "number": pr.get("number"),
    "state": pr.get("state"),
    "created_at": created,
    "merged_at": merged,
    "lead_time_hours": lead_time_hours,
}

# JSON
with open(outdir / "latest.json", "w") as jf:
    json.dump(data, jf, indent=2)

# CSV (append mode for accumulation)
csv_path = outdir / "history.csv"
exists = csv_path.exists()
with open(csv_path, "a", newline="") as cf:
    w = csv.DictWriter(cf, fieldnames=list(data.keys()))
    if not exists:
        w.writeheader()
    w.writerow(data)

print("Metrics exported to", outdir)
