# D2(c) Sequential vs Batched Tool Calls

- Backend: `live`
- Model: `meta-llama/llama-3.3-70b-instruct`
- Tool spec version: `v2`
- Autonomy: `confirm`
- Approved for write: `True`
- Sequential mode: `MAX_TOOL_CALLS_PER_TURN=1`
- Batched mode: `MAX_TOOL_CALLS_PER_TURN=None`
- Dependency rule: get_claim runs first; lookup_policy waits for get_claim and runs alone; check_coverage calls for claim lines may batch after policy gates pass; get_preauthorisation waits for coverage.requires_preauth; issue_decision_letter runs alone behind the autonomy gate.

| Metric | Sequential | Batched |
|---|---:|---:|
| `trials` | 60 | 60 |
| `pass_rate` | 0.75 | 0.8 |
| `negative_pass_rate` | 0.6333333333333333 | 0.6333333333333333 |
| `median_turns` | 4.0 | 4.0 |
| `worst_turns` | 7 | 5 |
| `tool_turns` | 249 | 234 |
| `model_calls` | 337 | 324 |
| `input_tokens` | 559675 | 529211 |
| `output_tokens` | 13474 | 28656 |
| `api_cost` | 0.06135709999999999 | 0.06438350000000002 |
| `total_tool_calls` | 249 | 260 |
| `avg_tool_calls_per_turn` | 1.0 | 1.1111111111111112 |
| `batched_turns` | 0 | 15 |
| `max_tool_calls_in_one_turn` | 1 | 4 |
| `cap_hits` | 1 | 0 |

## Interpretation

The D2(c) controlled variable is the tool-call execution strategy. The sequential baseline allows at most one tool call per model turn with parallel execution disabled. The batched condition allows multiple independent tool calls in the same model turn with parallel execution enabled.

Correctness is checked by comparing pass rate across the same evaluation cases. A lower `tool_turns` or `model_calls` count in the batched run is the measured turn-collapse effect.
