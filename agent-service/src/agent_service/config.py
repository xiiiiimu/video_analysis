from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
  openai_api_key: str
  openai_model: str
  openai_base_url: str
  deepseek_api_key: str
  deepseek_model: str
  deepseek_base_url: str
  chat_api_key: str
  chat_model: str
  chat_base_url: str
  embedding_openai_api_key: str
  embedding_openai_model: str
  embedding_openai_base_url: str
  java_backend_base_url: str
  java_internal_api_key: str
  harness_max_turns: int
  harness_max_tokens: int
  harness_max_graph_steps: int
  harness_timeout_seconds: int
  max_react_iterations: int
  tool_timeout: float
  retrieval_top_k: int
  rerank_enabled: bool
  evaluator_retry_limit: int
  max_global_replans: int
  max_agent_handoffs: int
  java_http_max_retries: int
  java_http_retry_backoff_seconds: float
  agent_service_host: str
  agent_service_port: int
  # 只有显式打开时才允许 mock LLM（测试 / 演示）。生产缺 Key 直接失败，避免假结论落库。
  llm_mock: bool
  llm_timeout_seconds: float
  # Skill 文件目录；Docker 里由 SKILLS_DIR 指定，不再依赖源码相对路径
  skills_dir: str
  # 任务执行：进程内有界并发 + 按 job_id 去重
  max_concurrent_jobs: int
  # agent-service 自己的入站鉴权（Java -> Python）；为空表示不校验（仅本地开发）
  agent_service_api_key: str
  # 证据截断上限（字符），超出部分会在 payload 中标记 truncated
  evidence_text_limit: int
  skill_procedure_limit: int
  # v0.2 时间轴证据：每个视频送给模型的关键帧时间点 / 文字分段上限，单段文字字符上限
  evidence_max_keyframes: int = 60
  evidence_max_segments: int = 60
  evidence_segment_chars: int = 200
  # HOOK 专家只看开场这一段（秒），其余维度看完整分析窗口
  hook_window_seconds: int = 15
  # 诊断质量规则版本：v1=改造前行为（用于评测基线对比）；v2=区分差距/优势、强制原文引用、跨维度矛盾检查
  quality_rules: str = "v2"
  # 评分点检索（RAG）：always=每个维度诊断前必检索知识库里的评分点并要求结论注明依据；
  # off=只在任务显式要求知识时才检索（改造前的行为，用于评测对比）
  rag_mode: str = "always"
  # 提示词档位：full=带写死的概念定义（默认）；lite=去掉概念定义，只留流程和输出格式（评测 RAG 能否替代写死规则）
  prompt_profile: str = "full"
  rubric_top_k: int = 6
  # 内置评分点 md 目录；为空时用源码目录 agent-service/knowledge/rubric
  rubric_dir: str = ""


@lru_cache
def get_settings() -> Settings:
  openai_api_key = os.getenv("OPENAI_API_KEY", "")
  openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
  openai_base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
  deepseek_api_key = os.getenv("DEEPSEEK_API_KEY", "")
  deepseek_model = os.getenv("DEEPSEEK_MODEL", "deepseek-flash")
  deepseek_base_url = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
  chat_api_key = os.getenv("CHAT_API_KEY", "") or deepseek_api_key or openai_api_key
  chat_model = os.getenv("CHAT_MODEL", "") or (deepseek_model if deepseek_api_key else openai_model)
  chat_base_url = (
    os.getenv("CHAT_BASE_URL", "")
    or (deepseek_base_url if deepseek_api_key else openai_base_url)
  )
  return Settings(
    openai_api_key=openai_api_key,
    openai_model=openai_model,
    openai_base_url=openai_base_url,
    deepseek_api_key=deepseek_api_key,
    deepseek_model=deepseek_model,
    deepseek_base_url=deepseek_base_url,
    chat_api_key=chat_api_key,
    chat_model=chat_model,
    chat_base_url=chat_base_url,
    embedding_openai_api_key=os.getenv("EMBEDDING_OPENAI_API_KEY", "") or openai_api_key,
    embedding_openai_model=os.getenv("EMBEDDING_OPENAI_MODEL", "text-embedding-3-small"),
    embedding_openai_base_url=os.getenv("EMBEDDING_OPENAI_BASE_URL", "") or openai_base_url,
    java_backend_base_url=os.getenv("JAVA_BACKEND_BASE_URL", "http://localhost:8080"),
    java_internal_api_key=os.getenv("JAVA_INTERNAL_API_KEY", "change-me-in-production"),
    harness_max_turns=int(os.getenv("HARNESS_MAX_TURNS", "20")),
    # 改造前 token 从未被统计，32000 从没生效过；真实统计后先放宽，用真实任务的 usage 再校准
    # 分析窗口从 15 秒扩到 120 秒后，单次诊断输入约 8~10k token，按 6 次模型调用估算放宽到 200k
    harness_max_tokens=int(os.getenv("HARNESS_MAX_TOKENS", "200000")),
    harness_max_graph_steps=int(os.getenv("HARNESS_MAX_GRAPH_STEPS", "25")),
    harness_timeout_seconds=int(os.getenv("HARNESS_TIMEOUT_SECONDS", "300")),
    max_react_iterations=int(os.getenv("MAX_REACT_ITERATIONS", "3")),
    tool_timeout=float(os.getenv("TOOL_TIMEOUT_SECONDS", "30")),
    retrieval_top_k=int(os.getenv("RETRIEVAL_TOP_K", "5")),
    rerank_enabled=os.getenv("RERANK_ENABLED", "true").lower() in {"1", "true", "yes", "on"},
    evaluator_retry_limit=int(os.getenv("EVALUATOR_RETRY_LIMIT", "2")),
    max_global_replans=int(os.getenv("MAX_GLOBAL_REPLANS", "1")),
    max_agent_handoffs=int(os.getenv("MAX_AGENT_HANDOFFS", "2")),
    java_http_max_retries=int(os.getenv("JAVA_HTTP_MAX_RETRIES", "3")),
    java_http_retry_backoff_seconds=float(os.getenv("JAVA_HTTP_RETRY_BACKOFF_SECONDS", "0.5")),
    agent_service_host=os.getenv("AGENT_SERVICE_HOST", "0.0.0.0"),
    agent_service_port=int(os.getenv("AGENT_SERVICE_PORT", "8090")),
    llm_mock=_env_bool("LLM_MOCK", False),
    llm_timeout_seconds=float(os.getenv("LLM_TIMEOUT_SECONDS", "60")),
    skills_dir=os.getenv("SKILLS_DIR", ""),
    max_concurrent_jobs=int(os.getenv("MAX_CONCURRENT_JOBS", "4")),
    agent_service_api_key=os.getenv("AGENT_SERVICE_API_KEY", ""),
    evidence_text_limit=int(os.getenv("EVIDENCE_TEXT_LIMIT", "2000")),
    skill_procedure_limit=int(os.getenv("SKILL_PROCEDURE_LIMIT", "4000")),
    evidence_max_keyframes=int(os.getenv("EVIDENCE_MAX_KEYFRAMES", "60")),
    evidence_max_segments=int(os.getenv("EVIDENCE_MAX_SEGMENTS", "60")),
    evidence_segment_chars=int(os.getenv("EVIDENCE_SEGMENT_CHARS", "200")),
    hook_window_seconds=int(os.getenv("HOOK_WINDOW_SECONDS", "15")),
    quality_rules=os.getenv("QUALITY_RULES", "v2").strip().lower() or "v2",
    rag_mode=os.getenv("RAG_MODE", "always").strip().lower() or "always",
    prompt_profile=os.getenv("PROMPT_PROFILE", "full").strip().lower() or "full",
    rubric_top_k=int(os.getenv("RUBRIC_TOP_K", "6")),
    rubric_dir=os.getenv("RUBRIC_DIR", ""),
  )


def _env_bool(name: str, default: bool) -> bool:
  value = os.getenv(name)
  if value is None:
    return default
  return value.strip().lower() in {"1", "true", "yes", "on"}
