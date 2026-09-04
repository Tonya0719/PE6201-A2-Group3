# D0 — Why an Agent at All?

## D0(a) Ladder and workflow test

Problem A belongs on **Rung 7 — Agent** because the same control loop has different step counts for different claims and the next action is selected after reading authoritative observations.

Expected efficient paths under the current design:
- duplicate / hostile narrative: **2 model turns**;
- policy lapsed / outside dates / annual-limit exceeded: **3 model turns**;
- ordinary approve / request-document path: **4 model turns**.

The loop itself is not a hard-coded 2/3/4-turn workflow. It repeatedly asks the model for either one Action object (which may contain several independent tool calls) or Final. Early stopping depends on the evidence returned for the current claim.

Rungs 1–6 do not offer the same combination of variable step count and observation-driven next-step selection. The cost of Rung 7 is less predictable turns/tokens and a larger failure surface, which D3–D7 must measure and control.

### Two Agent conditions
1. Steps are not fully known in advance; the run may stop after Turn 1/2 evidence or continue to line verification.
2. Each stage is grounded in a fast system of record: claim/history, policy, coverage/procedure, preauthorisation, hospital and required-document fixtures.

### Governance cliff

All retrieval is read-only. The first world-changing action is `issue_decision_letter`. In A2 this is simulated as a local structured log, but it is still the gated action and remains behind the autonomy/write-dedup checks.

## D0(b) Ground-truth test and reliability diagnostic

The relevant systems of record can contradict the model within seconds:
- claim + duplicate history: `claims.json`, `decided_claims.json`;
- policy status/dates/limits/exclusions: `policies.json`;
- procedure coverage/preauth requirement: `procedures.json` + policy exclusions;
- preauthorisation records: `preauthorisations.json`;
- required documents: `required_documents.json`;
- hospital panel status: `hospitals.json`.

After D4/D7 produce measured whole-run pass rate `P` and median model turns `T`, calculate:

` s = P^(1/T) `

Use `s` only as a diagnostic for whether improvement should focus on per-step quality or on reducing turns. Steps are not independent and do not have equal reliability, so `s` is not a literal fixed probability.

## D0(c) Exactly five What Good Looks Like statements

**Commit these before the first Agent-code commit.**

1. The final ACT / ASK / ESCALATE outcome is consistent with the authoritative records for the claim.
2. The decisive reason is traceable to specific system-of-record evidence and, where required, the correct single trigger or named missing item.
3. The Agent never invents a system-of-record fact; unknown facts remain unknown until a real tool/helper observation supplies them.
4. The gated decision action executes at most once and only after the applicable facts for that path are established and the autonomy gate passes.
5. The run is bounded and avoids unnecessary work through evidence-based early exit and measured batching of independent calls.
