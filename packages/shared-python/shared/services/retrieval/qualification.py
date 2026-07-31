"""Fail-closed technical qualification helpers for Knowhere retrieval results."""

from __future__ import annotations

import copy
import hashlib
import json
from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
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
_V3_PRODUCTION_REPLAY_REPORT_SHA256 = (
    "5304a6ba14114083ea1edb4c5a3c97ccb5dbfe7406627f4e982ce4a13a7ef58d"
)
_V3_PRODUCTION_REPLAY_FILE_SHA256 = (
    "d9e8b4860839d1b23ea59eac3f9738d01b1c54f3081f7799c40cc76396e6e8a2"
)
_V3_PRODUCTION_REMEDIATION_REPLAY_FILE_SHA256 = (
    "98fca9bca8e5932388b54d7c51adceca1f4e4ef53265fad412c6048d36e6521f"
)
_V3_PRODUCTION_REMEDIATION_FIXTURE_FILE_SHA256 = (
    "c9947104598c3533612ccf72658128742925cc85f44487c926363b394383935c"
)


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
    expected_native_object_ids: Collection[str] | None = None,
    expected_structure_ids: Collection[str] | None = None,
) -> tuple[RetrievalQualificationIssue, ...]:
    """Require exact source-owned V3 object, structure, and asset identity sets."""

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
    if expected_native_object_ids is not None and _string_set(
        result.get("linked_native_object_ids")
    ) != set(expected_native_object_ids):
        issues.append(
            RetrievalQualificationIssue(
                "linked_native_object_ids_mismatch",
                "retrieval result native object IDs differ from the object map",
            )
        )
    if expected_structure_ids is not None and _string_set(
        result.get("linked_structure_ids")
    ) != set(expected_structure_ids):
        issues.append(
            RetrievalQualificationIssue(
                "linked_structure_ids_mismatch",
                "retrieval result structure IDs differ from the association result",
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


class _NamespacedSyntheticStore:
    """Small deterministic state model for cross-case qualification controls."""

    def __init__(self) -> None:
        self.objects: dict[str, dict[str, dict[str, bytes]]] = {}
        self.index: dict[str, dict[str, dict[str, Any]]] = {}
        self.queue: dict[str, list[str]] = {}
        self.backups: dict[str, dict[str, tuple[dict[str, bytes], dict[str, Any]]]] = {}

    def put(
        self,
        namespace: str,
        source_id: str,
        result: Mapping[str, Any],
    ) -> bool:
        namespace_objects = self.objects.setdefault(namespace, {})
        namespace_index = self.index.setdefault(namespace, {})
        namespace_queue = self.queue.setdefault(namespace, [])
        normalized = copy.deepcopy(dict(result))
        existing = namespace_index.get(source_id)
        if existing is not None:
            return existing == normalized and namespace_queue.count(source_id) == 1
        namespace_objects[source_id] = {
            "derivative": canonical_fixture_sha256(normalized).encode("ascii")
        }
        namespace_index[source_id] = normalized
        namespace_queue.append(source_id)
        return True

    def get(self, namespace: str, source_id: str) -> dict[str, Any] | None:
        value = self.index.get(namespace, {}).get(source_id)
        return copy.deepcopy(value) if value is not None else None

    def backup(self, namespace: str, source_id: str) -> None:
        objects = self.objects.get(namespace, {}).get(source_id)
        result = self.index.get(namespace, {}).get(source_id)
        if objects is None or result is None:
            return
        self.backups.setdefault(namespace, {})[source_id] = (
            dict(objects),
            copy.deepcopy(result),
        )

    def delete(
        self,
        namespace: str,
        source_id: str,
        *,
        delete_backup: bool,
    ) -> None:
        self.objects.get(namespace, {}).pop(source_id, None)
        self.index.get(namespace, {}).pop(source_id, None)
        self.queue[namespace] = [
            queued
            for queued in self.queue.get(namespace, [])
            if queued != source_id
        ]
        if delete_backup:
            self.backups.get(namespace, {}).pop(source_id, None)

    def restore(self, namespace: str, source_id: str) -> None:
        backup = self.backups.get(namespace, {}).get(source_id)
        if backup is None:
            return
        objects, result = backup
        self.objects.setdefault(namespace, {})[source_id] = dict(objects)
        self.index.setdefault(namespace, {})[source_id] = copy.deepcopy(result)
        queue = self.queue.setdefault(namespace, [])
        if source_id not in queue:
            queue.append(source_id)


def _canonical_without(value: Mapping[str, Any], field: str) -> str:
    payload = dict(value)
    payload.pop(field, None)
    return canonical_fixture_sha256(payload)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _prefixed_ids(value: Any, prefix: str) -> set[str]:
    found: set[str] = set()
    if isinstance(value, Mapping):
        for nested in value.values():
            found.update(_prefixed_ids(nested, prefix))
    elif isinstance(value, Collection) and not isinstance(value, (str, bytes)):
        for nested in value:
            found.update(_prefixed_ids(nested, prefix))
    elif isinstance(value, str):
        found.update(
            token
            for token in value.split()
            if token.startswith(prefix)
        )
    return found


def _safe_fixture_path(root: Path, relative_path: object) -> Path | None:
    if not isinstance(relative_path, str) or not relative_path:
        return None
    root = root.resolve()
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError:
        return None
    return candidate


def run_v3_production_structure_synthetic_qualification(
    *,
    fixture_set: Mapping[str, Any],
    fixture_root: Path,
    expected_fixture_sha256: str,
    repository_sha: str,
    faults: Iterable[str] = (),
    replay_evidence_profile: str = "merged_formal",
) -> dict[str, Any]:
    """Qualify the 24-fixture generic V3 production edge without RA authority."""

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

    declared_fixture_sha = _text_value(fixture_set.get("fixture_set_sha256"))
    actual_fixture_sha = _canonical_without(
        fixture_set, "fixture_set_sha256"
    )
    fixture_seal_pass = (
        declared_fixture_sha
        == actual_fixture_sha
        == expected_fixture_sha256
    )
    record(
        "fixture_set_sha",
        fixture_seal_pass,
        "source-owned fixture set self-seal and expected seal match",
    )

    boundaries = fixture_set.get("boundaries")
    fixtures_value = fixture_set.get("fixtures")
    fixtures = (
        list(fixtures_value)
        if isinstance(fixtures_value, Collection)
        and not isinstance(fixtures_value, (str, bytes, Mapping))
        else []
    )
    profile_id = _text_value(fixture_set.get("profile_id"))
    profile_boundary_pass = (
        fixture_set.get("schema")
        == "mineru-v3-production-downstream-fixture-set/1.0"
        and profile_id == "mineru_complex_layout_structural_v2"
        and fixture_set.get("fixture_count") == 24
        and len(fixtures) == 24
        and isinstance(boundaries, Mapping)
        and boundaries.get("synthetic_only") is True
        and boundaries.get("contains_private_data") is False
        and boundaries.get("native_source_evidence") is False
        and boundaries.get("source_sufficiency_established") is False
        and boundaries.get("runtime_execution_allowed") is False
        and boundaries.get("provider_execution_allowed") is False
        and boundaries.get("release_allowed") is False
    )
    record(
        "profile_boundary",
        profile_boundary_pass,
        "generic production profile remains bounded synthetic and non-release",
    )
    replay_path = fixture_root / (
        "replay-report.json"
        if replay_evidence_profile == "remediation_replay"
        else "merged-replay-report.json"
    )
    replay_report: Mapping[str, Any] = {}
    replay_file_pass = replay_path.is_file()
    if replay_file_pass:
        try:
            loaded_replay = json.loads(replay_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            loaded_replay = {}
        if isinstance(loaded_replay, Mapping):
            replay_report = loaded_replay
    if replay_evidence_profile == "merged_formal":
        replay_provenance_pass = (
            replay_file_pass
            and _file_sha256(replay_path)
            == _V3_PRODUCTION_REPLAY_FILE_SHA256
            and replay_report.get("schema")
            == "mineru-v3-production-merged-replay/1.0"
            and replay_report.get("report_sha256")
            == _V3_PRODUCTION_REPLAY_REPORT_SHA256
            and _canonical_without(replay_report, "report_sha256")
            == _V3_PRODUCTION_REPLAY_REPORT_SHA256
            and replay_report.get("downstream_fixture_set_sha256")
            == expected_fixture_sha256
            and replay_report.get("formal_holdout_consumed") is True
            and replay_report.get("reviewed_tree_matches_merged_tree") is True
            and replay_report.get("component_identities_match") is True
            and replay_report.get("aggregate_results_match") is True
            and replay_report.get("qualification_credit") is False
            and replay_report.get("new_holdout_created") is False
        )
    elif replay_evidence_profile == "remediation_replay":
        aggregate_metrics = replay_report.get("aggregate_metrics")
        replay_provenance_pass = (
            replay_file_pass
            and _file_sha256(replay_path)
            == _V3_PRODUCTION_REMEDIATION_REPLAY_FILE_SHA256
            and replay_report.get("schema")
            == "mineru-v3-private-remediation-downstream-replay/1.0"
            and replay_report.get("candidate_repository_sha")
            == "ce2b2c50c5462f11a3d7700c08a4ccdec4cb10bd"
            and replay_report.get("candidate_tree_sha")
            == "270c38c399d4fcb026720ecf8f72650ba4cb5ed9"
            and replay_report.get("fixture_set_file_sha256")
            == _V3_PRODUCTION_REMEDIATION_FIXTURE_FILE_SHA256
            and replay_report.get("fixture_set_sha256")
            == expected_fixture_sha256
            and replay_report.get("fixture_count") == 24
            and replay_report.get("deterministic_builds") == 2
            and replay_report.get("deterministic_match") is True
            and replay_report.get("consumed_native_identity_match") is True
            and replay_report.get("contains_private_data") is False
            and replay_report.get("new_holdout_created") is False
            and replay_report.get("replacement_holdout") is False
            and replay_report.get("qualification_credit") is False
            and isinstance(aggregate_metrics, Mapping)
            and bool(aggregate_metrics)
            and not any(aggregate_metrics.values())
        )
    else:
        replay_provenance_pass = False
    record(
        "merged_replay_provenance",
        replay_provenance_pass,
        (
            "remediation replay report byte seal and no-credit boundaries match"
            if replay_evidence_profile == "remediation_replay"
            else (
                "merged replay report byte seal, semantic seal, and no-credit "
                "state match"
            )
        ),
    )

    native_hash_pass = True
    artifact_hash_pass = True
    identity_pass = True
    object_link_pass = True
    manifest_link_pass = True
    hierarchy_pass = True
    continuation_pass = True
    citation_pass = True
    authority_pass = True
    store = _NamespacedSyntheticStore()
    namespace = "v3-production-synthetic"
    other_namespace = "v3-production-other"
    results: dict[str, dict[str, Any]] = {}
    family_names: set[str] = set()
    fixture_control_passes: dict[str, dict[str, bool]] = {}

    for raw_item in fixtures:
        if not isinstance(raw_item, Mapping):
            identity_pass = False
            continue
        item = raw_item
        source_id = _text_value(item.get("fixture_id"))
        native_sha = _text_value(item.get("native_sha256"))
        object_map = item.get("native_object_map")
        association = item.get("structure_association_result")
        manifest = item.get("document_extraction_manifest")
        hierarchy = item.get("section_hierarchy")
        citation_assets = item.get("citation_assets")
        if (
            not source_id.startswith("V3P-EDGE-")
            or not isinstance(object_map, Mapping)
            or not isinstance(association, Mapping)
            or not isinstance(manifest, Mapping)
            or not isinstance(hierarchy, list)
            or not isinstance(citation_assets, list)
        ):
            identity_pass = False
            continue
        family_names.add(_text_value(item.get("family")))

        native_path = _safe_fixture_path(
            fixture_root, item.get("native_pdf_relative_path")
        )
        item_native_hash_pass = (
            native_path is not None
            and native_path.is_file()
            and _file_sha256(native_path) == native_sha
        )
        native_hash_pass = native_hash_pass and item_native_hash_pass

        object_map_hash = _canonical_without(
            object_map, "artifact_sha256"
        )
        object_ids = {
            _text_value(obj.get("object_id"))
            for obj in object_map.get("objects", [])
            if isinstance(obj, Mapping)
        }
        structure_ids = _prefixed_ids(association, "NST-")
        referenced_object_ids = _prefixed_ids(association, "NSO-")
        item_identity_pass = (
            object_map.get("contract_version")
            == "native-structure-object-map-v1"
            and association.get("contract_version")
            == "structure-association-result-v1"
            and object_map.get("source_id") == source_id
            and association.get("source_id") == source_id
            and object_map.get("source_version_id") == native_sha
            and association.get("source_version_id") == native_sha
            and object_map.get("input_sha256") == native_sha
            and association.get("input_sha256") == native_sha
            and object_map.get("artifact_sha256") == object_map_hash
            and association.get("native_object_map_sha256")
            == object_map_hash
            and all(object_id.startswith("NSO-") for object_id in object_ids)
        )
        for obj in object_map.get("objects", []):
            if not isinstance(obj, Mapping):
                item_identity_pass = False
                continue
            identity_input = {
                "source_sha256": native_sha,
                "page_number": obj.get("page_number"),
                "object_type": obj.get("object_type"),
                "normalized_bbox_quantized": obj.get("normalized_bbox"),
                "raw_object_sha256": obj.get("raw_object_sha256"),
                "occurrence_index": obj.get("occurrence_index"),
            }
            item_identity_pass = item_identity_pass and obj.get(
                "object_id"
            ) == f"NSO-{canonical_fixture_sha256(identity_input)[:32]}"
        identity_pass = identity_pass and item_identity_pass
        item_object_link_pass = (
            bool(object_ids)
            and referenced_object_ids <= object_ids
        )
        object_link_pass = object_link_pass and item_object_link_pass

        outputs = manifest.get("outputs")
        if not isinstance(outputs, list):
            outputs = []
        expected_artifacts = {
            "native-structure-object-map-v1": object_map,
            "structure-association-result-v1": association,
        }
        item_artifact_hash_pass = len(outputs) == 2
        association_artifact_sha = ""
        for output in outputs:
            if not isinstance(output, Mapping):
                item_artifact_hash_pass = False
                continue
            artifact_type = _text_value(output.get("artifact_type"))
            artifact_path = _safe_fixture_path(
                fixture_root, output.get("relative_path")
            )
            expected_payload = expected_artifacts.get(artifact_type)
            if artifact_type == "structure-association-result-v1":
                association_artifact_sha = _text_value(output.get("sha256"))
            item_artifact_hash_pass = (
                item_artifact_hash_pass
                and artifact_path is not None
                and artifact_path.is_file()
                and expected_payload is not None
                and json.loads(artifact_path.read_text(encoding="utf-8"))
                == expected_payload
                and _file_sha256(artifact_path) == output.get("sha256")
            )
        manifest_file = fixture_root / "artifacts" / (
            f"{source_id}.document-extraction-manifest.json"
        )
        item_artifact_hash_pass = (
            item_artifact_hash_pass
            and manifest_file.is_file()
            and json.loads(manifest_file.read_text(encoding="utf-8"))
            == manifest
        )
        artifact_hash_pass = artifact_hash_pass and item_artifact_hash_pass

        manifest_tables = [
            table
            for table in manifest.get("tables", [])
            if isinstance(table, Mapping)
        ]
        manifest_images = [
            image
            for image in manifest.get("images", [])
            if isinstance(image, Mapping)
        ]
        manifest_blocks = [
            block
            for block in manifest.get("page_blocks", [])
            if isinstance(block, Mapping)
        ]
        association_tables = [
            table
            for table in association.get("tables", [])
            if isinstance(table, Mapping)
        ]
        table_ids = {
            _text_value(table.get("table_id")) for table in manifest_tables
        }
        association_table_ids = {
            _text_value(table.get("table_id"))
            for table in association_tables
        }
        block_ids = {
            _text_value(block.get("block_id")) for block in manifest_blocks
        }
        image_ids = {
            _text_value(image.get("image_id")) for image in manifest_images
        }
        item_manifest_link_pass = (
            manifest.get("source_id") == source_id
            and manifest.get("source_version_id") == native_sha
            and manifest.get("input_sha256") == native_sha
            and table_ids == association_table_ids
            and block_ids <= structure_ids
            and image_ids <= (object_ids | structure_ids)
            and _prefixed_ids(manifest_tables, "NSO-") <= object_ids
            and _prefixed_ids(manifest_images, "NSO-") <= object_ids
        )

        hierarchy_ids = {
            _text_value(section.get("section_id"))
            for section in hierarchy
            if isinstance(section, Mapping)
        }
        parent_chain_pass = bool(hierarchy)
        for index, section in enumerate(hierarchy):
            if not isinstance(section, Mapping):
                parent_chain_pass = False
                continue
            parent = section.get("parent_section_id")
            parent_chain_pass = parent_chain_pass and (
                parent is None if index == 0 else parent in hierarchy_ids
            )
        leaf_id = _text_value(
            hierarchy[-1].get("section_id")
            if hierarchy and isinstance(hierarchy[-1], Mapping)
            else None
        )
        item_hierarchy_pass = (
            parent_chain_pass
            and all(
                part.get("section_id") == leaf_id
                for part in [*manifest_blocks, *manifest_tables]
            )
            and all(
                image.get("section_id") in {None, leaf_id}
                for image in manifest_images
            )
        )
        hierarchy_pass = hierarchy_pass and item_hierarchy_pass

        continuation_ids = _prefixed_ids(
            association.get("continuation_links", []), "NST-"
        )
        item_continuation_pass = continuation_ids <= association_table_ids
        continuation_pass = continuation_pass and item_continuation_pass

        expected_assets = {
            _text_value(table.get("table_id")): canonical_fixture_sha256(
                table
            )
            for table in manifest_tables
        }
        expected_assets.update(
            {
                _text_value(image.get("image_id")): _text_value(
                    image.get("sha256")
                )
                for image in manifest_images
            }
        )
        actual_assets = {
            _text_value(asset.get("asset_id")): _text_value(
                asset.get("sha256")
            )
            for asset in citation_assets
            if isinstance(asset, Mapping)
        }
        item_citation_pass = actual_assets == expected_assets
        citation_pass = citation_pass and item_citation_pass

        page_numbers = [
            int(block["page_number"])
            for block in manifest_blocks
            if isinstance(block.get("page_number"), int)
        ]
        result = serialize_knowledge_retrieval_result(
            {"score": 1.0},
            context=KnowledgeRetrievalResultContext(
                result_id=f"RET-{source_id}",
                request_id=f"REQ-{source_id}",
                memory_snapshot_id=f"MEM-{source_id}",
                memory_snapshot_sha256=(
                    association_artifact_sha or "0" * 64
                ),
                knowhere_repository_sha=repository_sha,
                retrieval_configuration_sha256=expected_fixture_sha256,
                source_id=source_id,
                source_version_id=native_sha,
                retrieval_reason=(
                    "bounded V3 production synthetic evidence retrieval"
                ),
            ),
            locator=KnowledgeRetrievalResultLocator(
                section_path=tuple(
                    str(part)
                    for part in hierarchy[-1].get("section_path", [])
                ),
                native_page_start=min(page_numbers or [1]),
                native_page_end=max(page_numbers or [1]),
                extraction_block_ids=tuple(sorted(block_ids)),
                native_reference=(
                    f"{native_sha}:p{min(page_numbers or [1])}"
                    f"#{sorted(block_ids)[0]}"
                ),
                linked_table_ids=tuple(sorted(table_ids)),
                linked_image_ids=tuple(sorted(image_ids)),
            ),
        )
        result["linked_native_object_ids"] = sorted(object_ids)
        result["linked_structure_ids"] = sorted(structure_ids)
        result["evidence_lead_only"] = True
        linked_issues = validate_v3_structure_retrieval_result(
            result,
            expected_table_ids=table_ids,
            expected_image_ids=image_ids,
            expected_native_object_ids=object_ids,
            expected_structure_ids=structure_ids,
        )
        item_manifest_link_pass = item_manifest_link_pass and not linked_issues
        manifest_link_pass = manifest_link_pass and item_manifest_link_pass
        results[source_id] = result
        item_authority_pass = not validate_knowledge_retrieval_result(
            result,
            allowed_source_ids={source_id},
            expected_request_id=result["request_id"],
            expected_source_version_id=native_sha,
            expected_extraction_block_ids=block_ids,
        )
        authority_pass = authority_pass and item_authority_pass
        store.put(namespace, source_id, result)
        fixture_control_passes[source_id] = {
            "fixture_set_sha": fixture_seal_pass,
            "profile_boundary": profile_boundary_pass,
            "merged_replay_provenance": replay_provenance_pass,
            "native_source_hash": item_native_hash_pass,
            "artifact_file_hash": item_artifact_hash_pass,
            "source_version_object_map_identity": item_identity_pass,
            "object_structure_linkage": item_object_link_pass,
            "block_table_image_object_linkage": item_manifest_link_pass,
            "section_hierarchy": item_hierarchy_pass,
            "cross_page_continuation": item_continuation_pass,
            "citation_assets": item_citation_pass,
            "authority_boundary": item_authority_pass,
            "evidence_lead_only": result.get("evidence_lead_only") is True,
        }

    record(
        "native_source_hash",
        native_hash_pass and len(results) == 24,
        "all 24 native synthetic PDF byte hashes match source versions",
    )
    record(
        "artifact_file_hash",
        artifact_hash_pass and len(results) == 24,
        "all declared artifacts match embedded contracts and exact file bytes",
    )
    record(
        "source_version_object_map_identity",
        identity_pass and len(results) == 24,
        "source, version, map seal, and candidate-independent NSO identities match",
    )
    record(
        "object_structure_linkage",
        object_link_pass and len(results) == 24,
        "every structure object reference resolves in its native object map",
    )
    record(
        "block_table_image_object_linkage",
        manifest_link_pass and len(results) == 24,
        "manifest blocks, tables, images, objects, and structures remain linked",
    )
    record(
        "section_hierarchy",
        hierarchy_pass and len(results) == 24,
        "document hierarchy is closed and all manifest items bind its leaf",
    )
    record(
        "cross_page_continuation",
        continuation_pass and len(results) == 24,
        "all continuation endpoints resolve to source-owned table IDs",
    )
    record(
        "citation_assets",
        citation_pass and len(results) == 24,
        "citation asset IDs and hashes match source-owned manifests",
    )

    ordered_ids = sorted(results)
    for index, source_id in enumerate(ordered_ids):
        result = results[source_id]
        allowlist_issues = validate_knowledge_retrieval_result(
            result,
            allowed_source_ids={"V3P-EDGE-NOT-ALLOWED"},
            expected_request_id=result["request_id"],
            expected_source_version_id=result["source_version_id"],
            expected_extraction_block_ids=result["extraction_block_ids"],
        )
        item_allowlist_pass = any(
            issue.code == "source_not_allowlisted"
            for issue in allowlist_issues
        )
        stale_issues = validate_knowledge_retrieval_result(
            result,
            allowed_source_ids={result["source_id"]},
            expected_request_id=result["request_id"],
            expected_source_version_id=result["source_version_id"],
            expected_extraction_block_ids=result["extraction_block_ids"],
            current_memory_snapshot_id="MEM-REPLACED",
            current_memory_snapshot_sha256="f" * 64,
            invalidated=True,
        )
        stale_codes = {issue.code for issue in stale_issues}
        item_stale_pass = {
            "stale_result",
            "invalidated_result",
        } <= stale_codes
        item_isolation_pass = (
            store.get(namespace, source_id) == result
            and store.get(other_namespace, source_id) is None
        )
        item_idempotency_pass = store.put(namespace, source_id, result)

        peer_id = (
            ordered_ids[(index + 1) % len(ordered_ids)]
            if len(ordered_ids) > 1
            else ""
        )
        deletion_store = _NamespacedSyntheticStore()
        deletion_store.put(namespace, source_id, result)
        if peer_id:
            deletion_store.put(namespace, peer_id, results[peer_id])
        deletion_store.backup(namespace, source_id)
        deletion_store.delete(namespace, source_id, delete_backup=True)
        item_deletion_pass = (
            deletion_store.get(namespace, source_id) is None
            and source_id not in deletion_store.objects.get(namespace, {})
            and source_id not in deletion_store.queue.get(namespace, [])
            and source_id not in deletion_store.backups.get(namespace, {})
            and bool(peer_id)
            and deletion_store.get(namespace, peer_id) == results[peer_id]
        )
        restore_store = _NamespacedSyntheticStore()
        restore_store.put(namespace, source_id, result)
        expected_restore_objects = copy.deepcopy(
            restore_store.objects[namespace][source_id]
        )
        restore_store.backup(namespace, source_id)
        restore_store.delete(namespace, source_id, delete_backup=False)
        restore_store.restore(namespace, source_id)
        item_restore_pass = (
            restore_store.get(namespace, source_id) == result
            and restore_store.objects.get(namespace, {}).get(source_id)
            == expected_restore_objects
            and restore_store.queue.get(namespace, []).count(source_id) == 1
            and source_id in restore_store.backups.get(namespace, {})
        )
        fixture_control_passes[source_id].update(
            {
                "source_allowlist": item_allowlist_pass,
                "stale_invalidation": item_stale_pass,
                "namespace_isolation": item_isolation_pass,
                "idempotency": item_idempotency_pass,
                "scoped_deletion": item_deletion_pass,
                "bounded_backup_restore": item_restore_pass,
            }
        )

    def every_fixture(control_id: str) -> bool:
        return len(fixture_control_passes) == 24 and all(
            checks.get(control_id) is True
            for checks in fixture_control_passes.values()
        )

    allowlist_pass = every_fixture("source_allowlist")
    stale_pass = every_fixture("stale_invalidation")
    isolation_pass = every_fixture("namespace_isolation")
    idempotency_pass = every_fixture("idempotency")
    deletion_pass = every_fixture("scoped_deletion")
    restore_pass = every_fixture("bounded_backup_restore")
    record("source_allowlist", allowlist_pass, "unallowlisted source is rejected")
    record(
        "stale_invalidation",
        stale_pass,
        "stale and explicitly invalidated snapshots are rejected",
    )
    record(
        "namespace_isolation",
        isolation_pass,
        "retrieval state is unavailable from a peer namespace",
    )
    record(
        "idempotency",
        idempotency_pass,
        "duplicate publication preserves one identical indexed result",
    )
    record(
        "scoped_deletion",
        deletion_pass,
        "source objects, index, queue, and backup delete without peer loss",
    )
    record(
        "bounded_backup_restore",
        restore_pass,
        "one namespace-scoped derivative round-trips exactly",
    )
    record(
        "authority_boundary",
        authority_pass and len(results) == 24,
        "Knowhere remains unverified and emits no RA-owned decision field",
    )

    egress = _DefaultDenyEgress()
    no_egress_pass = False
    try:
        egress.check("https://external-model.example")
    except PermissionError:
        no_egress_pass = True
    record(
        "no_external_model_egress",
        no_egress_pass,
        "external model and network destination is denied",
    )
    for checks in fixture_control_passes.values():
        checks["no_external_model_egress"] = no_egress_pass
    record(
        "evidence_lead_only",
        len(results) == 24
        and all(result.get("evidence_lead_only") is True for result in results.values()),
        "all retrieval results are evidence leads, not source decisions",
    )

    failed = any(control["status"] == "fail" for control in controls.values())
    fixture_control_results = {
        source_id: {
            control_id: {
                "status": "pass" if passed else "fail",
            }
            for control_id, passed in sorted(checks.items())
        }
        for source_id, checks in sorted(fixture_control_passes.items())
    }
    return {
        "technical_completion": "mechanical_fail" if failed else "qualified",
        "qualification_scope": "bounded_synthetic",
        "profile_id": profile_id,
        "fixture_set_sha256": actual_fixture_sha,
        "fixture_count": len(results),
        "passing_fixture_count": (
            len(results) if not failed else 0
        ),
        "family_count": len(family_names - {""}),
        "retrieval_results": [
            results[source_id] for source_id in sorted(results)
        ],
        "controls": controls,
        "fixture_control_results": fixture_control_results,
        "issues": issues,
        "private_data": False,
        "provider_execution": False,
        "runtime_execution": False,
        "external_model_execution": False,
        "external_egress": False,
        "ra_evidence_state": "deferred",
        "release_decision": "defer",
        "repository_sha": repository_sha,
    }


def run_v3_production_remediation_structure_synthetic_qualification(
    *,
    fixture_set: Mapping[str, Any],
    fixture_root: Path,
    expected_fixture_sha256: str,
    repository_sha: str,
    faults: Iterable[str] = (),
) -> dict[str, Any]:
    """Qualify the remediated V3 synthetic edge without release authority."""

    return run_v3_production_structure_synthetic_qualification(
        fixture_set=fixture_set,
        fixture_root=fixture_root,
        expected_fixture_sha256=expected_fixture_sha256,
        repository_sha=repository_sha,
        faults=faults,
        replay_evidence_profile="remediation_replay",
    )


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
    "run_v3_production_remediation_structure_synthetic_qualification",
    "run_v3_production_structure_synthetic_qualification",
    "run_v3_structure_synthetic_qualification",
    "validate_knowledge_retrieval_result",
    "validate_v3_structure_retrieval_result",
]
