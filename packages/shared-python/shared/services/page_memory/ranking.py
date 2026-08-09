"""Deterministic, model-free ranking primitives for page retrieval."""

from __future__ import annotations

import math
import re
from collections.abc import Sequence

from shared.services.page_memory.contracts import PageMemoryContractError

_TOKEN_RE = re.compile(r"[^\W_]+", re.UNICODE)


def tokenize(value: str) -> tuple[str, ...]:
    return tuple(_TOKEN_RE.findall(value.casefold()))


def lexical_score(native_text: str, query: str) -> float:
    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.0
    text_tokens = set(tokenize(native_text))
    matched = sum(token in text_tokens for token in query_tokens)
    return matched / len(query_tokens)


def cosine_similarity(
    left: Sequence[float],
    right: Sequence[float],
) -> float:
    if len(left) != len(right) or not left:
        raise PageMemoryContractError("visual vectors must have the same dimension")
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0
    cosine = sum(a * b for a, b in zip(left, right, strict=True)) / (
        left_norm * right_norm
    )
    return max(0.0, min(1.0, cosine))


def weighted_score(
    *,
    lexical: float,
    visual: float,
    section_proximity: float = 0.0,
    adjacent_page: float = 0.0,
) -> float:
    return (
        lexical * 0.50
        + visual * 0.35
        + section_proximity * 0.10
        + adjacent_page * 0.05
    )


__all__ = ["cosine_similarity", "lexical_score", "tokenize", "weighted_score"]
