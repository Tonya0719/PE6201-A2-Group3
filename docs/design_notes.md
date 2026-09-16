# Design Notes — Problem A

## D1 / D2(c) dependency rule

The implementation is one generic ReAct loop; paths vary with observations.

1. `get_claim` runs first.
2. If `duplicate_of` or hostile/injected narrative is decisive, no further read tool is allowed; the model must choose the gated decision action.
3. Otherwise `lookup_policy` runs alone because it produces `policy_id` and may itself create an early escalation.
4. After policy gates pass, `check_coverage` calls for separate lines are independent and may batch.
5. `get_preauthorisation` may run only after the returned coverage observation for that procedure says it is required. Independent PA lookups may batch with each other, but not with the coverage call that determines whether they are needed.
6. `issue_decision_letter` runs alone behind the autonomy gate.

Hospital-panel and required-document checks are deterministic helpers because they are fixed joins/comparisons rather than model-selected business actions.

## D2(a) tool boundary

Retained: `get_claim`, `lookup_policy`, `check_coverage`, `get_preauthorisation`, `issue_decision_letter`. Helpers not exposed as tools: exact duplicate match, hospital panel lookup, missing-document join, write de-duplication. The shortest-list argument is that each exposed read answers a distinct system-of-record question the model may need at runtime; deterministic joins are moved outside the loop.

## D2(b) controlled rewrite

Only `get_preauthorisation` changes between v1 and v2. v1 returns repeated member/procedure identifiers inside every record; v2 returns a compact bounded list of `{preauthorisation_id, valid_from, valid_to}` after coverage has established that PA is required. This isolates descriptor + return-shape quality as the experimental variable. Live pass/token measurements still need to be run and committed.

## D3 governance cliff

`issue_decision_letter` is the first irreversible step. `AUTONOMY="confirm"` is runtime configuration, never a model argument. The gate sits directly in front of the local write. Runtime controls also enforce step cap, budget ceiling, action de-duplication, active-case ID match, and no further reads after decisive duplicate/hostile intake evidence.

## D4 grading

Fixed fields (decision, trigger, exact missing item, gated-action count) are code-checked. A handful of prose reason/evidence records must also receive a human or different-model judgement check before final submission; the fixed rubric lives in `evals/judgement_prompt.txt`.

## Freeze rule

Once the final 30–50 case set is integrated and checked, all live battery members must run the same commit with the same v2 prompt/tool interface; only `MODEL` changes.
