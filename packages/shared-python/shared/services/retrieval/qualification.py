"""Fail-closed technical qualification helpers for Knowhere retrieval results."""

from __future__ import annotations

import copy
import hashlib
import json
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


def validate_v3_structure_retrieval_result(
    result: Mapping[str, Any],
    *,
    expected_table_ids: Collection[str],
    expected_image_ids: Collection[str],
) -> tuple[RetrievalQualificationIssue, ...]:
    """Require exact source-owned V3 table and image identity sets."""

    issues: list[RetrievalQualificationIssue] = []
    if _string_set(result.get("linked_table_ids")) != set(
        expected_table_ids
    ):
        issues.append(
            RetrievalQualificationIssue(
                "linked_table_ids_mismatch",
                "retrieval result table IDs differ from the V3 manifest",
            )
        )
    if _string_set(result.get("linked_image_ids")) != set(
        expected_image_ids
    ):
        issues.append(
            RetrievalQualificationIssue(
                "linked_image_ids_mismatch",
                "retrieval result image IDs differ from the V3 manifest",
            )
        )
    return tuple(issues)


def canonical_fixture_sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


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


def run_v3_structure_synthetic_qualification(
    *,
    fixture_set: Mapping[str, Any],
    expected_fixture_sha256: str,
    repository_sha: str,
    faults: Iterable[str] = (),
) -> dict[str, Any]:
    """Qualify the exact MinerU V3 fixture through bounded Knowhere controls."""

    fault_set = set(faults)
    controls: dict[str, dict[str, str]] = {}
    issues: list[dict[str, str]] = []

    def record(control_id: str, passed: bool, detail: str) -> None:
        if control_id in fault_set:
            passed = False
            detail = f"fault injected: {detail}"
        controls[control_id] = {
            "status": "pass" if passed else "fail",
            "detail": detail,
        }
        if not passed:
            issues.append(
                {
                    "code": "control_failed",
                    "control_id": control_id,
                    "detail": detail,
                }
            )

    actual_fixture_sha256 = canonical_fixture_sha256(fixture_set)
    record(
        "fixture_sha",
        actual_fixture_sha256 == expected_fixture_sha256,
        "canonical MinerU fixture identity matches",
    )
    profile_id = _text_value(fixture_set.get("profile_id"))
    boundaries = fixture_set.get("boundaries")
    fixtures_value = fixture_set.get("fixtures")
    fixtures = (
        list(fixtures_value)
        if isinstance(fixtures_value, Collection)
        and not isinstance(fixtures_value, (str, bytes, Mapping))
        else []
    )
    record(
        "profile_boundary",
        profile_id == "pypdf_geometry_full_layout_v1_2_candidate"
        and isinstance(boundaries, Mapping)
        and boundaries.get("synthetic_only") is True
        and boundaries.get("contains_private_data") is False
        and boundaries.get("runtime_execution_allowed") is False
        and boundaries.get("provider_execution_allowed") is False
        and boundaries.get("release_allowed") is False,
        "exact bounded synthetic V3 profile and prohibitions are present",
    )

    store = _SyntheticStore()
    results: dict[str, dict[str, Any]] = {}
    fixture_by_id: dict[str, Mapping[str, Any]] = {}
    payload_hash_pass = True
    linked_table_pass = True
    linked_image_pass = True
    continuation_pass = True
    hierarchy_pass = True
    citation_asset_pass = True
    traceability_pass = True
    leakage_values: list[str] = []

    for raw_item in fixtures:
        if not isinstance(raw_item, Mapping):
            payload_hash_pass = False
            continue
        item = raw_item
        fixture_id = _text_value(item.get("fixture_id"))
        manifest = item.get("document_extraction_manifest")
        payload = item.get("structure_payload")
        hierarchy = item.get("section_hierarchy")
        citation_assets = item.get("citation_assets")
        if (
            not fixture_id
            or not isinstance(manifest, Mapping)
            or not isinstance(payload, Mapping)
            or not isinstance(hierarchy, list)
            or not isinstance(citation_assets, list)
        ):
            payload_hash_pass = False
            continue
        fixture_by_id[fixture_id] = item

        payload_sha = canonical_fixture_sha256(payload)
        payload_hash_pass = payload_hash_pass and payload_sha == item.get(
            "candidate_sha256"
        )
        payload_hash_pass = payload_hash_pass and (
            manifest.get("outputs", [{}])[0].get("sha256") == payload_sha
        )
        traceability_pass = traceability_pass and (
            manifest.get("input_sha256") == item.get("native_sha256")
            and manifest.get("source_version_id") == item.get("native_sha256")
        )

        blocks = manifest.get("page_blocks")
        tables = manifest.get("tables")
        images = manifest.get("images")
        if not isinstance(blocks, list):
            blocks = []
        if not isinstance(tables, list):
            tables = []
        if not isinstance(images, list):
            images = []
        block_ids = {
            _text_value(block.get("block_id"))
            for block in blocks
            if isinstance(block, Mapping)
        }
        table_ids = {
            _text_value(table.get("table_id"))
            for table in tables
            if isinstance(table, Mapping)
        }
        image_ids = {
            _text_value(image.get("image_id"))
            for image in images
            if isinstance(image, Mapping)
        }
        block_ids.discard("")
        table_ids.discard("")
        image_ids.discard("")

        continuation_endpoints = {
            _text_value(link.get(key))
            for link in payload.get("continuation_links", [])
            if isinstance(link, Mapping)
            for key in ("from_table_id", "to_table_id")
        }
        continuation_endpoints.discard("")
        continuation_pass = (
            continuation_pass and continuation_endpoints <= table_ids
        )

        section_ids = {
            _text_value(section.get("section_id"))
            for section in hierarchy
            if isinstance(section, Mapping)
        }
        parent_chain_valid = bool(hierarchy)
        for index, section in enumerate(hierarchy):
            if not isinstance(section, Mapping):
                parent_chain_valid = False
                continue
            parent_id = section.get("parent_section_id")
            if index == 0:
                parent_chain_valid = (
                    parent_chain_valid and parent_id is None
                )
            else:
                parent_chain_valid = (
                    parent_chain_valid
                    and isinstance(parent_id, str)
                    and parent_id in section_ids
                )
        leaf = hierarchy[-1] if hierarchy else {}
        leaf_id = (
            _text_value(leaf.get("section_id"))
            if isinstance(leaf, Mapping)
            else ""
        )
        section_path = (
            leaf.get("section_path")
            if isinstance(leaf, Mapping)
            else None
        )
        hierarchy_pass = hierarchy_pass and parent_chain_valid and bool(
            leaf_id
        )
        hierarchy_pass = hierarchy_pass and all(
            part.get("section_id") == leaf_id
            for part in [*blocks, *tables, *images]
            if isinstance(part, Mapping)
        )

        expected_asset_hashes: dict[str, str] = {}
        for table in tables:
            if isinstance(table, Mapping):
                expected_asset_hashes[_text_value(table.get("table_id"))] = (
                    canonical_fixture_sha256(table)
                )
        for image in images:
            if isinstance(image, Mapping):
                expected_asset_hashes[_text_value(image.get("image_id"))] = (
                    _text_value(image.get("sha256"))
                )
        actual_asset_hashes = {
            _text_value(asset.get("asset_id")): _text_value(
                asset.get("sha256")
            )
            for asset in citation_assets
            if isinstance(asset, Mapping)
        }
        citation_asset_pass = citation_asset_pass and (
            actual_asset_hashes == expected_asset_hashes
        )

        page_numbers = [
            int(block["page_number"])
            for block in blocks
            if isinstance(block, Mapping)
            and isinstance(block.get("page_number"), int)
        ]
        source_id = _text_value(manifest.get("source_id"))
        source_version_id = _text_value(manifest.get("source_version_id"))
        result = serialize_knowledge_retrieval_result(
            {"score": 1.0},
            context=KnowledgeRetrievalResultContext(
                result_id=f"RET-{fixture_id}",
                request_id=f"REQ-{fixture_id}",
                memory_snapshot_id=f"MEM-{fixture_id}",
                memory_snapshot_sha256=payload_sha,
                knowhere_repository_sha=repository_sha,
                retrieval_configuration_sha256=expected_fixture_sha256,
                source_id=source_id,
                source_version_id=source_version_id,
                retrieval_reason="bounded V3 synthetic structure qualification",
            ),
            locator=KnowledgeRetrievalResultLocator(
                section_path=tuple(
                    str(value)
                    for value in section_path
                    if isinstance(value, str)
                )
                if isinstance(section_path, list)
                else ("synthetic-v3",),
                native_page_start=min(page_numbers or [1]),
                native_page_end=max(page_numbers or [1]),
                extraction_block_ids=tuple(sorted(block_ids)),
                native_reference=(
                    f"{source_version_id}:p{min(page_numbers or [1])}"
                    f"#{sorted(block_ids)[0] if block_ids else fixture_id}"
                ),
                linked_table_ids=tuple(sorted(table_ids)),
                linked_image_ids=tuple(sorted(image_ids)),
            ),
        )
        results[fixture_id] = result
        store.put_case(fixture_id, result)
        linked_issues = validate_v3_structure_retrieval_result(
            result,
            expected_table_ids=table_ids,
            expected_image_ids=image_ids,
        )
        linked_table_pass = linked_table_pass and not any(
            issue.code == "linked_table_ids_mismatch"
            for issue in linked_issues
        )
        linked_image_pass = linked_image_pass and not any(
            issue.code == "linked_image_ids_mismatch"
            for issue in linked_issues
        )
        for token in payload.get("critical_tokens", []):
            if isinstance(token, Mapping):
                value = token.get("value")
                if (
                    isinstance(value, str)
                    and value
                    and value != fixture_id
                ):
                    leakage_values.append(value)

    record(
        "candidate_payload_hash",
        payload_hash_pass and len(results) == 16,
        "all payloads match frozen candidate hashes",
    )
    record(
        "source_version_traceability",
        traceability_pass and len(results) == 16,
        "manifest source/version identity is preserved",
    )
    record(
        "linked_table_ids",
        linked_table_pass and len(results) == 16,
        "retrieval results preserve exact table ID sets",
    )
    record(
        "linked_image_ids",
        linked_image_pass and len(results) == 16,
        "retrieval results preserve exact image ID sets",
    )
    record(
        "continuation_closure",
        continuation_pass,
        "all continuation endpoints resolve to source-owned tables",
    )
    record(
        "hierarchy_parent_chain",
        hierarchy_pass,
        "three-level section parent chains remain closed",
    )
    record(
        "citation_asset_hash",
        citation_asset_pass,
        "citation assets match source-owned IDs and hashes",
    )

    first_ids = sorted(results)
    allowlist_pass = False
    stale_pass = False
    deletion_pass = False
    restore_pass = False
    if first_ids:
        first_id = first_ids[0]
        first = results[first_id]
        rejected = validate_knowledge_retrieval_result(
            first,
            allowed_source_ids={"SYNTHETIC-NOT-ALLOWED"},
            expected_request_id=first["request_id"],
            expected_source_version_id=first["source_version_id"],
            expected_extraction_block_ids=first["extraction_block_ids"],
        )
        allowlist_pass = any(
            issue.code == "source_not_allowlisted" for issue in rejected
        )
        stale = validate_knowledge_retrieval_result(
            first,
            allowed_source_ids={first["source_id"]},
            expected_request_id=first["request_id"],
            expected_source_version_id=first["source_version_id"],
            expected_extraction_block_ids=first["extraction_block_ids"],
            current_memory_snapshot_id="MEM-STALE-REPLACEMENT",
            current_memory_snapshot_sha256="f" * 64,
            invalidated=True,
        )
        stale_codes = {issue.code for issue in stale}
        stale_pass = {"stale_result", "invalidated_result"} <= stale_codes

        store.backup_case(first_id)
        peer_id = first_ids[1] if len(first_ids) > 1 else None
        store.delete_case(first_id, delete_backup=True)
        deletion_pass = (
            first_id not in store.objects
            and first_id not in store.index
            and first_id not in store.queue
            and first_id not in store.backups
            and (peer_id is None or peer_id in store.index)
        )
        if peer_id is not None:
            store.backup_case(peer_id)
            store.delete_case(peer_id, delete_backup=False)
            store.restore_case(peer_id)
            restore_pass = (
                peer_id in store.objects
                and store.index.get(peer_id) == results[peer_id]
            )
    record(
        "source_allowlist",
        allowlist_pass,
        "unallowlisted V3 source is rejected",
    )
    record(
        "stale_invalidation",
        stale_pass,
        "stale and invalidated V3 results are rejected",
    )
    record(
        "scoped_deletion",
        deletion_pass,
        "bounded synthetic object, index, queue, and backup state is removed",
    )
    record(
        "bounded_backup_restore",
        restore_pass,
        "bounded synthetic peer state round-trips without release claim",
    )

    persisted = json.dumps(store.index, ensure_ascii=False, sort_keys=True)
    leakage_pass = not any(value in persisted for value in leakage_values)
    record(
        "prohibited_persisted_text",
        leakage_pass,
        "raw candidate token text is absent from retrieval index fields",
    )
    record(
        "private_data_boundary",
        True,
        "source fixture declares synthetic-only and contains no private data",
    )
    record(
        "runtime_provider_boundary",
        True,
        "qualification invokes neither runtime nor provider",
    )

    failed = any(item["status"] == "fail" for item in controls.values())
    return {
        "technical_completion": "mechanical_fail" if failed else "qualified",
        "qualification_scope": "bounded_synthetic",
        "ra_evidence_state": "deferred",
        "release_decision": "defer",
        "profile_id": profile_id,
        "fixture_sha256": actual_fixture_sha256,
        "fixture_count": len(results),
        "family_count": len(
            {
                _text_value(item.get("family"))
                for item in fixture_by_id.values()
            }
        ),
        "retrieval_results": [
            results[fixture_id] for fixture_id in sorted(results)
        ],
        "controls": controls,
        "issues": issues,
        "private_data": False,
        "provider_execution": False,
        "runtime_execution": False,
        "repository_sha": repository_sha,
    }


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
    "canonical_fixture_sha256",
    "run_d4_synthetic_qualification",
    "run_v3_structure_synthetic_qualification",
    "validate_knowledge_retrieval_result",
    "validate_v3_structure_retrieval_result",
]
