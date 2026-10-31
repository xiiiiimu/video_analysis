skill_id: hook_analysis
version: 1.0.0

# Hook Analysis Skill

Goal: judge whether the first 3 to 5 seconds create a clear reason to keep watching.

Evidence window: only the opening window (default first 15 seconds) is provided. Opening frames are sampled every second
(reason=hook). Cite time-level refs such as `FRAME:T@00:00:02`, `OCR:T@00:00:00`, `ASR:T@00:00:01`.

Procedure:
- Check opening text, transcript, key frames, and timing evidence first.
- If visible text or transcript is missing, request frame text evidence.
- If opening frame evidence is missing, request key frame evidence.
- Scoring rubric: the system retrieves this dimension's scoring points from the knowledge base before every diagnosis (input field `rubric`). Judge against the relevant rubric items and cite them in `rubric_refs`; do not embed rules in this skill.
- Produce evidence gaps when required evidence is unavailable.
- When the opening shows product features but user benefit is ambiguous, request capability `value_delivery`.

Output constraints:
- Produce one grounded finding with confidence and evidence references.
- Do not include full knowledge corpus content in the finding.
- Do not call tools outside the agent allowed tool policy.
