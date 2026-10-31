from __future__ import annotations

import math
import os
from dataclasses import dataclass
from typing import Protocol

from agent_service.config import get_settings


class EmbeddingProviderError(RuntimeError):
  """Raised when an embedding provider cannot produce vectors."""


class EmbeddingProvider(Protocol):
  provider_name: str
  model_name: str
  dimension: int

  def embed(self, text: str) -> list[float]:
    ...

  def embed_batch(self, texts: list[str]) -> list[list[float]]:
    ...


@dataclass(frozen=True)
class StaticEmbeddingProvider:
  """Test provider with caller-supplied vectors; not used as a production fallback."""

  vectors: dict[str, list[float]]
  provider_name: str = "static-test-embedding-provider"
  model_name: str = "static-test-vectors"

  @property
  def dimension(self) -> int:
    first = next(iter(self.vectors.values()), [])
    return len(first)

  def embed(self, text: str) -> list[float]:
    try:
      return list(self.vectors[text])
    except KeyError as exc:
      raise EmbeddingProviderError(f"No static embedding vector for text: {text}") from exc

  def embed_batch(self, texts: list[str]) -> list[list[float]]:
    return [self.embed(text) for text in texts]


class OpenAIEmbeddingProvider:
  """OpenAI embedding adapter loaded lazily so tests do not require network access."""

  def __init__(
    self,
    *,
    model: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
  ) -> None:
    settings = get_settings()
    self.provider_name = "openai"
    self.model_name = model or settings.embedding_openai_model
    self._dimension = 0
    key = api_key or settings.embedding_openai_api_key or os.getenv("OPENAI_API_KEY", "")
    embedding_base_url = base_url or settings.embedding_openai_base_url
    if not key:
      raise EmbeddingProviderError(
        "EMBEDDING_OPENAI_API_KEY or OPENAI_API_KEY is required for OpenAI embedding retrieval."
      )
    try:
      from langchain_openai import OpenAIEmbeddings
    except Exception as exc:  # pragma: no cover - environment dependent
      raise EmbeddingProviderError("langchain-openai is required for OpenAI embeddings.") from exc
    self._client = OpenAIEmbeddings(
      model=self.model_name,
      api_key=key,
      base_url=embedding_base_url or None,
    )

  @property
  def dimension(self) -> int:
    return self._dimension

  def embed(self, text: str) -> list[float]:
    vectors = self.embed_batch([text])
    return vectors[0]

  def embed_batch(self, texts: list[str]) -> list[list[float]]:
    try:
      vectors = [list(vector) for vector in self._client.embed_documents(texts)]
    except Exception as exc:  # pragma: no cover - network/provider dependent
      raise EmbeddingProviderError(f"Embedding provider failed: {exc}") from exc
    if vectors:
      self._dimension = len(vectors[0])
    return vectors


def cosine_similarity(left: list[float], right: list[float]) -> float:
  if len(left) != len(right):
    raise EmbeddingProviderError(
      f"Embedding dimension mismatch: left={len(left)} right={len(right)}"
    )
  left_norm = math.sqrt(sum(value * value for value in left))
  right_norm = math.sqrt(sum(value * value for value in right))
  if left_norm == 0 or right_norm == 0:
    return 0.0
  return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)
