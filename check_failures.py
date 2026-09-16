import json
r = json.load(open("results/results.json"))
seen = set()
for rec in r["records"]:
    if not rec["passed"] and rec["case_id"] not in seen:
        seen.add(rec["case_id"])
        events = rec.get("guardrail_events", [])
        print(rec["case_id"], "| status:", rec.get("status"), "| failure_reason:", rec.get("failure_reason"), "| guardrail_events:", events)