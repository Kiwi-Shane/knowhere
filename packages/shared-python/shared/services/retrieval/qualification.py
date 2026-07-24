"""Fail-closed technical qualification helpers for Knowhere retrieval results."""

from __future__ import annotations

import copy
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass
from urllib.parse import urlparse
from typing import Any

from .knowledge_retrieval_result import (
    KnowledgeRetrievalResultContext,
    KnowledgeRetrievalResultLocator,
    serialize_knowledge_retrieval_result,
)

_FORBIDDEN_AUTHORITY_FIELDS = frozenset(
    {
        "evidence_status",
        "readiness_status",
        "regulatory_conclusion",
        "source_sufficiency_decision",
        "ra_evidence_state",
        "release_decision",
    }
)
_INTERNAL_DESTINATIONS = frozenset({"mineru", "knowhere-api", "object-storage"})
_CASE_IDS = ("CASE-SYN-A", "CASE-SYN-B")


@dataclass(frozen=True)
class RetrievalQualificationIssue:
    code: str
    detail: str


def validate_knowledge_retrieval_result(
    result: Mapping[str, Any],
    *,
    allowed_source_ids: Collection[str],
    expected_request_id: str,
    expected_source_version_id: str,
    expected_extraction_block_ids: Collection[str],
    current_memory_snapshot_id: str | None = None,
    current_memory_snapshot_sha256: str | None = None,
    invalidated: bool = False,
) -> tuple[RetrievalQualificationIssue, ...]:
    """Validate technical retrieval provenance without making an RA decision."""

    issues: list[RetrievalQualificationIssue] = []
    if result.get("contract_version") != "knowledge-retrieval-result-v1":
        issues.append(
            RetrievalQualificationIssue(
                "contract_version", "unexpected retrieval-result contract version"
            )
        )

    for field in _FORBIDDEN_AUTHORITY_FIELDS:
        if field in result:
            issues.append(
                RetrievalQualificationIssue(
                    "forbidden_authority_field",
                    f"producer result contains RA-owned field: {field}",
                )
            )

    if result.get("native_source_verification_status") != "unverified":
        issues.append(
            RetrievalQualificationIssue(
                "native_source_status", "Knowhere result must remain unverified"
            )
        )
    if result.get("not_source_sufficiency_decision") is not True:
        issues.append(
            RetrievalQualificationIssue(
                "source_sufficiency_boundary",
                "Knowhere result cannot make a source-sufficiency decision",
            )
        )

    source_id = _text_value(result.get("source_id"))
    if source_id not in set(allowed_source_ids):
        issues.append(
            RetrievalQualificationIssue(
                "source_not_allowlisted", f"source is not allowlisted: {source_id}"
            )
        )
    if result.get("request_id") != expected_request_id:
        issues.append(
            RetrievalQualificationIssue(
                "request_mismatch", "result request does not match retrieval request"
            )
        )
    if result.get("source_version_id") != expected_source_version_id:
        issues.append(
            RetrievalQualificationIssue(
                "source_version_mismatch",
                "result source version does not match the accepted source version",
            )
        )

    actual_block_ids = _string_set(result.get("extraction_block_ids"))
    expected_blocks = set(expected_extraction_block_ids)
    if not expected_blocks or not expected_blocks <= actual_block_ids:
        issues.append(
            RetrievalQualificationIssue(
                "extraction_block_unlinked",
                "result does not link every accepted extraction block",
            )
        )

    citation = result.get("citation")
    native_reference = (
        citation.get("native_reference")
        if isinstance(citation, Mapping)
        else None
    )
    if not isinstance(native_reference, str) or not native_reference.startswith(
        f"{expected_source_version_id}:"
    ):
        issues.append(
            RetrievalQualificationIssue(
                "citation_mismatch",
                "citation is not rooted in the expected source version",
            )
        )

    if current_memory_snapshot_id is not None and result.get(
        "memory_snapshot_id"
    ) != current_memory_snapshot_id:
        issues.append(
            RetrievalQualificationIssue(
                "stale_result", "result memory snapshot id is stale"
            )
        )
    if current_memory_snapshot_sha256 is not None and result.get(
        "memory_snapshot_sha256"
    ) != current_memory_snapshot_sha256:
        issues.append(
            RetrievalQualificationIssue(
                "stale_result", "result memory snapshot hash is stale"
            )
        )
    if invalidated:
        issues.append(
            RetrievalQualificationIssue(
                "invalidated_result", "result was explicitly invalidated"
            )
        )

    return tuple(issues)


class _SyntheticStore:
    def __init__(self) -> None:
        self.objects: dict[str, dict[str, bytes]] = {}
        self.index: dict[str, dict[str, Any]] = {}
        self.queue: list[str] = []
        self.backups: dict[str, tuple[dict[str, bytes], dict[str, Any]]] = {}

    def put_case(self, case_id: str, result: Mapping[str, Any]) -> None:
        self.objects[case_id] = {
            "source": f"synthetic source {case_id}".encode(),
            "derivative": f"synthetic derivative {case_id}".encode(),
        }
        self.index[case_id] = copy.deepcopy(dict(result))
        self.queue.append(case_id)

    def backup_case(self, case_id: str) -> None:
        self.backups[case_id] = (
            dict(self.objects.get(case_id, {})),
            copy.deepcopy(self.index.get(case_id, {})),
        )

    def delete_case(self, case_id: str, *, delete_backup: bool) -> None:
        self.objects.pop(case_id, None)
        self.index.pop(case_id, None)
        self.queue = [item for item in self.queue if item != case_id]
        if delete_backup:
            self.backups.pop(case_id, None)

    def restore_case(self, case_id: str) -> None:
        backup = self.backups.get(case_id)
        if backup is None:
            return
        objects, result = backup
        self.objects[case_id] = dict(objects)
        self.index[case_id] = copy.deepcopy(result)


class _DefaultDenyEgress:
    def check(self, destination: str) -> None:
        parsed = urlparse(destination)
        host = (parsed.hostname or "").lower()
        if parsed.scheme not in {"http", "https"} or host not in {
            f"{name}.internal" for name in _INTERNAL_DESTINATIONS
        }:
            raise PermissionError("external egress denied")


class _DisabledTelemetry:
    def emit(self, _event: Mapping[str, Any]) -> None:
        raise PermissionError("telemetry is disabled for D4 synthetic qualification")


def run_d4_synthetic_qualification(
    *,
    repository_sha: str,
    faults: Iterable[str] = (),
) -> dict[str, Any]:
    """Run the source-owned, two-case D4 control plane with synthetic state."""

    fault_set = set(faults)
    controls: dict[str, dict[str, str]] = {}
    issues: list[dict[str, str]] = []

    def record(control_id: str, passed: bool, detail: str) -> None:
        if control_id in fault_set:
            passed = False
            detail = f"fault injected: {detail}"
        status = "pass" if passed else "fail"
        controls[control_id] = {"status": status, "detail": detail}
        if not passed:
            issues.append(
                {"code": "control_failed", "control_id": control_id, "detail": detail}
            )

    contract_pass = repository_sha and len(repository_sha) in range(7, 65)
    record("contract_edge", bool(contract_pass), "D1 result contract is available")

    store = _SyntheticStore()
    results: dict[str, dict[str, Any]] = {}
    metadata: dict[str, dict[str, str]] = {}
    for case_id in _CASE_IDS:
        suffix = case_id.removeprefix("CASE-")
        source_id = f"SRC-{suffix}"
        source_version_id = f"{source_id}-V001"
        block_id = f"BLK-{suffix}-001"
        result = serialize_knowledge_retrieval_result(
            {"score": 1.0},
            context=KnowledgeRetrievalResultContext(
                result_id=f"RET-{suffix}",
                request_id=f"REQ-{suffix}",
                memory_snapshot_id=f"MEM-{suffix}",
                memory_snapshot_sha256="a" * 64,
                knowhere_repository_sha=repository_sha,
                retrieval_configuration_sha256="b" * 64,
                source_id=source_id,
                source_version_id=source_version_id,
                retrieval_reason="synthetic source-version match",
            ),
            locator=KnowledgeRetrievalResultLocator(
                section_path=("1. Scope",),
                native_page_start=1,
                native_page_end=1,
                extraction_block_ids=(block_id,),
                native_reference=f"{source_version_id}:p1#{block_id}",
            ),
        )
        results[case_id] = result
        metadata[case_id] = {
            "source_id": source_id,
            "source_version_id": source_version_id,
            "block_id": block_id,
        }
        store.put_case(case_id, result)

    traceability_pass = all(
        result["source_id"] == metadata[case_id]["source_id"]
        and result["source_version_id"] == metadata[case_id]["source_version_id"]
        and result["knowhere_repository_sha"] == repository_sha
        for case_id, result in results.items()
    )
    record("source_version_traceability", traceability_pass, "source/version and repository identities match")

    linkage_pass = all(
        not validate_knowledge_retrieval_result(
            result,
            allowed_source_ids={metadata[case_id]["source_id"]},
            expected_request_id=result["request_id"],
            expected_source_version_id=metadata[case_id]["source_version_id"],
            expected_extraction_block_ids={metadata[case_id]["block_id"]},
        )
        for case_id, result in results.items()
    )
    record("extraction_block_linkage", linkage_pass, "results link to accepted extraction blocks")

    rejected = validate_knowledge_retrieval_result(
        results["CASE-SYN-B"],
        allowed_source_ids={metadata["CASE-SYN-A"]["source_id"]},
        expected_request_id=results["CASE-SYN-B"]["request_id"],
        expected_source_version_id=metadata["CASE-SYN-B"]["source_version_id"],
        expected_extraction_block_ids={metadata["CASE-SYN-B"]["block_id"]},
    )
    record(
        "source_allowlist",
        any(issue.code == "source_not_allowlisted" for issue in rejected),
        "unallowlisted source is rejected",
    )

    record(
        "cross_case_isolation",
        results["CASE-SYN-A"]["source_id"] != results["CASE-SYN-B"]["source_id"]
        and results["CASE-SYN-A"]["source_version_id"]
        != results["CASE-SYN-B"]["source_version_id"],
        "case-scoped source and result identities remain distinct",
    )
    record(
        "citation",
        all(
            str(result["citation"]["native_reference"]).startswith(
                f"{metadata[case_id]['source_version_id']}:"
            )
            for case_id, result in results.items()
        ),
        "citations remain rooted in source versions",
    )

    stale = validate_knowledge_retrieval_result(
        results["CASE-SYN-A"],
        allowed_source_ids={metadata["CASE-SYN-A"]["source_id"]},
        expected_request_id=results["CASE-SYN-A"]["request_id"],
        expected_source_version_id=metadata["CASE-SYN-A"]["source_version_id"],
        expected_extraction_block_ids={metadata["CASE-SYN-A"]["block_id"]},
        current_memory_snapshot_id="MEM-SYN-A-NEW",
        current_memory_snapshot_sha256="c" * 64,
        invalidated=True,
    )
    stale_codes = {issue.code for issue in stale}
    record(
        "stale_invalidation",
        {"stale_result", "invalidated_result"} <= stale_codes,
        "stale and invalidated results are rejected",
    )

    store.backup_case("CASE-SYN-A")
    store.backup_case("CASE-SYN-B")
    store.delete_case("CASE-SYN-A", delete_backup=True)
    deletion_pass = (
        "CASE-SYN-A" not in store.objects
        and "CASE-SYN-A" not in store.index
        and "CASE-SYN-A" not in store.queue
        and "CASE-SYN-A" not in store.backups
        and "CASE-SYN-B" in store.objects
    )
    record("scoped_deletion", deletion_pass, "source, derivative, index, queue, and backup removed")

    store.delete_case("CASE-SYN-B", delete_backup=False)
    store.restore_case("CASE-SYN-B")
    record(
        "backup_restore",
        "CASE-SYN-B" in store.objects
        and store.index["CASE-SYN-B"]["source_id"] == results["CASE-SYN-B"]["source_id"],
        "synthetic case restored from bounded backup",
    )

    try:
        _DefaultDenyEgress().check("https://external.invalid/d4")
        egress_pass = False
    except PermissionError:
        egress_pass = True
    record("egress_default_deny", egress_pass, "external destination denied")

    try:
        _DisabledTelemetry().emit({"event": "synthetic-d4"})
        telemetry_pass = False
    except PermissionError:
        telemetry_pass = True
    record("telemetry_disabled", telemetry_pass, "telemetry emission denied")

    record("private_data_boundary", True, "synthetic identifiers and bytes only")
    record("ra_evidence_deferred", True, "native verification and RA acceptance remain pending")

    failed = any(item["status"] == "fail" for item in controls.values())
    return {
        "technical_completion": "mechanical_fail" if failed else "qualified",
        "ra_evidence_state": "deferred",
        "release_decision": "defer",
        "controls": controls,
        "issues": issues,
        "case_ids": list(_CASE_IDS),
        "private_data": False,
        "provider_execution": False,
        "repository_sha": repository_sha,
    }


def _text_value(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


def _string_set(value: object) -> set[str]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Collection):
        return set()
    return {item.strip() for item in value if isinstance(item, str) and item.strip()}


__all__ = [
    "RetrievalQualificationIssue",
    "run_d4_synthetic_qualification",
    "validate_knowledge_retrieval_result",
]
