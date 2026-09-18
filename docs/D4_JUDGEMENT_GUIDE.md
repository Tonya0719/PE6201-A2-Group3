# D4 judgement check guide

## Purpose

The deterministic evaluation already checks fixed fields such as decision, trigger, missing item and gated-action count. D4 also requires a judgement check for prose fields whose quality cannot be established by exact comparison:

- whether the final reason is consistent with the structured outcome;
- whether cited evidence appears in the recorded tool trace;
- whether the response invents unsupported policy, medical or business facts;
- whether the explanation is specific enough to justify the first-response record.

The fixed rubric is `evals/judgement_prompt.txt`. The runner evaluates 12 records fixed before review: four approve, four request-document and four escalate cases, always using trial 1. The selection covers different tool paths and does not depend on the judgement outcome.

The source used for the final check is the preserved Google Gemini 2.5 Flash battery result. Do not edit that source JSON.

## Option 1: LLM-as-judge

Use a judge from a different model family from the source agent. The supplied default is OpenAI GPT-4o mini, while the source agent is Google Gemini 2.5 Flash.

Run from the project root:

```powershell
D:\software\anaconda3\envs\PE6201\python.exe run_judgement_review.py `
  --mode llm `
  --source results_organized\live\google__gemini-2_5-flash.json `
  --output-dir results_organized\judgement `
  --judge-model openai/gpt-4o-mini
```

The command requires the same OpenRouter key mechanism as the other live runners. It writes:

```text
results_organized/judgement/judgement_results_llm.json
results_organized/judgement/judgement_summary_llm.md
```

The JSON records the source model, judge model, fixed sample, rubric path, per-case verdict and reason, trace supplied to the judge, and judge token usage. The runner rejects a judge from the same provider family as the source model.

Before submission, inspect every LLM verdict manually for obvious grading errors. Do not replace deterministic checks with the LLM judgement; the two measurements answer different questions.

## Option 2: human review

Generate the template from the real Gemini records:

```powershell
D:\software\anaconda3\envs\PE6201\python.exe run_judgement_review.py `
  --mode human-template `
  --source results_organized\live\google__gemini-2_5-flash.json `
  --output-dir results_organized\judgement
```

This writes:

```text
results_organized/judgement/judgement_human_template.json
results_organized/judgement/judgement_rubric.txt
```

A real team member must then open the template and complete:

- `reviewer` with their real name;
- `review_date`;
- all four boolean checks for each record;
- `judgement_pass`, which is true only when all four checks are true;
- a short `review_comment` identifying the supporting trace fact or the defect.

Do not change the copied source fields, selected case IDs, reason, evidence or trace. The reviewer must verify cited identifiers, dates, policy status, exclusions, pre-authorisation windows and missing documents directly against the included trace.

After completing the file, validate it and generate the final evidence:

```powershell
D:\software\anaconda3\envs\PE6201\python.exe run_judgement_review.py `
  --mode validate-human `
  --template results_organized\judgement\judgement_human_template.json `
  --output-dir results_organized\judgement
```

This writes:

```text
results_organized/judgement/judgement_results_human.json
results_organized/judgement/judgement_summary_human.md
```

The validator refuses incomplete checks, missing reviewer information, missing comments, or a `judgement_pass` value inconsistent with the four checks.

## Which option to submit

Submit one completed method as the primary D4 judgement evidence. Human review is cheaper and explicitly permitted, but it must be genuinely completed by a team member. LLM-as-judge is reproducible and records token usage, but the judge must be a different family and its verdicts should be sanity-checked.

In either case, the report should state the method, source model, sample size, selection rule, reviewer or judge, review date, pass count, and at least one concrete failure example if any judgement record fails.

Do not report an unfilled human template as completed evidence.
