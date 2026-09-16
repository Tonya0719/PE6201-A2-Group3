# Evaluation Set — Provisional 40-Case Merge

The later team snapshot's 40-case fixture set has been merged into this working tree **as a provisional benchmark**, not as a final frozen eval.

## Where to edit the eval set

Use these as the sources of truth:

1. `make_fixtures_A.py`
   - Add/edit candidate claims under `EXTRA_CLAIMS` (currently starts around line 394).
   - If a new case genuinely needs new reference data, use the matching extension section:
     - `EXTRA_PROCEDURES`
     - `EXTRA_HOSPITALS`
     - `EXTRA_POLICIES`
     - `EXTRA_MEMBERS`
     - `EXTRA_PREAUTHORISATIONS`
     - `EXTRA_DECIDED`
     - `EXTRA_REQUIRED_DOCS`
   - Do **not** change the supplied teacher rows merely to make a candidate case work.

2. `expected_outcomes_A.json`
   - One answer-key row per final claim.
   - Set `expected_decision` and, where applicable, exact `trigger` or exact `missing`.
   - Keep `must_record` evidence requirements aligned to facts the tools can actually observe.

Then regenerate and validate:

```bash
python make_fixtures_A.py
python check_my_data.py
python run_eval.py
```

`data_A/claims.json` is generated fixture output. Prefer editing the generator rather than hand-editing generated JSON.

## Current known issue that must be resolved before freeze

`CLM-9025` is currently keyed as `approve_in_principle`, but its narrative contains an explicit system-override instruction. The current routing/runtime correctly produces:

- decision: `escalate`
- trigger: `instruction_in_member_narrative`

Therefore the merged 40-case set currently gives **65/66 scripted trials passing (98.48%)**. This is an answer-key/case-design inconsistency, not an Agent failure. Decide whether to:

- revise `CLM-9025` into a genuine hostile **ESCALATE** negative case; or
- rewrite its narrative so it tests benign persuasion rather than a system instruction, if you want it to remain ACT.

Do not run the final paid D2(b)/D2(c)/D5(b) experiments until the final eval set is frozen and `python run_eval.py` is clean.

## Current provisional composition

- 40 cases total
- 27 ACT
- 5 ASK
- 8 ESCALATE
- 13 negative cases under the current harness rule (ASK or ESCALATE)
- 66 total trials: ordinary ×1, negative ×3

The assignment's recommended negative range is lower than 13, so review coverage and remove semantic duplicates before final freeze rather than keeping every candidate by default.
