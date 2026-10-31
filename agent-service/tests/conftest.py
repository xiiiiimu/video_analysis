from __future__ import annotations

import pytest

from agent_service.config import get_settings


def pytest_configure(config: pytest.Config) -> None:
  config.addinivalue_line("markers", "quality_v2: run the test with QUALITY_RULES=v2")
  config.addinivalue_line("markers", "rag: run the test with RAG_MODE=always (rubric retrieval before every diagnosis)")


@pytest.fixture(autouse=True)
def _quality_rules(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch):
  """
  编排 / harness 的既有测试用的是不带 quotes / polarity 的 mock 结论，固定在 v1 规则下运行；
  v2 质量规则由标记了 quality_v2 的测试单独覆盖。
  """
  version = "v2" if request.node.get_closest_marker("quality_v2") else "v1"
  monkeypatch.setenv("QUALITY_RULES", version)
  # 既有编排测试的假工具里没有 retrieve_knowledge；评分点检索由标记了 rag 的测试覆盖
  monkeypatch.setenv("RAG_MODE", "always" if request.node.get_closest_marker("rag") else "off")
  get_settings.cache_clear()
  yield
  get_settings.cache_clear()
