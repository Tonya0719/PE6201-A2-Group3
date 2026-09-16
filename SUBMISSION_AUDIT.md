# PE6201 A2 Group 3 — Submission Audit

This audit compares the current project against the latest A2 brief, FAQ, document update notice, teacher scaffold and self-appraisal requirements included in `support/`.

## Executive result

The **core agent architecture is substantially complete**, but the repository snapshot is **not yet submission-complete** because the final D4 evaluation set, D2(b) measured rewrite evidence, D5(b) live battery evidence, D6 generated cost evidence, D7 two reproducible failure scripts/tables, judgement checks, and final submission artefacts are not all present in the repository.

The freeze candidate fixes clear code/hygiene defects without fabricating missing measurements.

## D0–D7 requirement matrix

| Area | Requirement | Repository / code evidence | Status | Remaining action |
|---|---|---|---|---|
| D0(a) | Place Problem A on Rung 7; compare Rungs 1–6; show variable steps, ground truth each step, governance cliff | `docs/D0_why_agent.md`; hand-written loop; variable early exits | Done | Final report should cite final eval cases/turn counts |
| D0(b) | Ground-truth test + reliability arithmetic `s=P^(1/T)` using measured P and median T | Ground-truth sources documented; arithmetic section is still a placeholder | Needs evidence | Insert final measured P/T after final battery/failure runs |
| D0(c) | Exactly five testable “What Good Looks Like” statements committed before Agent implementation | Five statements exist in initial D0 file; actual Agent implementation appears in later commit | Done | Preserve Git history and mention commit evidence if challenged |
| D1 | Single-agent, hand-written ReAct loop; several tools; multiple independent calls per turn; no framework-owned loop | `src/agent_core.py`, `src/tools.py` | Done | Keep architecture single-agent |
| D2(a) | Shortest defensible tool set; score every shipped tool against 3 questions; document one tool cut/not added | Five visible tools + helpers boundary exists | Partially done | Add explicit 3-question tool table + “tool not added/removed” evidence + tool-block token count |
| D2(b) | Six-field descriptor for every tool; ≥2 poka-yoke moves; one tool v1→v2 descriptor **and return shape**; same model; report tokens/call, pass rate, guardrail pass | Freeze candidate makes only `get_preauthorisation` differ v1/v2; v2 has six fields | Needs evidence | Run v1 and v2 on same cheap live model, final eval set; save result JSON/table; report two poka-yoke before→after moves |
| D2(c) | Parse/execute several independent tool calls; write dependency rule; same eval sequential vs batched; turns/tokens/cost; correctness unchanged | `run_d2c.py`; dependency rule; freeze run gives 100% vs 100% on current 15-case set, worst 7→5 tool turns | Partially done | Re-run on final eval set; add non-zero token/cost evidence from an appropriate measured run |
| D3(a) | Hard code controls: step cap, budget ceiling, action dedupe, explicit suggest/confirm/act; gate immediately before irreversible write | `src/guardrails.py`, `src/agent_core.py`; `AUTONOMY="confirm"` | Done | Defend `confirm` and cap=8 from measured distribution |
| D3(b) | ≥10 guardrail cases; each names wrong behaviour and observed result; ≥3 hostile free-text cases; scripted backend | `run_guardrails.py` + `results/guardrails/checklist.json`: 10/10, 3 hostile | Done | Keep machine-generated checklist in final repo |
| D4 | 30–50 eval cases; 6–10 negatives expected; clean state; ordinary 1 trial, negatives 3; outcome grading; code + judgement checks; pass rate with trial count | Harness has clean-state reset, trial policy and code checks; current repo has only 15 labelled cases | Missing | Curate/integrate final 30–50 case set; run `check_my_data.py`; add a handful of actual human/LLM judgement checks and record check type per case |
| D5(a) | Submitted default `BACKEND="scripted"`; end-to-end deterministic, no key/network; marker clone reproduces | Freeze config defaults scripted; `python run_eval.py` runs successfully | Partially done | Re-run after final D4 set is frozen; save final scripted result |
| D5(b) | Same final eval/v2 prompt; ≥3 live models, expected N−1; ≥2 price tiers; distinct families; one member/model; only MODEL differs | Live backend seam exists | Missing evidence | Commit per-model result files + model/member mapping + trial counts; do not rerun unless current evidence cannot be recovered |
| D6 | 3-layer cost-to-serve; measured D4/D5 inputs; ±10pp sensitivity; break-even; 4-lever ledger; state step/budget/monthly-user caps | `src/cost_analysis.py` implements formulas | Needs evidence | Generate final cost tables from live result files; include tool-block, D2(c), D2(b), success-rate before/after evidence and cap rationale |
| D7-1 | Reproduced loop-control failure as “working agent minus X”; scripted; instrumentation; distribution; before/after turns/tokens/cost/pass | No reproducible failure runner/table in repo | Missing | Add deterministic failure runner and before/after result file |
| D7-2 | Different layer (tool interface or prompt), also “working agent minus X”; scripted before/after; explain layer | Design discussion exists but no reproducible runner/table | Missing | Add second deterministic failure reproduction; avoid making it another loop-control failure |

## Code completeness vs teacher scaffold

The project has replacements/extensions for all core scaffold responsibilities:

- Scaffold `agent.py` → `src/agent_core.py`: implemented, larger hand-written loop with multi-call Actions, gate handling and instrumentation.
- Scaffold `tools.py` → `src/tools.py`: implemented Problem A tool layer, helper/tool split, descriptors and local write.
- Scaffold `guardrails.py` → `src/guardrails.py`: implemented hard controls.
- Scaffold `backends.py` → `src/backends.py`: scripted + one vendor-aware live function.
- Scaffold `harness.py` → `src/harness.py`: trial policy, code grading, summaries and D2(c) comparison.
- Scaffold `prompt.py` → `src/prompt.py`: final system protocol and dependency rules.
- Scaffold `run_eval.py` → root `run_eval.py`: marker-facing no-argument scripted runner.

The important missing scaffold-equivalent evidence is **not core loop code**: it is D7 reproduction tooling/results and final experimental evidence.

## Experiments audit

### D2(b)
Current snapshot had v1/v2 definitions, but v1 changed the entire tool block and the runtime return shape did not actually vary. That is too weak for the brief’s “take one tool” controlled experiment. The freeze candidate corrects the design so only `get_preauthorisation` changes descriptor + return shape. **Measurements must now be rerun**; old v1/v2 numbers should not be claimed for this corrected experiment.

### D2(c)
The original stored comparison covered only one case. The freeze candidate was rerun over the current 15-case set: sequential and batched both passed 100%; worst tool turns were 7 vs 5, and total tool turns 125 vs 113. Because the backend is scripted, token/cost values are zero. Final evidence must use the final locked eval set and include meaningful token/cost measurement.

### D3(b)
Freeze candidate adds a runnable ten-case deterministic checklist. It passes 10/10 and contains three hostile free-text cases. This is now reproducible by a marker.

### D4
Current repo: 15 cases, 33 scripted trials (6 ACT, 9 negative cases → 27 negative trials). This **does not meet** the required 30–50 case set. The Google Sheet candidates are not yet materialised into the repo fixtures/answer key. Also, `judgement_prompt.txt` existed but the harness did not actually apply a judgement check.

### D5(a)
Infrastructure passes. On current 15 cases, scripted run passes 33/33, median 3 tool turns, worst 5, cap hits 0. This is not the final headline until D4 is frozen.

### D5(b)
No machine-readable multi-model result set is present in this repo snapshot. External/shared results must be copied into the repo before submission and tied to the exact final commit.

### D6
Formula code exists, but no final cost result folder/table was present. Do not hand-enter results; generate them from the committed live battery files.

### D7
No two runnable “working agent minus X” reproductions are committed in the project snapshot. This is a submission blocker.

## Marker-pick risks / likely challenges

1. **Original ZIP contained a `.env` with a live API key.** It was not Git-tracked, but it was included in the uploaded working copy. The freeze candidate removes it. Rotate that key if it has been shared beyond your own machine.
2. **Merge-conflict markers** existed in README, CONTRIBUTIONS, D0/design notes, results README, `.gitignore`, `requirements.txt`, and the judgement prompt. Freeze candidate removes them.
3. **Submitted default backend** in the snapshot was `live`, even though `run_eval.py` forced scripted. The brief explicitly requires `BACKEND="scripted"` as submitted default. Freeze candidate fixes this.
4. **Budget guard** was checked only before a model call. Freeze candidate also stops before tool/write execution if the latest model call crosses the budget.
5. **Case-ID mismatch** on the gated write was not blocked. Freeze candidate adds a hard active-claim ID guard.
6. **Duplicate/hostile early exit** relied on prompt/nudge. Freeze candidate adds a runtime read-block after decisive intake evidence.
7. **D2(b) attribution** was not clean. Freeze candidate changes only one tool interface, but this invalidates old v1/v2 measurements for final reporting.
8. **D2(c) cap interaction:** step cap 7 caused the genuine sequential baseline to truncate legitimate long runs. Freeze candidate uses cap 8; full current scripted set then preserves correctness. This cap still needs final-set evidence.
9. **Puri CLM-3009 in the shared Sheet appears mislabelled** if retained: the Problem A routing rule says a narrative containing instructions aimed at the system must ESCALATE, not ACT. Re-label or drop it before final D4 integration.
10. **Negative-case count** should be reviewed after curation. The brief expects 6–10 in a 40-case set; blindly merging all current ASK/ESCALATE candidates will likely exceed that shape.
11. **Judgement check is not optional.** Having a prompt file is not the same as having judged records and recorded results.
12. **CONTRIBUTIONS.md is still a template.** Final version must contain real names, case IDs, model/v1 ownership and concrete evidence consistent with Git history.

## Submission requirements

Final archive must be named `PE6201_A2_[TeamID].zip` and contain the same code files as the public repository copy, plus:

1. Code repository copy with README, agent, tools, guardrails, 30–50 case eval set, harness, fixtures, machine-generated result tables and cost model.
2. Team report, maximum 2,000 prose words, in six required sections: Why an agent; Tool layer; Evidence; Cost; Two failures; What we would not deploy.
3. 5-minute recorded demo link; system running, one negative case live, headline numbers, every member speaks.
4. Completed team self-appraisal checked into submission folder.
5. `CONTRIBUTIONS.md` consistent with commit history.
6. Team Declaration file (required checkpoint document) should remain with team records/submission as instructed.
7. `check_my_data.py` must pass; supplied fixture records must remain unedited.

## Final freeze gate

Do **not** tag the repository as final until all of these are true:

- 30–50 final eval cases are materialised and labelled; negative count intentionally defended.
- `check_my_data.py` passes.
- scripted full run passes/reproduces from a fresh clone.
- judgement checks are completed and recorded.
- D2(b) v1/v2 live comparison rerun on corrected one-tool interface.
- D2(c) final-set sequential/batched evidence saved.
- six-family/N−1 live battery evidence is committed and tied to this exact commit.
- D6 tables generated from those results.
- D7 two scripted before/after failures reproduce.
- report/self-appraisal/contributions/video are final.
- no `.env`, API keys, merge markers, IDE caches or bytecode are in the submission copy.
