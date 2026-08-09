"""Case-bound lexical, visual, and bounded-adjacency page retrieval."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from shared.services.page_memory.contracts import (
    PAGE_RETRIEVAL_CONTRACT_VERSION,
    PRECOMPUTED_VISUAL_BACKEND_ID,
    PageMemoryContractError,
    validate_vector,
)
from shared.services.page_memory.models import (
    PageMemoryPage,
    PageMemorySnapshot,
    PageRetrievalRequest,
    PageRetrievalResult,
)
from shared.services.page_memory.ranking import (
    cosine_similarity,
    lexical_score,
    weighted_score,
)


@dataclass(frozen=True)
class _Candidate:
    page: PageMemoryPage
    lexical: float
    visual: float
    section_proximity: float
    adjacent_page: float
    match_modes: tuple[str, ...]
    reason_codes: tuple[str, ...]

    @property
    def score(self) -> float:
        return weighted_score(
            lexical=self.lexical,
            visual=self.visual,
            section_proximity=self.section_proximity,
            adjacent_page=self.adjacent_page,
        )


def _section_proximity(page: PageMemoryPage, query: str) -> float:
    query_terms = {part.casefold() for part in query.split() if part.strip()}
    if not query_terms:
        return 0.0
    hint_terms = {
        part.casefold()
        for hint in page.coarse_section_hints
        for part in hint.split()
    }
    return 1.0 if query_terms & hint_terms else 0.0


def _result_id(request_id: str, snapshot_id: str, page_id: str) -> str:
    digest = hashlib.sha256(
        f"{request_id}|{snapshot_id}|{page_id}".encode("utf-8")
    ).hexdigest()
    return "result-" + digest


def _context_matches(
    request: PageRetrievalRequest,
    snapshot: PageMemorySnapshot,
) -> bool:
    if snapshot.invalidated:
        return False
    if request.case_namespace != snapshot.case_namespace:
        return False
    if request.source_id not in set(request.allowed_source_ids):
        return False
    return (
        request.source_id == snapshot.source_id
        and request.source_version_id == snapshot.source_version_id
        and request.native_sha256 == snapshot.native_sha256
    )


def _visual_context(
    request: PageRetrievalRequest,
    snapshot: PageMemorySnapshot,
) -> tuple[float, ...] | None:
    if request.visual_query is None:
        return None
    if snapshot.visual_index_status != "ready":
        raise PageMemoryContractError("visual index unavailable")
    if request.visual_backend_id != PRECOMPUTED_VISUAL_BACKEND_ID:
        raise PageMemoryContractError("visual backend identity mismatch")
    if request.visual_backend_id != snapshot.visual_embedding_backend_id:
        raise PageMemoryContractError("visual backend identity mismatch")
    query_vector = validate_vector(request.visual_query, "visual_query")
    dimensions = {
        len(page.visual_embedding)
        for page in snapshot.pages
        if page.visual_embedding is not None
    }
    if dimensions and len(query_vector) not in dimensions:
        raise PageMemoryContractError("visual query dimension mismatch")
    return query_vector


def _primary_candidates(
    request: PageRetrievalRequest,
    snapshot: PageMemorySnapshot,
    visual_query: tuple[float, ...] | None,
) -> list[_Candidate]:
    candidates: list[_Candidate] = []
    for page in snapshot.pages:
        lexical = lexical_score(page.native_text, request.query)
        visual = 0.0
        if visual_query is not None and page.visual_embedding is not None:
            visual = cosine_similarity(page.visual_embedding, visual_query)
        section_proximity = _section_proximity(page, request.query)
        if lexical <= 0.0 and visual <= 0.0:
            continue
        match_modes: list[str] = []
        reason_codes: list[str] = []
        if lexical > 0.0:
            match_modes.append("lexical")
            reason_codes.append("lexical_match")
        if visual > 0.0:
            match_modes.append("visual")
            reason_codes.append("visual_match")
        if section_proximity > 0.0:
            reason_codes.append("coarse_section_hint")
        candidates.append(
            _Candidate(
                page=page,
                lexical=lexical,
                visual=visual,
                section_proximity=section_proximity,
                adjacent_page=0.0,
                match_modes=tuple(match_modes),
                reason_codes=tuple(reason_codes),
            )
        )
    return sorted(
        candidates,
        key=lambda candidate: (
            -candidate.score,
            candidate.page.page_number,
            candidate.page.page_id,
        ),
    )


def _adjacent_candidates(
    primary: list[_Candidate],
    snapshot: PageMemorySnapshot,
    radius: int,
) -> list[_Candidate]:
    if radius == 0:
        return []
    page_by_id = {page.page_id: page for page in snapshot.pages}
    primary_ids = {candidate.page.page_id for candidate in primary}
    adjacent_ids: set[str] = set()
    for candidate in primary:
        current_ids = {candidate.page.page_id}
        for _ in range(radius):
            next_ids: set[str] = set()
            for current_id in current_ids:
                page = page_by_id[current_id]
                next_ids.update(page.adjacent_page_ids)
            adjacent_ids.update(next_ids - primary_ids)
            current_ids = next_ids
    return [
        _Candidate(
            page=page_by_id[page_id],
            lexical=0.0,
            visual=0.0,
            section_proximity=0.0,
            adjacent_page=1.0,
            match_modes=("adjacent_page",),
            reason_codes=("adjacent_to_ranked_page",),
        )
        for page_id in sorted(
            adjacent_ids,
            key=lambda item: (page_by_id[item].page_number, item),
        )
    ]


def _result(
    candidate: _Candidate,
    *,
    request: PageRetrievalRequest,
    snapshot: PageMemorySnapshot,
    rank: int,
) -> PageRetrievalResult:
    page = candidate.page
    return PageRetrievalResult(
        contract_version=PAGE_RETRIEVAL_CONTRACT_VERSION,
        request_id=request.request_id,
        result_id=_result_id(request.request_id, snapshot.memory_snapshot_id, page.page_id),
        memory_snapshot_id=snapshot.memory_snapshot_id,
        source_id=page.source_id,
        source_version_id=page.source_version_id,
        page_id=page.page_id,
        page_number=page.page_number,
        native_page_locator=f"{page.source_version_id}:p{page.page_number}",
        match_modes=candidate.match_modes,
        score_components={
            "lexical_score": candidate.lexical,
            "visual_score": candidate.visual,
            "section_proximity_score": candidate.section_proximity,
            "adjacent_page_score": candidate.adjacent_page,
            "weighted_score": candidate.score,
        },
        rank=rank,
        reason_codes=candidate.reason_codes,
        warnings=tuple(dict.fromkeys(snapshot.warnings + page.warnings)),
    )


def retrieve_pages(
    *,
    request: PageRetrievalRequest,
    snapshot: PageMemorySnapshot,
) -> tuple[PageRetrievalResult, ...]:
    """Return only current, allowlisted page leads with native locators."""

    if not _context_matches(request, snapshot):
        return ()
    visual_query = _visual_context(request, snapshot)
    primary = _primary_candidates(request, snapshot, visual_query)[: request.top_k]
    if not primary:
        return ()
    candidates = primary + _adjacent_candidates(
        primary, snapshot, request.adjacent_radius if request.expand_adjacent else 0
    )
    return tuple(
        _result(
            candidate,
            request=request,
            snapshot=snapshot,
            rank=rank,
        )
        for rank, candidate in enumerate(candidates, start=1)
    )


def classify_retrieval_disposition(
    results: tuple[PageRetrievalResult, ...],
) -> str:
    """Classify an empty result set without making an absence claim."""

    return "evidence_lead_only" if results else "no_result_found"


__all__ = [
    "classify_retrieval_disposition",
    "retrieve_pages",
]
