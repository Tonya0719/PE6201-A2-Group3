# Evaluation support files

`guardrail_cases.json` is for the **D3(b) guardrail checklist**, not the D4 business evaluation set.

The D4 evaluation cases themselves live in the Problem A fixture data (`data_A/claims.json`) and are labelled in `expected_outcomes_A.json`. When the team adds cases, extend the generator and the same answer key rather than creating a second truth set.

If the team uses an LLM-as-judge for any judgement checks, keep its fixed grading instructions in `judgement_prompt.txt` and record the judge model in the results.
