from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

# 固定诊断 Skill；skill_key 用于 Agent Runtime，dimension 与 Java AnalysisDimensionEnum 对齐。
CORE_DIAGNOSIS_SKILLS = [
  {"skill_key": "hook_analysis", "dimension": "HOOK", "goal": "检查前 3-5 秒是否快速建立兴趣、价值预期或情绪张力。"},
  {
    "skill_key": "structure_rhythm_analysis",
    "dimension": "STRUCTURE_RHYTHM",
    "goal": "检查段落结构、节奏切换、过渡词与信息密度。",
  },
  {"skill_key": "value_delivery_analysis", "dimension": "VALUE_DELIVERY", "goal": "检查是否明确传达观众收益。"},
]

CORE_DIAGNOSIS_DIMENSIONS = [item["dimension"] for item in CORE_DIAGNOSIS_SKILLS]

EvaluationDecision = Literal["PASS", "RETRY_AGENT", "REPLAN", "FAILED"]
RuntimeStatus = Literal[
  "PLANNED",
  "RUNNING",
  "EVALUATING",
  "REFINING",
  "REPLANNING",
  "SYNTHESIZING",
  "COMPLETED",
  "COMPLETED_WITH_GAPS",
  "FAILED",
]
ReasoningStatus = Literal["FINAL", "NEED_TOOL", "RETRY", "FAILED"]
SkillStatus = Literal["COMPLETED", "FAILED"]


class DraftHypothesis(TypedDict, total=False):
  """Agent 推理草稿假设（非权威 Finding 实体）。"""

  skill_key: str
  skill_code: str
  dimension: str
  outcome: str
  observation: str
  finding_type: str
  reason: str
  question: str
  target_capability: str
  evidence_gap: dict[str, Any]
  handoff_rejected: dict[str, Any]
  difference_text: str
  hypothesis_text: str
  suggested_action: str
  target_frame_refs: list[str]
  reference_frame_refs: list[str]
  evidence_refs: list[str]
  video_evidence_refs: list[str]
  knowledge_evidence_refs: list[str]
  evidence_gaps: list[dict[str, Any]]
  handoff_requests: list[dict[str, Any]]
  counter_evidence: str
  confidence: float
  # 模型引用了但证据包里不存在的条目（已从 refs 中剔除，供 Evaluator 反馈）
  invalid_evidence_refs: list[str]
  # 回调整合后的结论记录答复来源
  handoff_answer: dict[str, Any]
  # 部分完成时，因系统故障补位的 ABSTAIN
  system_failure: bool
  # quality rules v2
  polarity: str  # GAP / STRENGTH / PARITY
  quotes: list[dict[str, str]]  # 模型逐字摘抄的原文 [{ref, text}]
  grounded_quotes: list[dict[str, str]]  # 校验通过（在证据中真实存在）的原文
  quote_issues: list[str]
  cited_refs: list[str]  # 模型自己引用的条目（不含系统自动补充的视频级引用）
  priority: str  # 合成后分配：P0 / P1 / P2
  target_score: float | None  # 模型给目标在本维度的打分（1~5）
  reference_scores: dict[str, float]  # 模型给每个参考视频的打分，如 {"R1": 3}
  polarity_overridden: dict[str, Any]  # 模型写的方向与评分不一致、被系统按评分改写时的记录
  first_benefit_seconds: dict[str, float | None]  # VALUE：每个视频第一次说出观众收益的秒数（T / R1 ...）
  # RAG 评分点：模型声明的依据 / 本次检索到的全部评分点 / 模型引用了但没检索到的
  rubric_refs: list[str]
  retrieved_rubric_refs: list[str]
  invalid_rubric_refs: list[str]
  # 用户评分标准：分给本维度的条目 id、模型的逐条回应、缺少回应的条目
  assigned_criteria_ids: list[str]
  criteria_verdicts: list[dict[str, Any]]
  missing_criteria_ids: list[str]
  type_corrected: dict[str, Any]  # 系统按可计算的事实改写 finding_type 的记录
  downgraded: dict[str, Any]  # 打回次数用尽仍违反硬规则、被降级为 PARITY 的记录


class DiagnosisPlanItem(TypedDict, total=False):
  skill_key: str
  agent_id: str
  dimension: str
  goal: str
  required_evidence: list[str]
  skill_snapshot: dict[str, str]


class EvaluationResult(TypedDict, total=False):
  decision: EvaluationDecision
  reasons: list[str]
  affected_skills: list[str]
  evidence_gaps: list[dict[str, Any]]


class ReasoningDecision(TypedDict, total=False):
  status: ReasoningStatus
  reasoning_summary: str
  requested_evidence_type: str
  tool_input: dict[str, Any]
  finding: DraftHypothesis


class ToolResolution(TypedDict, total=False):
  evidence_type: str
  tool_name: str
  skill_key: str
  reason: str


class ToolObservation(TypedDict, total=False):
  observation_type: str
  tool_name: str
  payload: dict[str, Any]
  evidence_refs: list[str]
  knowledge_evidence_refs: list[str]
  retrieval_trace: dict[str, Any]
  success: bool
  error: str


class SkillExecutionResult(TypedDict, total=False):
  agent_id: str
  skill_code: str
  specialist_result: DraftHypothesis
  finding: DraftHypothesis
  observations: list[ToolObservation]
  evidence_refs: list[str]
  knowledge_evidence_refs: list[str]
  handoff_requests: list[dict[str, Any]]
  react_iterations: int
  status: SkillStatus
  error: str
  step_traces: list[dict[str, Any]]


class StepTrace(TypedDict, total=False):
  agent_id: str
  node: str
  skill: str
  step_type: str
  start: str
  end: str
  status: str
  iteration: int
  tool_calls: list[dict[str, Any]]
  error: str
  input_summary: str
  output_summary: str
  requested_evidence: str
  tool_name: str
  skill_code: str
  query: str
  knowledge_type: str
  retrieval_method: str
  bm25_count: int
  vector_count: int
  rrf_count: int
  rerank_count: int
  top_k: int
  latency: int
  selected_evidence_refs: list[str]
  skill_id: str
  skill_version: str
  skill_hash: str


class AgentGraphState(TypedDict):
  """
  AgentRuntimeState / DiagnosisState：一次 AgentRun 的运行上下文（草稿层）。

  禁止存放权威业务实体（Finding/VideoAsset/AnalysisJob 等完整对象）。
  Java 负责业务事实状态；Python 仅保存本次 Agent 编排、推理和工具调用状态。
  """

  run_id: str
  job_id: str
  skill_snapshots: dict[str, dict[str, str]]
  agent_states: dict[str, dict[str, Any]]
  agents_to_run: NotRequired[list[str]]
  handoff_requests: list[dict[str, Any]]
  active_handoff: NotRequired[dict[str, Any]]
  routing_history: list[dict[str, Any]]
  global_replan_count: int
  max_global_replans: int
  max_agent_handoffs: int
  plan: list[DiagnosisPlanItem]
  current_skill: NotRequired[str]
  evidence_refs: list[str]
  knowledge_evidence_refs: list[str]
  findings: list[DraftHypothesis]
  evidence_gaps: list[dict[str, Any]]
  tool_results: list[dict[str, Any]]
  evaluation_results: list[EvaluationResult]
  iteration_count: int
  react_iterations_by_skill: dict[str, int]
  current_observation: NotRequired[ToolObservation]
  tool_observations: list[ToolObservation]
  knowledge_observations: list[ToolObservation]
  retrieval_traces: list[dict[str, Any]]
  pending_tool_request: NotRequired[ToolResolution]
  skill_execution_status: dict[str, str]
  status: RuntimeStatus
  diagnosis_completion_status: NotRequired[str]
  step_traces: list[StepTrace]
  agent_trace: list[dict[str, Any]]
  result_version: int

  # 兼容旧字段：外部 Java callback 仍吃 draft_observations。
  # 交接回调：被询问方的答复单独保存，提问方在回调阶段整合
  handoff_answers: NotRequired[list[dict[str, Any]]]
  pending_integration: NotRequired[dict[str, Any] | None]
  dropped_handoffs: NotRequired[list[dict[str, Any]]]
  # Evaluator 给每个需要重试的 Skill 的具体原因（skill_key -> reasons）
  retry_feedback: NotRequired[dict[str, list[str]]]
  # Synthesizer 的跨维度合成结果
  synthesis: NotRequired[dict[str, Any]]

  draft_messages: list[dict[str, Any]]
  draft_observations: list[str]
  draft_hypotheses: list[DraftHypothesis]
  job_context: NotRequired[dict[str, Any]]
  evidence_pack: NotRequired[dict[str, Any]]
  skills_to_run: NotRequired[list[str]]
  next_action: str
  done: bool
  error: NotRequired[str]
