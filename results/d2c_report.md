# D2(c) Sequential vs Batched Tool Calls

- Backend: `scripted`
- Model: `google/gemini-2.5-flash-lite`
- Tool spec version: `v2`
- Autonomy: `confirm`
- Approved for write: `True`
- Sequential mode: `MAX_TOOL_CALLS_PER_TURN=1`
- Batched mode: `MAX_TOOL_CALLS_PER_TURN=None`
- Dependency rule: get_claim runs first; lookup_policy waits for get_claim and runs alone; check_coverage calls for claim lines may batch after policy gates pass; get_preauthorisation waits for coverage.requires_preauth; issue_decision_letter runs alone behind the autonomy gate.

| Metric | Sequential | Batched |
|---|---:|---:|
| `trials` | 60 | 60 |
| `pass_rate` | 1.0 | 1.0 |
| `negative_pass_rate` | 1.0 | 1.0 |
| `median_turns` | 4.0 | 4.0 |
| `worst_turns` | 7 | 5 |
| `tool_turns` | 250 | 229 |
| `model_calls` | 310 | 289 |
| `input_tokens` | 0 | 0 |
| `output_tokens` | 0 | 0 |
| `api_cost` | 0.0 | 0.0 |
| `max_tool_calls_in_one_turn` | 1 | 4 |
| `cap_hits` | 0 | 0 |

## Interpretation

The D2(c) controlled variable is the tool-call execution strategy. The sequential baseline allows at most one tool call per model turn with parallel execution disabled. The batched condition allows multiple independent tool calls in the same model turn with parallel execution enabled.

Correctness is checked by comparing pass rate across the same evaluation cases. A lower `tool_turns` or `model_calls` count in the batched run is the measured turn-collapse effect.

Scripted backend note: token and API cost fields are zero because no live model API is called.
