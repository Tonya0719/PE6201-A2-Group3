<<<<<<< HEAD
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
=======
# D0 — Why an Agent? · Problem A

> This file should be committed **before the first Agent-code commit**. It is the written pre-build reasoning for D0.

## D0(a) Place Problem A on the Class 4 ladder

### Task
Explain why Problem A belongs at **Rung 7: Agent**, rather than a simpler fixed workflow.

### Evidence already present in the supplied data

Problem A does not have one fixed number of steps:

- `CLM-8850` is a short ordinary claim with one consultation line.
- `CLM-8960` has four claim lines and therefore requires more line-level checks.
- `CLM-8861` contains procedure `27447`, whose procedure record says `requires_preauth=true`; this creates an extra lookup branch.
- `CLM-8910` has a lapsed policy and should stop early once that fact is established instead of continuing to price its three lines.
- `CLM-8925` exceeds the remaining annual limit and should also exit before unnecessary line-level work.

The key D0 argument is therefore not merely that the data vary. The **number and sequence of required steps vary by case**, and the next step can depend on a fact returned during the current run.

### Points to write in the final D0(a)

1. Briefly compare Rungs 1–6 with Rung 7.
2. Explain what the lower rungs could deliver and where they become too rigid for this task.
3. Use your own eval cases later to show genuine variation in turn count.
4. State the two Agent conditions:
   - steps are not fully known in advance;
   - each step receives ground truth from a tool / system of record.
5. Identify the **governance cliff**: retrieval is read-only; the first irreversible step is the gated local decision write.

## D0(b) When NOT to build an Agent

### Ground-truth test

Problem A has machine-speed ground truth because each decision-relevant fact can be checked against a local system of record:

| Question | Ground truth source |
|---|---|
| Which policy belongs to the member? | `members.json` |
| Is the policy active and inside its dates? | `policies.json` |
| How much annual limit remains? | `policies.json` |
| Is a procedure excluded? | `policies.json` + claim line code |
| Does a procedure require pre-authorisation? | `procedures.json` |
| Is a matching pre-authorisation valid on the service date? | `preauthorisations.json` |
| Is a required document attached? | `required_documents.json` + claim documents |
| Is the hospital panel / non-panel? | `hospitals.json` |
| Is the claim a duplicate of a decided claim? | `decided_claims.json` |

These records can contradict a model immediately. That is what makes an iterative Agent defensible here.

### Reliability arithmetic — fill after D4 and D7

Later, insert the measured values:

- `P` = end-to-end run pass rate from D4 / D5
- `T` = median turns from D7 instrumentation
- `s = P^(1/T)`

Use `s` diagnostically to discuss whether the main weakness is step quality or step count. Do not present it as a literal constant reliability for every step.

## D0(c) What good looks like

Draft five testable statements before Agent implementation. Suggested Problem A shape:

1. **Correct outcome.** The final `approve_in_principle`, `request_document`, or `escalate` outcome matches the authoritative records.
2. **Correct reason.** The run records the correct single trigger or exact missing item; reaching the right outcome for the wrong reason does not count as success.
3. **Traceable evidence.** Decision-relevant claims can be traced to specific policy, procedure, pre-authorisation, hospital, document, or claims-history records.
4. **Safe gated action.** The local decision write happens at most once and only after the configured autonomy gate is satisfied; if evidence is insufficient, the Agent asks or escalates rather than inventing facts.
5. **Bounded and efficient.** The run stops on decisive evidence, avoids pointless repeated calls, stays within step/budget limits, and is cheap enough to compare meaningfully with human handling cost.

These statements should later map directly to D3 guardrails, D4 evaluation checks, D6 cost evidence, and D7 failure analysis.
>>>>>>> 5bd9f6e092f1512df28d8169c82e5b4e456af3a3
