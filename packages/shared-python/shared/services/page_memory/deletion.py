"""Fail-closed page deletion for immutable snapshots."""

from __future__ import annotations

from dataclasses import replace

from shared.services.page_memory.contracts import PageMemoryContractError
from shared.services.page_memory.index import _adjacent_ids, _snapshot_id
from shared.services.page_memory.models import PageMemorySnapshot


def delete_pages(
    snapshot: PageMemorySnapshot,
    *,
    page_ids: set[str],
) -> PageMemorySnapshot:
    """Return a new snapshot whose deleted pages cannot be retrieved."""

    if not page_ids:
        return snapshot
    known_page_ids = {page.page_id for page in snapshot.pages}
    unknown_page_ids = page_ids - known_page_ids
    if unknown_page_ids:
        raise PageMemoryContractError("cannot delete an unknown page_id")

    remaining = tuple(page for page in snapshot.pages if page.page_id not in page_ids)
    adjacency = _adjacent_ids(remaining)
    remaining = tuple(
        replace(page, adjacent_page_ids=adjacency[page.page_id]) for page in remaining
    )
    warnings = tuple(
        dict.fromkeys(
            snapshot.warnings
            + ("deleted_pages:" + ",".join(sorted(page_ids)),)
        )
    )
    return replace(
        snapshot,
        memory_snapshot_id=_snapshot_id(
            case_namespace=snapshot.case_namespace,
            source_id=snapshot.source_id,
            source_version_id=snapshot.source_version_id,
            native_sha256=snapshot.native_sha256,
            page_manifest_sha256=snapshot.page_manifest_sha256,
            pages=remaining,
            visual_embedding_artifact_sha256=snapshot.visual_embedding_artifact_sha256,
        ),
        pages=remaining,
        warnings=warnings,
    )


__all__ = ["delete_pages"]
