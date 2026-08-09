"""Small in-memory storage boundary for case-private page snapshots."""

from __future__ import annotations

from dataclasses import replace

from shared.services.page_memory.contracts import PageMemoryContractError
from shared.services.page_memory.models import PageMemorySnapshot


class PageMemoryStore:
    """Store immutable snapshots and invalidate stale source versions."""

    def __init__(self) -> None:
        self._snapshots: dict[str, PageMemorySnapshot] = {}

    def put(self, snapshot: PageMemorySnapshot) -> PageMemorySnapshot:
        existing = self._snapshots.get(snapshot.memory_snapshot_id)
        if existing is not None and existing != snapshot:
            raise PageMemoryContractError("memory_snapshot_id collision")
        self._snapshots[snapshot.memory_snapshot_id] = snapshot
        return snapshot

    def get(
        self,
        memory_snapshot_id: str,
        *,
        case_namespace: str,
    ) -> PageMemorySnapshot | None:
        snapshot = self._snapshots.get(memory_snapshot_id)
        if snapshot is None or snapshot.invalidated:
            return None
        if snapshot.case_namespace != case_namespace:
            return None
        return snapshot

    def invalidate_snapshot(self, memory_snapshot_id: str) -> PageMemorySnapshot:
        snapshot = self._snapshots.get(memory_snapshot_id)
        if snapshot is None:
            raise PageMemoryContractError("memory snapshot was not found")
        invalidated = replace(
            snapshot,
            invalidated=True,
            warnings=tuple(dict.fromkeys(snapshot.warnings + ("snapshot_invalidated",))),
        )
        self._snapshots[memory_snapshot_id] = invalidated
        return invalidated

    def invalidate_source_version(
        self,
        *,
        case_namespace: str,
        source_id: str,
        source_version_id: str,
    ) -> tuple[str, ...]:
        invalidated_ids: list[str] = []
        for snapshot_id, snapshot in tuple(self._snapshots.items()):
            if (
                snapshot.case_namespace == case_namespace
                and snapshot.source_id == source_id
                and snapshot.source_version_id == source_version_id
                and not snapshot.invalidated
            ):
                self.invalidate_snapshot(snapshot_id)
                invalidated_ids.append(snapshot_id)
        return tuple(invalidated_ids)


__all__ = ["PageMemoryStore"]
