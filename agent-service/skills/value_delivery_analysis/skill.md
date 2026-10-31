skill_id: value_delivery_analysis
version: 1.0.0

# Value Delivery Analysis Skill

Goal: judge whether the video clearly communicates user benefit, use case, value proposition, and actionability.

Evidence window: the full analysis window (default first 120 seconds). Locate when the benefit is first stated
(second N in `speech` / `screenText`), whether it is demonstrated or proven later, and whether the ending (reason=end
frame, last segments) closes with a result or call to action. If `speechStatus` is not `ok`, judge from screen text only
and lower confidence. Cite refs such as `ASR:T@00:00:12`, `OCR:T@00:01:50`, `FRAME:T@00:01:59`.

Procedure:
- Check transcript, visible copy, metadata timing, and referenced evidence.
- If visible text or transcript is missing, request frame text evidence.
- If value timing needs grounding, request metadata evidence.
- Scoring rubric: the system retrieves this dimension's scoring points from the knowledge base before every diagnosis (input field `rubric`). Judge against the relevant rubric items and cite them in `rubric_refs`; do not embed rules in this skill.
- Produce evidence gaps when user benefit or actionability cannot be grounded.

Output constraints:
- Produce one grounded finding with confidence and evidence references.
- Focus on user value and actionability, not opening attention mechanics.
- Do not call tools outside the agent allowed tool policy.
