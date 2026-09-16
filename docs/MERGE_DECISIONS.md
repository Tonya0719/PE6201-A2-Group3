# Later Snapshot → Freeze Baseline Merge Decisions

This working tree uses the cleaned Freeze Candidate as the code baseline and selectively recovers useful work from `PE6201-A2-Group3-main-ruinedbysam-14926.zip`.

## Merged because it improves the project without weakening the Freeze baseline

| Later-snapshot item | What was merged | Why |
|---|---|---|
| 40-case eval fixtures | `make_fixtures_A.py`, `data_A/claims.json`, `expected_outcomes_A.json` | Restores the larger D4 benchmark. Marked provisional until case review is complete. |
| D5(b) battery orchestration | `run_live_battery.py` | Recovered and cleaned so it changes model only and uses final v2 tool specs. |
| D6 cost runner | `run_cost_model.py` | Pure arithmetic over final live results; stale recompute-script wording removed. |
| D6 diagnostics | `analyze_reasoning.py`, `inspect_case.py`, `check_failures.py` | Useful analysis/debugging utilities; no runtime-control changes. |
| D3 evidence-readiness control | `check_evidence_complete()` + integration before write | Safe cherry-pick: blocks irreversible write before any `get_claim` evidence while preserving duplicate/hostile early exits. Added as an 11th deterministic guardrail case. |
| Historical evidence | copied under `results/recovered_later_snapshot/` | Preserves prior paid work without pretending it was produced by the current merged commit. |

## Explicitly NOT merged because it conflicts with stronger Freeze code

These require an explicit team decision before changing the baseline:

| Conflict | Later snapshot | Freeze baseline | Recommendation |
|---|---|---|---|
| Post-model budget enforcement | Missing | Re-checks budget after each model call and stops before any tool/write if the call itself crosses the ceiling | **Keep Freeze**. This is a stronger hard ceiling. |
| Active-case write binding | Missing | `check_case_id_match()` blocks `issue_decision_letter` targeting another claim | **Keep Freeze**. Strong poka-yoke. |
| Decisive-intake read block | Duplicate-only `check_no_retrieval_after_duplicate()` | General `check_no_retrieval_after_decisive_intake()` covers duplicate **and hostile member instructions** | **Keep Freeze** unless there is a grading reason to narrow it. |
| D2(b) tool specs | Multiple tool descriptors changed between old v1/v2 | Only `get_preauthorisation` changes descriptor + return shape | **Keep Freeze**. The later experiment is not a clean one-variable rewrite. |
| D7 Failure-2 runner | Written against duplicate-only guard function | Freeze has generalized decisive-intake guard | **Not merged yet**. Port the runner only after deciding which guard naming/semantics to freeze. |
| Later `src/agent_core.py` | Removes some Freeze controls | Includes post-call budget, case-id binding, generalized intake stop | **Do not overwrite Freeze**. |
| Later `src/guardrails.py` | Adds readiness check but loses Freeze controls | Broader control set | Readiness check was cherry-picked; the file itself was not overwritten. |
| Later `.env` | Contains a real API secret | Freeze excludes secrets | **Never merge**; rotate key if it was shared. |
| Later docs/requirements | Contain stale text/conflict markers | Freeze cleaned versions | **Keep Freeze**. |

## D7 consequence

The later snapshot contains valuable D7 failure evidence, but the Failure-2 replay imports a guard function that is intentionally different from the Freeze implementation. Historical result JSONs were preserved under `results/recovered_later_snapshot/failures/`; the runner itself is not treated as current until ported to the frozen guardrail API.

## Final D7 Failure 2 decision

The later snapshot's **experiment design and recorded live failure trace are retained**, but the obsolete duplicate-only guard is not restored. `demo_prompt_compliance_failure.py` has been ported to the final generalized runtime control `check_no_retrieval_after_decisive_intake()`. The before condition temporarily disables only that current guard; the after condition restores it. The replay now reproduces 4 tool turns before vs 2 after and records `READ_AFTER_DECISIVE_INTAKE_BLOCKED` with `decisive_reason=duplicate_claim`.
