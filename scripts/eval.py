"""Runs the 50 labelled queries once, then sweeps the guard threshold to pick it from data."""
import json, statistics
from app.graph import run

qs = json.load(open("data/test_queries.json"))
rows = []
for q in qs:
    o = run(q["query"], threshold=0.0)  # record raw scores, no blocking
    rows.append({"label": q["label"], "route": o["route"], "score": o.get("score", 0.0),
                 "has_answer": bool(o.get("answer")), "lat": o["latency_s"]})

print("route accuracy: %.0f%%" % (100 * sum(r["label"] == r["route"] for r in rows) / len(rows)))
print("avg latency: %.2fs" % statistics.mean(r["lat"] for r in rows))
answerable = [r for r in rows if r["label"] != "escalate"]
print("\nthreshold | resolved w/o human | ungrounded blocked")
for t in [0.5, 0.6, 0.7, 0.8, 0.9]:
    ok = sum(r["has_answer"] and r["route"] == r["label"] and r["score"] >= t for r in answerable)
    blocked = sum(r["has_answer"] and r["score"] < t for r in rows)
    print(f"   {t:.1f}    | {100*ok/len(answerable):5.1f}%            | {blocked}")
json.dump(rows, open("data/eval_scores.json", "w"), indent=1)
print("\nPick the highest threshold that keeps resolved% acceptable, set GUARD_THRESHOLD, paste proof line in README.")
