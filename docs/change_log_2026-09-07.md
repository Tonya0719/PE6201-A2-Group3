# Change Log - 2026-09-07

## 中文改动记录

今天主要完成了 A2 项目的架构整理和 D2(c) 实验支持。

### 1. 架构重构

按照 lecturer 的 A2 架构要求，把原来混在一起的职责拆开：

```text
src/
- prompt.py
- agent_core.py
- harness.py
- evaluation.py
- tools.py
- guardrails.py
- backends.py
- config.py
```

具体改动：

- 新增 `src/prompt.py`
  - 从 `agent_core.py` 移出所有 system prompt 内容
  - 保留 `build_system_prompt(tool_specs: str) -> str`
  - prompt 语义不变

- 更新 `src/agent_core.py`
  - 只保留单个 claim 的 ReAct runtime
  - 负责 model call、tool orchestration、guardrail、gated action、token/cost accounting
  - 通过 `from src.prompt import build_system_prompt` 使用 prompt

- 新增 `src/harness.py`
  - 放 evaluation running / grading / aggregation
  - 包含 `run_evaluation(...)`
  - 包含 `grade_run(...)`
  - 包含 `summarize_results(...)`

- 简化 `src/evaluation.py`
  - 只保留 evaluation data helpers
  - 负责 expected outcomes、case IDs、negative case 判断等
  - 不再包含 agent running / grading / summary 逻辑

- 更新 `run_eval.py`
  - 改为从 `src.harness` 导入：

    ```python
    from src.harness import run_evaluation, summarize_results
    ```

  - 保持 marker-facing D5(a) 入口
  - 默认 scripted backend
  - 不需要 API key / network
  - 输出到 `results/results.json`

### 2. D2(c) sequential vs batched 支持

根据 PDF 要求，D2(c) 要展示：

```text
一个 turn 一个 tool call
vs
一个 turn 多个 independent tool calls
```

所以新增配置：

```python
MAX_TOOL_CALLS_PER_TURN = None
```

含义：

```text
None = batched mode
1    = sequential baseline
```

相关改动：

- 更新 `src/config.py`
  - 新增 `MAX_TOOL_CALLS_PER_TURN`
  - 保留 `PARALLEL_ENABLED`
  - 明确 `PARALLEL_ENABLED` 只是物理并发执行，不是 D2(c) 主变量

- 更新 `src/agent_core.py`
  - 新增每轮 tool call 限制逻辑
  - 当 `MAX_TOOL_CALLS_PER_TURN=1` 时，每个 model turn 最多执行一个 tool call
  - 剩余 tool calls 会被 defer
  - 不改变业务逻辑

- 更新 `src/harness.py`
  - 新增 `run_d2c_comparison(...)`
  - 新增 `print_d2c_report(...)`
  - 新增 `save_d2c_comparison(...)`
  - 新增 `write_d2c_report(...)`
  - 可比较 sequential 和 batched 的 pass rate、turns、model calls、tokens、cost、cap hits 等指标

### 3. D2(c) 独立入口

新增：

```text
run_d2c.py
```

用法：

```bash
python run_d2c.py
```

默认行为：

- 使用 scripted backend
- 跑完整 D2(c) comparison
- 打印 summary table
- 保存完整 JSON evidence
- 保存 Markdown report summary

输出文件：

```text
results/d2c_comparison.json
results/d2c_report.md
```

也可以只跑指定 case：

```bash
python run_d2c.py --case CLM-8960
```

跑 live token/cost evidence：

```bash
python run_d2c.py --backend live --case CLM-8960
```

### 4. Notebook / CLI 更新

- 更新 `A2_Agent_System.py`
  - 新增 `--d2c`
  - 新增 `--d2c-case`
  - 新增 `--credits`
  - `--sequential` 现在对应 `MAX_TOOL_CALLS_PER_TURN=1`

- 更新 `A2_Agent_System.ipynb`
  - 同步新的模块结构
  - 更新 imports
  - 更新 D2(c) 单元
  - 使用 `run_d2c_comparison(...)`

### 5. OpenRouter credits helper

新增函数：

```python
from src.backends import get_openrouter_credit_balance
```

也可以命令行查看：

```bash
python A2_Agent_System.py --credits
```

返回：

```json
{
  "total_credits": "...",
  "total_usage": "...",
  "remaining_credits": "..."
}
```

### 6. 验证结果

已验证：

```bash
python run_eval.py
```

结果：

```text
trials: 33
pass_rate: 1.0
negative_trials: 27
negative_pass_rate: 1.0
median_turns: 3
worst_turns: 5
cap_hits: 0
```

已验证：

```bash
python run_d2c.py --case CLM-8960 --no-progress
```

结果：

```text
sequential:
tool_turns = 7
model_calls = 8

batched:
tool_turns = 4
model_calls = 5

pass_rate unchanged = 1.0
```

## English Change Log

Today's changes focused on aligning the A2 codebase with the lecturer's architecture and adding proper D2(c) sequential-vs-batched measurement support.

### 1. Architecture Refactor

The codebase was reorganised into the required structure:

```text
src/
- prompt.py
- agent_core.py
- harness.py
- evaluation.py
- tools.py
- guardrails.py
- backends.py
- config.py
```

Changes made:

- Added `src/prompt.py`
  - Moved all system prompt content out of `agent_core.py`
  - Exposes `build_system_prompt(tool_specs: str) -> str`
  - Prompt semantics were preserved

- Updated `src/agent_core.py`
  - Now focuses only on running one claim through the ReAct loop
  - Keeps model calls, tool orchestration, guardrails, gated action handling, and token/cost accounting
  - Imports prompt via `from src.prompt import build_system_prompt`

- Added `src/harness.py`
  - Owns evaluation execution, grading, and aggregation
  - Contains `run_evaluation(...)`, `grade_run(...)`, and `summarize_results(...)`

- Simplified `src/evaluation.py`
  - Now only contains evaluation data helpers
  - Handles expected outcomes, case IDs, and negative-case identification
  - No longer runs or grades the agent

- Updated `run_eval.py`
  - Imports from `src.harness`
  - Remains the marker-facing D5(a) entry point
  - Forces scripted backend
  - Requires no API key or network
  - Writes output to `results/results.json`

### 2. D2(c) Sequential vs Batched Support

The PDF requirement for D2(c) is to compare:

```text
one tool call per turn
vs
multiple independent tool calls per turn
```

Added:

```python
MAX_TOOL_CALLS_PER_TURN = None
```

Meaning:

```text
None = batched mode
1    = sequential baseline
```

Related changes:

- Updated `src/config.py`
  - Added `MAX_TOOL_CALLS_PER_TURN`
  - Kept `PARALLEL_ENABLED`
  - Clarified that `PARALLEL_ENABLED` only controls physical concurrent execution inside an already-batched turn

- Updated `src/agent_core.py`
  - Added runtime tool-call limiting
  - When `MAX_TOOL_CALLS_PER_TURN=1`, only one tool call is executed per model turn
  - Deferred calls are not marked as executed
  - Business logic remains unchanged

- Updated `src/harness.py`
  - Added `run_d2c_comparison(...)`
  - Added `print_d2c_report(...)`
  - Added `save_d2c_comparison(...)`
  - Added `write_d2c_report(...)`
  - Reports pass rate, turns, model calls, tokens, cost, max tool calls in one turn, and cap hits

### 3. Dedicated D2(c) Entry Point

Added:

```text
run_d2c.py
```

Usage:

```bash
python run_d2c.py
```

Default behaviour:

- uses scripted backend
- runs the full D2(c) comparison
- prints a summary table
- saves full JSON evidence
- saves a Markdown report summary

Output files:

```text
results/d2c_comparison.json
results/d2c_report.md
```

Run selected cases:

```bash
python run_d2c.py --case CLM-8960
```

Run live token/cost evidence:

```bash
python run_d2c.py --backend live --case CLM-8960
```

### 4. Notebook / CLI Updates

- Updated `A2_Agent_System.py`
  - Added `--d2c`
  - Added `--d2c-case`
  - Added `--credits`
  - `--sequential` now maps to `MAX_TOOL_CALLS_PER_TURN=1`

- Updated `A2_Agent_System.ipynb`
  - Updated module structure notes
  - Updated imports
  - Updated D2(c) section
  - Uses `run_d2c_comparison(...)`

### 5. OpenRouter Credits Helper

Added:

```python
from src.backends import get_openrouter_credit_balance
```

CLI usage:

```bash
python A2_Agent_System.py --credits
```

Returns:

```json
{
  "total_credits": "...",
  "total_usage": "...",
  "remaining_credits": "..."
}
```

### 6. Validation

Validated:

```bash
python run_eval.py
```

Result:

```text
trials: 33
pass_rate: 1.0
negative_trials: 27
negative_pass_rate: 1.0
median_turns: 3
worst_turns: 5
cap_hits: 0
```

Validated:

```bash
python run_d2c.py --case CLM-8960 --no-progress
```

Result:

```text
sequential:
tool_turns = 7
model_calls = 8

batched:
tool_turns = 4
model_calls = 5

pass_rate unchanged = 1.0
```
