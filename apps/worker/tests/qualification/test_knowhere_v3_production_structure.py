from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest

from shared.services.retrieval.qualification import (
    run_v3_production_structure_synthetic_qualification,
)


FIXTURE_ROOT = (
    Path(__file__).parent / "fixtures" / "v3_production_structure"
)
FIXTURE_PATH = FIXTURE_ROOT / "fixture-set.json"
FIXTURE_SHA256 = (
    "6d368aa27e4dc8f82ff19ec02436b6a4ed53190f324028bfe2aedb198d1de8ec"
)
REPOSITORY_SHA = "b2287e32127ffdb28ab417e811ad5af24c6b4008"
QUALIFICATION_IMPLEMENTATION_SHA = (
    "589bc7a9327b5b9d6ee4cf26351bf2f3a4e145ca"
)
REPORT_PATH = (
    Path(__file__).resolve().parents[4]
    / "examples"
    / "qualification"
    / "v3-production-structure-retrieval"
    / "qualification-report.json"
)
REQUIRED_CONTROLS = {
    "fixture_set_sha",
    "profile_boundary",
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
    faults: tuple[str, ...] = (),
) -> dict[str, object]:
    return run_v3_production_structure_synthetic_qualification(
        fixture_set=fixture_set or _fixture(),
        fixture_root=FIXTURE_ROOT,
        expected_fixture_sha256=FIXTURE_SHA256,
        repository_sha=REPOSITORY_SHA,
        faults=faults,
    )


def test_v3_production_profile_qualifies_all_24_source_owned_fixtures() -> None:
    report = _run()
    fixture_by_id = {
        fixture["fixture_id"]: fixture for fixture in _fixture()["fixtures"]
    }

    assert report["technical_completion"] == "qualified"
    assert report["qualification_scope"] == "bounded_synthetic"
    assert report["profile_id"] == "mineru_complex_layout_structural_v2"
    assert report["fixture_set_sha256"] == FIXTURE_SHA256
    assert report["fixture_count"] == 24
    assert report["passing_fixture_count"] == 24
    assert report["family_count"] == 8
    assert len(report["retrieval_results"]) == 24
    assert set(report["controls"]) == REQUIRED_CONTROLS
    assert all(
        control["status"] == "pass"
        for control in report["controls"].values()
    )
    assert all(
        result["contract_version"] == "knowledge-retrieval-result-v1"
        and result["native_source_verification_status"] == "unverified"
        and result["not_source_sufficiency_decision"] is True
        and result["evidence_lead_only"] is True
        and result["linked_native_object_ids"]
        and result["linked_structure_ids"]
        for result in report["retrieval_results"]
    )
    assert all(
        result["memory_snapshot_sha256"]
        == next(
            output["sha256"]
            for output in fixture_by_id[result["source_id"]][
                "document_extraction_manifest"
            ]["outputs"]
            if output["artifact_type"]
            == "structure-association-result-v1"
        )
        for result in report["retrieval_results"]
    )
    assert report["private_data"] is False
    assert report["provider_execution"] is False
    assert report["runtime_execution"] is False
    assert report["external_model_execution"] is False
    assert report["external_egress"] is False
    assert report["release_decision"] == "defer"


@pytest.mark.parametrize("fault", sorted(REQUIRED_CONTROLS))
def test_v3_production_profile_fails_closed_for_every_control(
    fault: str,
) -> None:
    report = _run(faults=(fault,))

    assert report["technical_completion"] == "mechanical_fail"
    assert report["controls"][fault]["status"] == "fail"
    assert report["release_decision"] == "defer"


def test_v3_production_profile_rejects_object_identity_tampering() -> None:
    fixture = deepcopy(_fixture())
    fixture["fixtures"][0]["native_object_map"]["objects"][0][
        "object_id"
    ] = "NSO-tampered"

    report = _run(fixture_set=fixture)

    assert report["technical_completion"] == "mechanical_fail"
    assert report["controls"]["fixture_set_sha"]["status"] == "fail"
    assert report["controls"]["source_version_object_map_identity"][
        "status"
    ] == "fail"


def test_v3_production_profile_rejects_cross_namespace_retrieval() -> None:
    report = _run(faults=("namespace_isolation",))

    assert report["controls"]["namespace_isolation"]["status"] == "fail"
    assert report["technical_completion"] == "mechanical_fail"


def test_committed_v3_production_retrieval_report_is_exactly_bound() -> None:
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))

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
