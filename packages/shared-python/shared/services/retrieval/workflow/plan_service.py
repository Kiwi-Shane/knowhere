"""Plan loading and creation for decomposed retrieval workflows."""

from __future__ import annotations

from loguru import logger

from shared.services.ai.llm_endpoint_policy import normalize_provider_endpoint
from shared.services.ai.llm_overrides import get_current_llm_overrides
from shared.services.retrieval.agentic.core.budget import BudgetLedger
from shared.services.retrieval.cache_service import (
    get_cached_workflow_plan,
    set_cached_workflow_plan,
)
from shared.services.retrieval.llm_adapter import LLMFn
from shared.services.retrieval.workflow.planner import QueryPlanner
from shared.services.retrieval.workflow.types import QueryPlan


def _build_workflow_cache_identity() -> dict[str, str | None]:
    config = get_current_llm_overrides()
    if config is None:
        return {
            "llm_text_model": None,
            "llm_vision_model": None,
            "llm_text_endpoint": None,
            "llm_vision_endpoint": None,
        }

    text_provider = config.text_effective()
    vision_provider = config.vision_effective()
    return {
        "llm_text_model": text_provider.model if text_provider is not None else None,
        "llm_vision_model": (
            vision_provider.model if vision_provider is not None else None
        ),
        "llm_text_endpoint": (
            normalize_provider_endpoint(text_provider.base_url)
            if text_provider is not None
            else None
        ),
        "llm_vision_endpoint": (
            normalize_provider_endpoint(vision_provider.base_url)
            if vision_provider is not None
            else None
        ),
    }


class WorkflowPlanService:
    async def load_or_create(
        self,
        *,
        user_id: str,
        namespace: str,
        query: str,
        top_k: int,
        chunk_types: set[str] | None = None,
        exclude_document_ids: list[str] | None = None,
        planner_llm: LLMFn | None,
        planner_ledger: BudgetLedger,
        max_steps: int,
        wallet_total: int,
        per_retrieve: int,
        corpus_total_docs: int,
        corpus_total_chunks: int,
    ) -> QueryPlan:
        cache_identity = _build_workflow_cache_identity()
        try:
            cached = await get_cached_workflow_plan(
                user_id=user_id,
                namespace=namespace,
                query=query,
                top_k=top_k,
                chunk_types=chunk_types,
                exclude_document_ids=exclude_document_ids,
                **cache_identity,
            )
            if cached:
                return QueryPlan.from_dict(cached, original_query=query)
        except Exception as exc:
            logger.warning(f"workflow plan cache read failed (ignored): {exc}")

        planner = QueryPlanner(
            llm_fn=planner_llm,
            planner_ledger=planner_ledger,
            max_steps=max_steps,
            total_budget=wallet_total,
            per_step_budget=per_retrieve,
        )
        plan = await planner.plan(
            query=query,
            corpus_total_docs=corpus_total_docs,
            corpus_total_chunks=corpus_total_chunks,
        )
        try:
            await set_cached_workflow_plan(
                user_id=user_id,
                namespace=namespace,
                query=query,
                top_k=top_k,
                chunk_types=chunk_types,
                exclude_document_ids=exclude_document_ids,
                **cache_identity,
                plan=plan.to_dict(),
            )
        except Exception as exc:
            logger.warning(f"workflow plan cache write failed (ignored): {exc}")
        return plan
