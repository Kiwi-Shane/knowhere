from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from shared.services.retrieval.qualification import (
    canonical_fixture_sha256,
    run_v3_structure_synthetic_qualification,
)


FIXTURE_PATH = (
    Path(__file__).parent
    / "fixtures"
    / "v3_full_layout_v1_2"
    / "fixture-set.json"
)
FIXTURE_SHA256 = (
    "80d59fb7a12bc74be151786a50499b969a706d7974d6dd5c6e99295552fd7a9f"
)


def _fixture() -> dict[str, object]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_v3_profile_qualifies_exact_source_owned_fixture() -> None:
    fixture = _fixture()
    report = run_v3_structure_synthetic_qualification(
        fixture_set=fixture,
        expected_fixture_sha256=FIXTURE_SHA256,
        repository_sha="9c9c5edcba12fd8d17eda5bb5f2358fb4da0982e",
    )

    assert canonical_fixture_sha256(fixture) == FIXTURE_SHA256
    assert report["technical_completion"] == "qualified"
    assert report["qualification_scope"] == "bounded_synthetic"
    assert report["profile_id"] == (
        "pypdf_geometry_full_layout_v1_2_candidate"
    )
    assert report["fixture_count"] == 16
    assert len(report["retrieval_results"]) == 16
    assert all(
        result["contract_version"] == "knowledge-retrieval-result-v1"
        and result["native_source_verification_status"] == "unverified"
        and result["not_source_sufficiency_decision"] is True
        for result in report["retrieval_results"]
    )
    assert report["family_count"] == 8
    assert report["private_data"] is False
    assert report["provider_execution"] is False
    assert report["runtime_execution"] is False
    assert report["release_decision"] == "defer"
    assert all(
        control["status"] == "pass"
        for control in report["controls"].values()
    )


def test_v3_profile_rejects_identity_structure_and_persistence_faults() -> None:
    for fault in (
        "fixture_sha",
        "linked_table_ids",
        "linked_image_ids",
        "continuation_closure",
        "hierarchy_parent_chain",
        "citation_asset_hash",
        "source_allowlist",
        "stale_invalidation",
        "scoped_deletion",
        "prohibited_persisted_text",
    ):
        report = run_v3_structure_synthetic_qualification(
            fixture_set=_fixture(),
            expected_fixture_sha256=FIXTURE_SHA256,
            repository_sha="9c9c5edcba12fd8d17eda5bb5f2358fb4da0982e",
            faults=(fault,),
        )

        assert report["technical_completion"] == "mechanical_fail"
        assert report["controls"][fault]["status"] == "fail"
        assert report["release_decision"] == "defer"


def test_v3_profile_rejects_tampered_candidate_payload() -> None:
    fixture = deepcopy(_fixture())
    fixture["fixtures"][0]["structure_payload"]["critical_tokens"][0][
        "value"
    ] = "tampered"

    report = run_v3_structure_synthetic_qualification(
        fixture_set=fixture,
        expected_fixture_sha256=FIXTURE_SHA256,
        repository_sha="9c9c5edcba12fd8d17eda5bb5f2358fb4da0982e",
    )

    assert report["technical_completion"] == "mechanical_fail"
    assert report["controls"]["fixture_sha"]["status"] == "fail"
    assert report["controls"]["candidate_payload_hash"]["status"] == "fail"
