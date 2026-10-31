from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path


class SkillLoadError(RuntimeError):
  """Raised when an AgentRun cannot load its immutable Skill snapshot."""


@dataclass(frozen=True)
class SkillSnapshot:
  skill_id: str
  version: str
  content: str
  content_hash: str
  path: str

  def to_dict(self) -> dict[str, str]:
    return asdict(self)


class SkillLoader:
  def __init__(self, base_dir: Path | None = None) -> None:
    self._base_dir = base_dir or default_skills_dir()

  def load(self, *, agent_id: str, skill_id: str) -> SkillSnapshot:
    path = self._base_dir / skill_id / "skill.md"
    if not path.exists():
      raise SkillLoadError(f"Missing skill file agent_id={agent_id} skill_id={skill_id} path={path}")
    content = path.read_text(encoding="utf-8").strip()
    if not content:
      raise SkillLoadError(f"Empty skill file agent_id={agent_id} skill_id={skill_id} path={path}")
    parsed_id = _parse_field(content, "skill_id") or skill_id
    version = _parse_field(content, "version")
    if not version:
      raise SkillLoadError(f"Missing skill version agent_id={agent_id} skill_id={skill_id} path={path}")
    if parsed_id != skill_id:
      raise SkillLoadError(
        f"Skill id mismatch agent_id={agent_id} skill_id={skill_id} parsed_skill_id={parsed_id} path={path}"
      )
    return SkillSnapshot(
      skill_id=skill_id,
      version=version,
      content=content,
      content_hash=hashlib.sha256(content.encode("utf-8")).hexdigest(),
      path=str(path),
    )

  def load_many(self, bindings: dict[str, str]) -> dict[str, dict[str, str]]:
    return {
      agent_id: self.load(agent_id=agent_id, skill_id=skill_id).to_dict()
      for agent_id, skill_id in bindings.items()
    }


def default_skills_dir() -> Path:
  """
  Skill 目录：优先 SKILLS_DIR 环境变量；否则使用源码树里的 agent-service/skills（pip install -e 时有效）。

  改造前只用 ``Path(__file__).parents[3]``：Docker 里用 ``pip install .`` 安装后，
  __file__ 位于 site-packages，这个路径就指错了，每个任务都会 SkillLoadError。
  """
  from agent_service.config import get_settings

  configured = get_settings().skills_dir
  if configured:
    return Path(configured)
  return Path(__file__).resolve().parents[3] / "skills"


def _parse_field(content: str, field: str) -> str:
  prefix = f"{field}:"
  for line in content.splitlines():
    stripped = line.strip()
    if stripped.startswith(prefix):
      return stripped[len(prefix):].strip()
  return ""
