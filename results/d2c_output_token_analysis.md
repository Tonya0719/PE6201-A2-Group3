# D2(c) Output-token discrepancy analysis

## Question investigated

Why did the current live D2(c) run report more output tokens for the batched condition than for the sequential condition, even though batching reduced model calls and tool turns?

Evidence source: `results/d2c_comparison.json`.

## Headline finding

The higher batched output-token total is not a general consequence of the batching strategy. It is almost entirely caused by one anomalous live-model response:

| Field | Value |
|---|---:|
| Case | `CLM-8941` |
| Condition | batched |
| Trial | 1 |
| Status | failed |
| Failure reason | `INVALID_OR_MULTIPLE_JSON` |
| Reported output tokens | 16,410 |
| Visible response length | 380 characters |

This single record contributes approximately 57% of all output tokens reported for the batched condition.

## Distribution check

| Metric | Sequential | Batched |
|---|---:|---:|
| Records | 60 | 60 |
| Total output tokens | 13,474 | 28,656 |
| Mean output tokens per record | 224.6 | 477.6 |
| Median output tokens per record | 218 | 216 |
| 90th percentile | 335 | 277 |
| Maximum | 412 | 16,410 |

The median and 90th-percentile results do not show generally longer batched responses. The difference in the totals is caused by the single extreme maximum.

## What happened in `CLM-8941`

The visible response attempted to issue an escalation decision but was malformed JSON: the response ended without the final outer closing brace. The evaluator therefore recorded `INVALID_OR_MULTIPLE_JSON`.

The backend enables JSON response format but does not currently set `max_tokens` or `max_completion_tokens`. A plausible explanation is that, after producing an incomplete JSON object, the model continued generating whitespace or other non-visible completion content until the provider-side limit was reached. The backend applies `.strip()` before saving the response, so the stored response contains only 380 visible characters, while OpenRouter still reports and charges 16,410 completion tokens.

This is an inference from the mismatch between the short stored response, malformed JSON, and provider-reported token usage. It is not evidence that the normal batched calls require 16,410 tokens.

## Sensitivity calculation

Removing only this identified generation anomaly gives:

```text
Batched output tokens excluding CLM-8941 outlier
= 28,656 - 16,410
= 12,246

Sequential output tokens
= 13,474
```

Using the configured prices of $0.10 per million input tokens and $0.40 per million output tokens:

```text
Adjusted batched cost
= 535,996 × $0.10 / 1,000,000
  + 12,246 × $0.40 / 1,000,000
= approximately $0.05850

Sequential measured cost
= $0.06136
```

Under this sensitivity calculation, batching costs approximately 4.7% less than sequential execution. This adjusted number must not replace the measured result silently; both the measured total and the outlier-adjusted sensitivity should be disclosed.

## Assessment of the batching strategy

There is no clear evidence that the dependency-aware batching strategy is incorrectly designed. It batches independent `check_coverage` calls while preserving the required order for dependent operations:

1. `get_claim` runs first.
2. `lookup_policy` waits for the claim result.
3. Independent claim-line coverage checks may be batched.
4. `get_preauthorisation` waits until coverage establishes that pre-authorisation is required.
5. `issue_decision_letter` runs alone behind the autonomy gate.

The measured run still shows that batching reduced tool turns from 249 to 234 and input tokens from 559,675 to 535,996. The abnormal total output-token result is therefore better classified as a missing output-control/instrumentation issue than as a batching-policy failure.

## Recommended report wording

> Dependency-aware batching reduced tool turns and repeated input context. One batched live response produced malformed JSON and an anomalous provider-reported 16,410 completion tokens despite containing only 380 visible characters. Consequently, the unadjusted run did not demonstrate a total-cost saving. An outlier sensitivity calculation suggests a reduction of approximately 4.7%, but this is reported separately and is not treated as the primary measured result.

## Recommended engineering follow-up

1. Add a per-call `max_completion_tokens` limit, for example 512 tokens.
2. Log token usage for every individual model call, rather than only the accumulated per-case total.
3. Flag cases where provider-reported output tokens are disproportionate to the visible response length.
4. Classify such cases explicitly, for example as `TOKEN_USAGE_OUTLIER` or `JSON_MODE_RUNAWAY`.
5. Rerun the complete D2(c) live experiment with the output limit applied.
6. Preserve the original result as evidence and clearly label the new run and configuration rather than overwriting the provenance.

## Conclusion

The present evidence does not indicate a fundamental defect in the batched execution strategy. The apparent output-token disadvantage is dominated by one malformed live-model response and by the absence of a hard completion-token limit. The primary measured result should remain unchanged, while the outlier analysis should be disclosed as a sensitivity check.
