"""Deterministic code guardrails for the Agent.

Purpose
-------
Provide hard controls that remain effective regardless of model behaviour.

Expected inputs
---------------
Current run state such as turn number, cumulative cost/token use, action signature,
requested gated action, configured autonomy setting, and (for confirm mode) human approval.

Expected outputs
----------------
Allow / block / halt decisions plus a clear reason that can be logged in the trace.

Required controls
-----------------
- Step cap
- Budget ceiling
- Action de-duplication
- Autonomy gate: suggest / confirm / act

The gate belongs directly in front of the irreversible local write, not in front
of ordinary read-only retrieval.

A2 mapping: D3(a); tested by D3(b); one control may be removed for D7 Failure 1.
"""
