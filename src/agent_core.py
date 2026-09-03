"""Single-agent ReAct core and model seam.

Purpose
-------
Own the one Agent control loop used by every experiment. Scripted and live runs
must go through the same loop so comparisons remain meaningful.

Expected inputs
---------------
- A task / claim case identifier or task text.
- Selected backend and MODEL from config.
- Tool registry / descriptor version.
- Guardrail settings.
- Sequential or parallel tool-execution setting for D2(c).

Expected outputs
----------------
A run result containing at least:
- final structured outcome / decision record
- turn count
- ordered tool-call trace
- token input/output counts or measured usage
- estimated / measured cost
- whether a guardrail halted the run
- transcript / observations needed for debugging

Responsibilities
----------------
- Model interface seam: scripted vs live; only the live call should know the vendor/API.
- ReAct loop: model proposes -> tool(s) execute -> observations append -> repeat -> final.
- Support multiple tool calls in one turn.
- Execute tools in parallel only when the declared dependency rule allows it.
- Instrument every run for D6 and D7.

Non-responsibilities
--------------------
Do not embed the answer key or hard-code the Problem A expected outcome for each case.
Do not calculate evaluation pass rates or the D6 business cost model here.

A2 mapping: D1, D2(c), D5 model seam, instrumentation used by D6/D7.
"""
