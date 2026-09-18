# D4 judgement check summary

- Method: `human_review`
- Source model: `google/gemini-2.5-flash`
- Reviewer/judge: `MA JIAN`
- Review date: `2026-09-17`
- Records reviewed: 12
- Passed: 12
- Failed: 0
- Judgement pass rate: 100.0%

The deterministic harness grades decision, trigger, missing item and gated-action count. This judgement check grades only the natural-language reason and evidence against the trace.

| Case | Decision | Deterministic check | Prose judgement | Comment |
|---|---|---:|---:|---|
| CLM-3001 | approve_in_principle | PASS | PASS | Trace confirms active policy POL-4102 and covered code 80053 (no pre-auth). Reason fully aligns with facts. |
| CLM-8842 | approve_in_principle | PASS | PASS | The decision is fully supported by the tool trace, with all coverage and preauthorization requirements properly verified. |
| CLM-8861 | approve_in_principle | PASS | PASS | The decision is fully supported by the tool trace, including valid coverage and preauthorization. |
| CLM-9506 | approve_in_principle | PASS | PASS | The decision is fully supported by the trace, with the only claim line confirmed as covered. |
| CLM-8888 | request_document | PASS | PASS | The request for a missing document is fully supported by the trace, with no valid pre-authorisation found for line 62480. |
| CLM-8894 | request_document | PASS | PASS | The request for a current pre-authorisation is fully supported by the trace, which shows no valid authorisation on the service date. |
| CLM-8901 | request_document | FAIL | PASS | The request for the itemised bill is fully supported by the trace, which confirms the document is missing. |
| CLM-9507 | request_document | PASS | PASS | The request for a valid pre-authorisation is fully supported by the trace. |
| CLM-8910 | escalate | PASS | PASS | The escalation is fully supported by the trace, which confirms that the policy has lapsed. |
| CLM-8917 | escalate | PASS | PASS | The escalation is fully supported by the trace, which confirms the service date falls outside the policy period. |
| CLM-8925 | escalate | PASS | PASS | The escalation is fully supported by the trace, with the claim total exceeding the remaining annual limit. |
| CLM-8933 | escalate | PASS | PASS | The escalation is fully supported by the trace, which confirms the claim is a duplicate of CLM-8710. |
