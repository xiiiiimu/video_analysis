skill_id: structure_rhythm_analysis
version: 1.0.0

# Structure Rhythm Analysis Skill

Goal: judge whether the video has understandable structure, pacing, segment progression, and rhythm changes.

Evidence window: the full analysis window (default first 120 seconds). Compare the precomputed `sceneStats`
(shot count, average / median / longest shot, shots under 2s, cuts per 30s) of target and references instead of
counting scenes yourself; use `scenes` only to locate a specific long or short shot. Use the timing of
`screenText` / `speech` segments (and step markers such as "第一步") for section boundaries.
Cite refs such as `METADATA:T`, `METADATA:R1`, `SCENE:T#3`, `OCR:R1@00:00:30`.

Procedure:
- Check key frames, scene metadata, transcript, and visible structure markers.
- If key frames are missing, request key frame evidence.
- If scene or rhythm metadata is missing, request metadata evidence.
- Scoring rubric: the system retrieves this dimension's scoring points from the knowledge base before every diagnosis (input field `rubric`). Judge against the relevant rubric items and cite them in `rubric_refs`; do not embed rules in this skill.
- Produce evidence gaps when structure or rhythm evidence is insufficient.

Output constraints:
- Produce one grounded finding with confidence and evidence references.
- Focus on organization and rhythm, not value proposition correctness.
- Do not call tools outside the agent allowed tool policy.
