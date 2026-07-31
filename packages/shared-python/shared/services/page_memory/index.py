"""Build deterministic page-memory snapshots from declared page derivatives."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path

from shared.services.page_memory.contracts import (
    PAGE_MEMORY_CONTRACT_VERSION,
    PRECOMPUTED_VISUAL_BACKEND_ID,
    RANKING_WEIGHTS,
    PageMemoryContractError,
    canonical_sha256,
    ensure_no_reparse_root,
    is_valid_case_namespace,
    read_declared_file,
    required_text,
    validate_manifest,
    validate_vector,
    validated_sha256,
)
from shared.services.page_memory.models import PageMemoryPage, PageMemorySnapshot


def _coarse_section_hints(native_text: str) -> tuple[str, ...]:
    hints: list[str] = []
    for line in native_text.splitlines():
        candidate = " ".join(line.split())
        if not candidate or len(candidate) > 120:
            continue
        if candidate.endswith(":") or candidate.isupper() or len(candidate.split()) <= 8:
            if candidate not in hints:
                hints.append(candidate)
        if len(hints) >= 3:
            break
    return tuple(hints)


def _visual_artifact(
    visual_embeddings: Mapping[str, tuple[float, ...]],
) -> str | None:
    if not visual_embeddings:
        return None
    return canonical_sha256(
        {
            page_id: list(visual_embeddings[page_id])
            for page_id in sorted(visual_embeddings)
        }
    )


def _snapshot_id(
    *,
    case_namespace: str,
    source_id: str,
    source_version_id: str,
    native_sha256: str,
    page_manifest_sha256: str,
    pages: tuple[PageMemoryPage, ...],
    visual_embedding_artifact_sha256: str | None,
) -> str:
    identity = {
        "case_namespace": case_namespace,
        "source_id": source_id,
        "source_version_id": source_version_id,
        "native_sha256": native_sha256,
        "page_manifest_sha256": page_manifest_sha256,
        "pages": [
            {
                "page_id": page.page_id,
                "page_number": page.page_number,
                "render_sha256": page.render_sha256,
                "native_text_sha256": page.native_text_sha256,
            }
            for page in pages
        ],
        "visual_embedding_artifact_sha256": visual_embedding_artifact_sha256,
    }
    return "mem-" + canonical_sha256(identity)


def _validate_visual_embeddings(
    visual_embeddings: Mapping[str, object] | None,
    page_ids: set[str],
) -> dict[str, tuple[float, ...]]:
    if visual_embeddings is None:
        return {}
    if not isinstance(visual_embeddings, Mapping):
        raise PageMemoryContractError("visual_embeddings must be a mapping")
    unknown_page_ids = set(visual_embeddings) - page_ids
    if unknown_page_ids:
        raise PageMemoryContractError("visual_embeddings contains an unknown page_id")
    normalized = {
        page_id: validate_vector(vector, f"visual_embeddings[{page_id}]")
        for page_id, vector in visual_embeddings.items()
    }
    dimensions = {len(vector) for vector in normalized.values()}
    if len(dimensions) > 1:
        raise PageMemoryContractError("visual embeddings must have one dimension")
    return normalized


def _adjacent_ids(
    pages: tuple[PageMemoryPage, ...],
) -> dict[str, tuple[str, ...]]:
    ordered = sorted(pages, key=lambda page: page.page_number)
    adjacency: dict[str, tuple[str, ...]] = {}
    for index, page in enumerate(ordered):
        adjacent: list[str] = []
        if index > 0:
            adjacent.append(ordered[index - 1].page_id)
        if index + 1 < len(ordered):
            adjacent.append(ordered[index + 1].page_id)
        adjacency[page.page_id] = tuple(adjacent)
    return adjacency


def ingest_page_memory(
    *,
    case_namespace: str,
    manifest: Mapping[str, object],
    page_root: Path,
    visual_embeddings: Mapping[str, tuple[float, ...]] | None,
) -> PageMemorySnapshot:
    """Create a case-bound page-memory snapshot without model or network calls."""

    if not is_valid_case_namespace(case_namespace):
        raise PageMemoryContractError("case_namespace is invalid")
    if not isinstance(manifest, Mapping):
        raise PageMemoryContractError("manifest must be a mapping")
    normalized_pages = validate_manifest(manifest)
    root = ensure_no_reparse_root(Path(page_root))
    source_id = required_text(manifest.get("source_id"), "source_id")
    source_version_id = required_text(
        manifest.get("source_version_id"), "source_version_id"
    )
    native_sha256 = validated_sha256(manifest.get("native_sha256"), "native_sha256")
    page_manifest_sha256 = canonical_sha256(manifest)

    page_ids = {
        required_text(page["identity"]["page_id"], "page_id")
        for page in normalized_pages
    }
    normalized_visual_embeddings = _validate_visual_embeddings(
        visual_embeddings, page_ids
    )
    visual_embedding_artifact_sha256 = _visual_artifact(normalized_visual_embeddings)
    visual_backend_id = (
        PRECOMPUTED_VISUAL_BACKEND_ID if normalized_visual_embeddings else None
    )

    pages: list[PageMemoryPage] = []
    for raw_page in normalized_pages:
        identity = raw_page["identity"]
        page_id = required_text(identity["page_id"], "page_id")
        image_bytes = read_declared_file(
            page_root=root,
            relative_path=raw_page["image_relative_path"],
            expected_sha256=identity["render_sha256"],
            field_name="image_relative_path",
        )
        del image_bytes

        native_text_path = raw_page.get("native_text_relative_path")
        native_text_sha256 = raw_page.get("native_text_sha256")
        native_text = ""
        if native_text_path is not None:
            if native_text_sha256 is None:
                raise PageMemoryContractError(
                    "native text path requires native_text_sha256"
                )
            native_text_bytes = read_declared_file(
                page_root=root,
                relative_path=native_text_path,
                expected_sha256=native_text_sha256,
                field_name="native_text_relative_path",
            )
            try:
                native_text = native_text_bytes.decode("utf-8")
            except UnicodeDecodeError as error:
                raise PageMemoryContractError(
                    "native text must be valid UTF-8"
                ) from error

        native_text_status = required_text(
            raw_page["native_text_status"], "native_text_status"
        )
        lexical_status = "ready" if native_text.strip() else native_text_status
        page_warnings: list[str] = []
        if native_text_status != "available":
            page_warnings.append(f"native_text_{native_text_status}")
        pages.append(
            PageMemoryPage(
                page_id=page_id,
                source_id=source_id,
                source_version_id=source_version_id,
                page_number=identity["page_number"],
                page_manifest_sha256=page_manifest_sha256,
                render_sha256=identity["render_sha256"],
                native_text_sha256=native_text_sha256,
                image_relative_path=raw_page["image_relative_path"],
                native_text_relative_path=native_text_path,
                native_text=native_text,
                lexical_index_status=lexical_status,
                visual_index_status=(
                    "ready" if page_id in normalized_visual_embeddings else "disabled"
                ),
                visual_embedding_backend_id=(
                    visual_backend_id if page_id in normalized_visual_embeddings else None
                ),
                visual_embedding_artifact_sha256=(
                    visual_embedding_artifact_sha256
                    if page_id in normalized_visual_embeddings
                    else None
                ),
                visual_embedding=normalized_visual_embeddings.get(page_id),
                adjacent_page_ids=(),
                coarse_section_hints=_coarse_section_hints(native_text),
                warnings=tuple(page_warnings),
            )
        )

    ordered_pages = tuple(sorted(pages, key=lambda page: page.page_number))
    adjacency = _adjacent_ids(ordered_pages)
    finalized_pages = tuple(
        replace(page, adjacent_page_ids=adjacency[page.page_id])
        for page in ordered_pages
    )
    visual_status = "ready" if normalized_visual_embeddings else "disabled"
    warnings: list[str] = []
    if visual_embeddings is not None and not normalized_visual_embeddings:
        warnings.append("visual_index_empty")
    snapshot = PageMemorySnapshot(
        contract_version=PAGE_MEMORY_CONTRACT_VERSION,
        memory_snapshot_id=_snapshot_id(
            case_namespace=case_namespace,
            source_id=source_id,
            source_version_id=source_version_id,
            native_sha256=native_sha256,
            page_manifest_sha256=page_manifest_sha256,
            pages=finalized_pages,
            visual_embedding_artifact_sha256=visual_embedding_artifact_sha256,
        ),
        case_namespace=case_namespace.strip(),
        source_id=source_id,
        source_version_id=source_version_id,
        native_sha256=native_sha256,
        page_manifest_sha256=page_manifest_sha256,
        lexical_index_status="ready",
        visual_index_status=visual_status,
        visual_embedding_backend_id=visual_backend_id,
        visual_embedding_artifact_sha256=visual_embedding_artifact_sha256,
        pages=finalized_pages,
        ranking_weights=dict(RANKING_WEIGHTS),
        warnings=tuple(warnings),
    )
    return snapshot


__all__ = ["ingest_page_memory"]
