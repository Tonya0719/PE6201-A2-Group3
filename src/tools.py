"""Problem A tool layer and tool descriptors.

Purpose
-------
Implement the tools through which the Agent reads the local systems of record,
plus the single gated local write. Keep tool interfaces compact and explicit.

Expected inputs
---------------
IDs and fields that can be obtained from the claim or previous observations, such
as claim_id, member_id, policy_id, procedure_code, hospital_id, and service date.
Tools should read the teacher-provided / extended JSON fixtures rather than use
model knowledge.

Expected outputs
----------------
Small, structured observations containing only the facts needed by the Agent.
The gated write should append one structured local decision record and return a
confirmation; it should not perform a real-world action.

Design requirements
-------------------
- D2(a): shortest defensible tool set; justify every tool.
- D2(b): every tool needs the six required descriptor fields.
- Include at least two poka-yoke interface improvements.
- Preserve a v1 and v2 descriptor / return-shape version for one measured rewrite.
- Tools return facts; they should not hard-code the full Act / Ask / Escalate routing decision.

A2 mapping: D2(a), D2(b), gated action used by D3.
"""
