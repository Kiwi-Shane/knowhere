from __future__ import annotations

import hashlib
import json
import shutil
from copy import deepcopy
from pathlib import Path

from shared.services.retrieval.qualification import (
    run_v3_production_remediation_structure_synthetic_qualification,
)


FIXTURE_ROOT = (
    Path(__file__).parent / "fixtures" / "v3_production_structure_remediation"
)
FIXTURE_PATH = FIXTURE_ROOT / "fixture-set.json"
FIXTURE_SHA256 = "dee23ff5acf3065ebb651790fbf57dbd6084c3a103f1492ccbea6a8d10e35203"
QUALIFICATION_IMPLEMENTATION_SHA = (
    "da2e898a75bf313a3db5ce13d6ae2ad1a02919bc"
)
REPORT_PATH = (
    Path(__file__).resolve().parents[4]
    / "examples"
    / "qualification"
    / "v3-production-remediation-structure-retrieval"
    / "qualification-report.json"
)
REPORT_SHA256 = "665b09802adf590fa4fb66d842f1975e9a08ec1d69c9e71dac933807e89737e1"
TEST_REPOSITORY_SHA = "a" * 40
REQUIRED_CONTROLS = {
    "fixture_set_sha",
    "profile_boundary",
    "merged_replay_provenance",
    "native_source_hash",
    "artifact_file_hash",
    "source_version_object_map_identity",
    "object_structure_linkage",
    "block_table_image_object_linkage",
    "section_hierarchy",
    "cross_page_continuation",
    "citation_assets",
    "source_allowlist",
    "stale_invalidation",
    "namespace_isolation",
    "idempotency",
    "scoped_deletion",
    "bounded_backup_restore",
    "authority_boundary",
    "no_external_model_egress",
    "evidence_lead_only",
}


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _run(
    *,
    fixture_set: dict[str, object] | None = None,
    fixture_root: Path = FIXTURE_ROOT,
    repository_sha: str = TEST_REPOSITORY_SHA,
) -> dict[str, object]:
    return run_v3_production_remediation_structure_synthetic_qualification(
        fixture_set=fixture_set or _fixture(),
        fixture_root=fixture_root,
        expected_fixture_sha256=FIXTURE_SHA256,
        repository_sha=repository_sha,
    )


def test_remediated_v3_edge_qualifies_24_fixtures_and_480_controls() -> None:
    report = _run()

    assert report["technical_completion"] == "qualified"
    assert report["qualification_scope"] == "bounded_synthetic"
    assert report["profile_id"] == "mineru_complex_layout_structural_v2"
    assert report["fixture_set_sha256"] == FIXTURE_SHA256
    assert report["fixture_count"] == 24
    assert report["passing_fixture_count"] == 24
    assert len(report["retrieval_results"]) == 24
    assert set(report["controls"]) == REQUIRED_CONTROLS
    assert all(control["status"] == "pass" for control in report["controls"].values())
    assert len(report["fixture_control_results"]) == 24
    assert (
        sum(
            control["status"] == "pass"
            for controls in report["fixture_control_results"].values()
            for control in controls.values()
        )
        == 480
    )
    assert all(
        result["native_source_verification_status"] == "unverified"
        and result["not_source_sufficiency_decision"] is True
        and result["evidence_lead_only"] is True
        and result["linked_native_object_ids"]
        and result["linked_structure_ids"]
        for result in report["retrieval_results"]
    )
    assert report["private_data"] is False
    assert report["provider_execution"] is False
    assert report["runtime_execution"] is False
    assert report["external_model_execution"] is False
    assert report["external_egress"] is False
    assert report["release_decision"] == "defer"


def test_remediated_v3_edge_rejects_fixture_identity_tampering() -> None:
    fixture = deepcopy(_fixture())
    fixture["fixtures"][0]["native_object_map"]["objects"][0]["object_id"] = (
        "NSO-tampered"
    )

    report = _run(fixture_set=fixture)

    assert report["technical_completion"] == "mechanical_fail"
    assert report["controls"]["fixture_set_sha"]["status"] == "fail"
    assert report["controls"]["source_version_object_map_identity"]["status"] == "fail"


def test_remediated_v3_edge_rejects_replay_provenance_tampering(
    tmp_path: Path,
) -> None:
    fixture_root = tmp_path / "v3_production_structure_remediation"
    shutil.copytree(FIXTURE_ROOT, fixture_root)
    replay_path = fixture_root / "replay-report.json"
    replay = json.loads(replay_path.read_text(encoding="utf-8"))
    replay["qualification_credit"] = True
    replay_path.write_text(json.dumps(replay), encoding="utf-8")

    report = _run(fixture_root=fixture_root)

    assert report["technical_completion"] == "mechanical_fail"
    assert report["controls"]["merged_replay_provenance"]["status"] == "fail"


def test_committed_remediated_v3_retrieval_report_is_exactly_bound() -> None:
    report_bytes = REPORT_PATH.read_bytes()
    report = json.loads(report_bytes)
    rebuilt_report = _run(repository_sha=QUALIFICATION_IMPLEMENTATION_SHA)

    assert hashlib.sha256(report_bytes).hexdigest() == REPORT_SHA256
    assert report == rebuilt_report
    assert report["technical_completion"] == "qualified"
    assert report["repository_sha"] == QUALIFICATION_IMPLEMENTATION_SHA
    assert report["fixture_set_sha256"] == FIXTURE_SHA256
    assert report["fixture_count"] == 24
    assert report["passing_fixture_count"] == 24
    assert len(report["retrieval_results"]) == 24
    assert set(report["controls"]) == REQUIRED_CONTROLS
    assert all(
        control["status"] == "pass"
        for control in report["controls"].values()
    )
    assert len(report["fixture_control_results"]) == 24
    assert all(
        set(fixture_controls) == REQUIRED_CONTROLS
        and all(
            control["status"] == "pass"
            for control in fixture_controls.values()
        )
        for fixture_controls in report["fixture_control_results"].values()
    )
    assert report["private_data"] is False
    assert report["provider_execution"] is False
    assert report["runtime_execution"] is False
    assert report["external_model_execution"] is False
    assert report["external_egress"] is False
    assert report["release_decision"] == "defer"
