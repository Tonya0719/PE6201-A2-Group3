# D2(b) Controlled Rewrite — Final Scheme

## Target tool

`get_preauthorisation(member_id, procedure_code)`

Why this tool: it has the cleanest and largest legitimate observation-size reduction without changing business semantics. Preauthorisation lookup returns repeated identifiers in the naive shape, and these observations are re-sent on later turns. It therefore gives a measurable D2(b) observation-size lever while keeping the decision logic and source data unchanged.

## V1 descriptor / return shape

Descriptor intent: generic search after the model decides to use it.

```text
get_preauthorisation(member_id: str, procedure_code: str)
WHAT: Search preauthorisation records for this member and procedure.
INPUT: member_id and procedure_code.
RETURNS: {member_id, procedure_code,
          matching_records:[{preauthorisation_id, member_id,
                             procedure_code, valid_from, valid_to}]}
FAILS WHEN: malformed IDs; empty matching_records means none found.
IRREVERSIBLE? No.
```

Example V1 observation:

```json
{
  "member_id": "M-2214",
  "procedure_code": "62480",
  "matching_records": [
    {
      "preauthorisation_id": "PA-5521",
      "member_id": "M-2214",
      "procedure_code": "62480",
      "valid_from": "2026-08-01",
      "valid_to": "2026-10-31"
    }
  ]
}
```

## V2 descriptor / return shape

Descriptor intent: dependency-aware and compact. It explicitly says to use the tool only after `check_coverage` has returned `requires_preauth=true`.

```text
get_preauthorisation(member_id: str, procedure_code: str)
WHAT: Retrieve only the raw validity windows needed to judge a preauthorisation already known to be required.
INPUT: member_id from get_claim and a procedure_code for which
       check_coverage returned requires_preauth=true.
RETURNS: {procedure_code,
          records:[{preauthorisation_id, valid_from, valid_to}]}
FAILS WHEN: malformed IDs; empty records means none found.
IRREVERSIBLE? No.
```

Example V2 observation:

```json
{
  "procedure_code": "62480",
  "records": [
    {
      "preauthorisation_id": "PA-5521",
      "valid_from": "2026-08-01",
      "valid_to": "2026-10-31"
    }
  ]
}
```

## What is held fixed

- same model;
- same frozen eval set;
- same system prompt outside the one tool descriptor;
- same Agent loop;
- same source fixture data;
- same four other tool descriptors and implementations;
- same guardrails;
- same autonomy mode and execution strategy.

Only the target tool descriptor and returned observation shape change.

## What to report

Run:

```bash
python run_d2b_comparison.py --dry-run
python run_d2b_comparison.py
```

Report from `results/experiments/d2b_v1_vs_v2.json`:

- average tokens returned per `get_preauthorisation` call (the runner clearly labels the chars/4 model-agnostic estimate);
- evaluation pass rate;
- negative pass rate;
- guardrail cases passed;
- exact provider input/output tokens and API cost for the live full-eval run.

Current provisional 40-case dry-run demonstrates the intended size effect: V1 about 44.7 estimated return tokens/call vs V2 about 27.5. Do not use those as final report numbers until the eval set is frozen.
