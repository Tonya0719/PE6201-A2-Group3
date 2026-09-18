# D2(c) previous live run — recovered aggregate analysis

## Evidence status

This analysis reconstructs the aggregate results of a previous D2(c) live run from a terminal screenshot. The corresponding record-level JSON was later overwritten.

The screenshot preserves the complete aggregate table, so overall deltas can be calculated. However, the lost JSON means that individual claim outcomes, failure reasons, paired case changes, and token outliers cannot be inspected retrospectively.

## Recovered results

| Metric | Sequential | Batched | Change |
|---|---:|---:|---:|
| Trials | 60 | 60 | equal |
| Pass rate | 73.33% | 83.33% | +10.00 percentage points |
| Negative pass rate | 63.33% | 66.67% | +3.33 percentage points |
| Median turns | 4 | 4 | no change |
| Worst turns | 7 | 6 | -1 |
| Tool turns | 258 | 236 | -22 (-8.53%) |
| Model calls | 343 | 327 | -16 (-4.66%) |
| Input tokens | 572,663 | 535,996 | -36,667 (-6.40%) |
| Output tokens | 125,088 | 13,171 | -111,917 (-89.47%) |
| API cost | $0.1073015 | $0.0588680 | -$0.0484335 (-45.14%) |
| Total tool calls | 258 | 261 | +3 (+1.16%) |
| Average tool calls per turn | 1.000 | 1.106 | +10.59% |
| Batched turns | 0 | 15 | +15 |
| Maximum calls in one turn | 1 | 4 | +3 |
| Step-cap hits | 2 | 0 | -2 |

## Did batching operate as intended?

Yes. The aggregate evidence shows that real batching occurred:

```text
batched_turns = 15
max_tool_calls_in_one_turn = 4
total_tool_calls = 261
tool_turns = 236
```

The batched condition completed 261 tool calls in 236 tool turns, demonstrating that some independent calls shared a model turn. In the sequential condition, 258 tool calls required exactly 258 tool turns.

The dependency-aware strategy therefore changed the trajectory structure as intended rather than merely relabelling sequential execution.

## Defensible efficiency findings

The following findings do not depend on the anomalous output-token total and are suitable as the primary D2(c) evidence:

- Tool turns fell by 8.53%.
- Model calls fell by 4.66%.
- Input tokens fell by 6.40%.
- Worst-case turns fell from 7 to 6.
- Step-cap hits fell from 2 to 0.
- Fifteen turns contained genuine batched calls, with as many as four calls in one turn.

These changes are consistent with the expected mechanism: batching independent tool calls reduces round trips and reduces the amount of accumulated history re-sent in later model requests.

## Correctness findings and limitation

The aggregate pass counts were:

```text
Sequential: 44/60
Batched:    50/60
Difference: +6 passing trials
```

For negative cases:

```text
Sequential: 19/30
Batched:    20/30
Difference: +1 passing trial
```

This run did not show a correctness penalty from batching. It showed a 10-percentage-point higher overall pass rate in the batched condition.

Because this was one live-model run and the record-level JSON is unavailable, the result cannot establish that batching caused the improvement. It is no longer possible to identify which claims changed outcome, conduct a paired case analysis, or classify the relevant failures. The appropriate claim is therefore that the higher pass rate was **observed in this run**, not that batching has been proven to improve correctness by 10 percentage points.

## Output-token anomaly

The output-token totals are the principal concern:

```text
Sequential output tokens: 125,088
Batched output tokens:     13,171
```

Average output per model call was therefore:

```text
Sequential: 125,088 / 343 = approximately 365 tokens per call
Batched:     13,171 / 327 = approximately 40 tokens per call
```

The sequential average is approximately nine times the batched average. The sequential restriction can increase the number of short calls, but it does not plausibly explain a nine-fold increase in the average length of each call.

A likely explanation is one or more JSON-mode runaway completions. The live backend used JSON response format without a hard `max_completion_tokens` limit. A malformed or incomplete JSON response can therefore accumulate a large provider-reported completion count, potentially including stripped whitespace or other non-visible content. A similar pattern was observed directly in a later run. However, because this run's JSON was overwritten, the exact affected claim and the number of anomalous calls cannot be established. This explanation must be presented as a strong inference rather than a verified record-level diagnosis.

## Cost decomposition

Using the experiment's configured prices of $0.10 per million input tokens and $0.40 per million output tokens:

```text
Sequential input cost
= 572,663 × $0.10 / 1,000,000
= $0.0572663

Sequential output cost
= 125,088 × $0.40 / 1,000,000
= $0.0500352

Sequential total
= $0.1073015
```

```text
Batched input cost
= 535,996 × $0.10 / 1,000,000
= $0.0535996

Batched output cost
= 13,171 × $0.40 / 1,000,000
= $0.0052684

Batched total
= $0.0588680
```

The total measured saving was $0.0484335. Its components were:

```text
Input-cost saving:  $0.0036667
Output-cost saving: $0.0447668
```

Approximately 92.4% of the reported cost difference came from output tokens. Because the sequential output total is anomalous and cannot now be audited at record level, the measured 45.14% total-cost reduction should not be attributed confidently to batching.

The 6.40% reduction in measured input tokens is the more defensible cost-related finding.

## Recommended report wording

> In this live run, dependency-aware batching reduced tool turns by 8.5%, model calls by 4.7%, and input tokens by 6.4%, while the observed pass rate increased from 73.3% to 83.3%. The run also reported an 89.5% reduction in output tokens and a 45.1% reduction in API cost. However, the sequential output-token count was anomalously high and the overwritten record-level JSON prevents retrospective outlier diagnosis. We therefore treat the turn-count and input-token reductions as the defensible findings and do not attribute the full measured cost difference to batching.

## Final assessment

This recovered experiment supports the claim that dependency-aware batching reduced trajectory length and repeated input context without showing a correctness penalty. It does not provide reliable evidence that batching reduced total API cost by 45.14%, because that figure is dominated by an unauditable sequential output-token anomaly.

The run should be retained as contextual evidence, clearly labelled as reconstructed from the screenshot. The current preserved JSON run should remain the primary auditable D2(c) evidence.
