from __future__ import annotations

from shared.services.retrieval.qualification import run_d4_synthetic_qualification

REQUIRED_CONTROLS = {
    "contract_edge",
    "source_version_traceability",
    "extraction_block_linkage",
    "source_allowlist",
    "cross_case_isolation",
    "citation",
    "stale_invalidation",
    "scoped_deletion",
    "backup_restore",
    "egress_default_deny",
    "telemetry_disabled",
    "private_data_boundary",
    "ra_evidence_deferred",
}


def test_d4_qualification_passes_all_bounded_controls() -> None:
    report = run_d4_synthetic_qualification(repository_sha="b" * 40)

    assert report["technical_completion"] == "qualified"
    assert report["ra_evidence_state"] == "deferred"
    assert report["release_decision"] == "defer"
    assert set(report["controls"]) == REQUIRED_CONTROLS
    assert all(item["status"] == "pass" for item in report["controls"].values())
    assert report["case_ids"] == ["CASE-SYN-A", "CASE-SYN-B"]
    assert report["private_data"] is False
    assert report["provider_execution"] is False


def test_d4_qualification_fails_closed_when_a_control_is_faulted() -> None:
    report = run_d4_synthetic_qualification(
        repository_sha="b" * 40,
        faults={"cross_case_isolation"},
    )

    assert report["technical_completion"] == "mechanical_fail"
    assert report["controls"]["cross_case_isolation"]["status"] == "fail"
    assert any(issue["code"] == "control_failed" for issue in report["issues"])
    assert report["ra_evidence_state"] == "deferred"
    assert report["release_decision"] == "defer"
