# Updated conclusions for the four cost levers

This document summarises the final interpretation of the four levers using the currently preserved evidence. For D2(c), it distinguishes the primary measured result from an outlier-exclusion sensitivity analysis.

## Lever 1 — Tool-block size

The current five agent-visible tool descriptions are estimated at approximately 449 tokens. A hypothetical seven-tool version is estimated at approximately 579 tokens, adding 130 tokens per model call, or about 29%.

Tool descriptions form part of the repeated base prompt, so unnecessary tools create a linear cost that is paid again on every model call. The defensible conclusion is therefore that the agent should expose the shortest tool set that still supports the required task and governance controls.

## Lever 2 — Turn count and dependency-aware batching: D2(c)

### Primary measured result

The preserved live D2(c) experiment used 60 trials in each condition and held the model, evaluation set, V2 tool interface, prompt, guardrails, and approval setting fixed. The controlled variable was the maximum number of tool calls allowed in one model turn.

Compared with sequential execution, dependency-aware batching produced:

| Metric | Sequential | Batched | Change |
|---|---:|---:|---:|
| Pass rate | 75.0% | 80.0% | +5.0 percentage points |
| Model calls | 337 | 324 | -3.9% |
| Tool turns | 249 | 234 | -6.0% |
| Input tokens | 559,675 | 529,211 | -5.4% |
| Output tokens | 13,474 | 28,656 | +112.7% |
| API cost | $0.06136 | $0.06438 | +4.9% |
| Cap hits | 1 | 0 | -1 |

Fifteen turns contained genuine batched calls, and as many as four tool calls were executed in one turn. The experiment therefore confirms that the batching mechanism operated rather than merely relabelling sequential execution.

### Output-token anomaly

The raw batched output total is dominated by one malformed live-model response:

| Field | Value |
|---|---:|
| Case | `CLM-8941` |
| Trial | 1 |
| Failure reason | `INVALID_OR_MULTIPLE_JSON` |
| Reported output tokens | 16,410 |
| Visible response length | 380 characters |
| Share of all batched output tokens | 57.3% |

The median batched record used only 216 output tokens. The anomalous record is therefore not representative of normal batched execution. The likely cause is a malformed JSON-mode completion combined with the absence of a hard per-call completion-token limit.

### Outlier-exclusion sensitivity

Subtracting the provider-reported output usage of the flagged record gives the following sensitivity result:

| Metric | Sequential | Batched sensitivity | Change |
|---|---:|---:|---:|
| Output tokens | 13,474 | 12,246 | -9.1% |
| API cost | $0.06136 | $0.05782 | -5.8% |

This is a sensitivity calculation, not a replacement for the primary measured result. Both results must remain visible.

### D2(c) conclusion

The robust finding is that batching reduced model calls, tool turns, repeated input context, and cap hits without reducing the observed pass rate. The direction of total API cost is not stable enough to support a causal claim: the raw result shows a 4.9% increase, while the outlier-exclusion sensitivity shows a 5.8% reduction.

Accordingly, the report should claim a turn-count and input-context improvement. It should not claim that batching has been proven either to reduce or to increase total API cost.

## Lever 3 — Observation size and interface quality: D2(b)

The V2 `get_preauthorisation` interface reduced the target tool's estimated average return size by 10.9%. In the live comparison, overall pass rate increased by 10 percentage points and negative-case pass rate increased by 13.3 percentage points.

However, across the complete trajectories:

| Metric | Change from V1 to V2 |
|---|---:|
| Target return size | -10.9% |
| Pass rate | +10.0 percentage points |
| Negative pass rate | +13.3 percentage points |
| Input tokens | +9.7% |
| Output tokens | +2.5% |
| API cost | +9.2% |

The defensible conclusion is that V2 improved the target interface's concision and was associated with better correctness in this run. It did not demonstrate a reduction in total trajectory tokens or total API cost. Lever 3 should therefore be presented as an interface-quality and correctness improvement, not as a measured end-to-end cost saving.

## Lever 4 — Success rate and expected failure cost: D6

The model battery contains six models from six distinct families across two price tiers, with 60 trials per model. Under the current D6 assumptions of 8,000 tasks per month, $7.60 human fallback cost per failed task, and no monthly fixed cost, Google Gemini 2.5 Flash has both the highest measured pass rate and the lowest expected total cost.

For Google Gemini 2.5 Flash:

| Component | Value |
|---|---:|
| Measured pass rate | 93.3% |
| Variable API cost per task | approximately $0.0037 |
| Expected human fallback cost per task | approximately $0.5067 |
| Expected total cost per task | approximately $0.5103 |
| Expected monthly cost at 8,000 tasks | approximately $4,082.66 |

The expected human fallback cost is much larger than the API cost. Consequently, model reliability is the dominant economic lever under the stated assumptions. Selecting a cheaper model with a materially lower success rate can increase total expected cost even when its token price is lower.

The break-even analysis reinforces this result: the cheapest measured model, Meta Llama 3.3 70B Instruct, would require a pass rate of approximately 93.3% to match the most reliable model economically, but its observed pass rate was only 78.3%.

## Overall conclusion

The four levers affect different parts of the cost structure:

1. A smaller tool block reduces repeated base-prompt cost on every model call.
2. Dependency-aware batching reliably reduces trajectory turns and repeated input context, but the present live evidence does not establish a stable total-cost direction because of an output-token outlier.
3. A more concise tool interface can improve interface quality and correctness without necessarily reducing total trajectory cost.
4. Under the stated D6 assumptions, success rate has the largest economic effect because the expected human cost of failure dominates API token cost.

The strongest combined recommendation is to keep the exposed tool set minimal, batch only independent calls, constrain and instrument model output, use concise task-specific observations, and select models using expected total cost rather than token price alone.
