# D2(b) One-tool V1→V2 Controlled Rewrite

- Model held fixed: `meta-llama/llama-3.3-70b-instruct`
- Target tool: `get_preauthorisation`
- All other tool descriptors/implementations: unchanged
- Backend: `live`

## Main results

| Metric | V1 | V2 |
|---|---:|---:|
| Eval pass rate | 0.7166666666666667 | 0.8166666666666667 |
| Negative pass rate | 0.5 | 0.6333333333333333 |
| Model input tokens | 497985 | 546448 |
| Model output tokens | 12768 | 13089 |
| API cost | 0.053884259999999996 | 0.05883328000000001 |
| Full tool-spec chars | 1614 | 1796 |
| Full tool-spec est. tokens | 404 | 449 |
| Target descriptor chars | 355 | 537 |
| Target descriptor est. tokens | 89 | 135 |
| Preauth calls observed | 20 | 19 |
| Avg return chars/call | 139.95 | 124.57894736842105 |
| Avg estimated return tokens/call | 35.6 | 31.736842105263158 |
| Guardrail cases passed | 11/11 | 11/11 |

## Controlled descriptor change

- Target descriptor character change, V2−V1: `182`
- Target descriptor estimated-token change, V2−V1: `46`
- Target descriptor character percentage change: `51.267605633802816`
- Target descriptor estimated-token percentage change: `51.68539325842697`

## Measurement notes

Tool-return and descriptor token counts are approximations using `ceil(chars / 4)`.
Provider-reported model input/output token counts are stored separately and should be treated as the authoritative API usage.
Differences in total model tokens or API cost can also reflect different agent trajectories, even when the controlled interface change itself is smaller.
