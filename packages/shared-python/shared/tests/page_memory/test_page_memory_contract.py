from __future__ import annotations

import hashlib
import socket
import urllib.request
from pathlib import Path
from typing import Any

import pytest

from shared.services.page_memory.contracts import PageMemoryContractError
from shared.services.page_memory.deletion import delete_pages
from shared.services.page_memory.index import ingest_page_memory
from shared.services.page_memory.models import PageRetrievalRequest
from shared.services.page_memory.query import (
    classify_retrieval_disposition,
    retrieve_pages,
)
from shared.services.page_memory.storage import PageMemoryStore


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _render_configuration() -> dict[str, Any]:
    return {
        "backend": "pypdfium2",
        "backend_version": "5.10.1",
        "scale": 2.0,
        "pixel_format": "RGB",
        "background": "white",
        "respect_crop_box": True,
        "respect_source_rotation": True,
        "image_format": "PNG",
        "compression": "deterministic",
        "render_options": {
            "draw_annots": False,
            "force_halftone": False,
            "limit_image_cache": False,
            "maybe_alpha": False,
            "may_draw_forms": False,
            "no_smoothimage": False,
            "no_smoothpath": False,
            "no_smoothtext": False,
            "prefer_bgrx": False,
            "rev_byteorder": True,
        },
    }


def _derivative_fixture(
    tmp_path: Path,
    *,
    source_id: str = "SRC-A",
    source_version_id: str = "SRC-A-V1",
) -> tuple[Path, dict[str, Any], tuple[str, ...]]:
    root = tmp_path / f"derivatives-{source_id}-{source_version_id}"
    (root / "pages").mkdir(parents=True)
    (root / "text").mkdir()

    page_texts = (
        "Scope and intended use",
        "Target keyword appears in the methods section",
        "Target keyword is expanded on the following page",
        "Appendix without the target term",
    )
    pages: list[dict[str, Any]] = []
    page_ids: list[str] = []
    for page_number, text in enumerate(page_texts, start=1):
        image_bytes = f"{source_id}|{source_version_id}|render|{page_number}".encode()
        native_text_bytes = text.encode("utf-8")
        render_sha256 = _sha256(image_bytes)
        page_id = "page-" + _sha256(
            f"{source_id}|{source_version_id}|{page_number}|{render_sha256}".encode()
        )
        page_ids.append(page_id)
        image_relative_path = f"pages/{page_id}.png"
        native_text_relative_path = f"text/{page_id}.txt"
        (root / image_relative_path).write_bytes(image_bytes)
        (root / native_text_relative_path).write_bytes(native_text_bytes)
        pages.append(
            {
                "identity": {
                    "source_id": source_id,
                    "source_version_id": source_version_id,
                    "native_sha256": "a" * 64,
                    "page_number": page_number,
                    "render_sha256": render_sha256,
                    "page_id": page_id,
                },
                "image_relative_path": image_relative_path,
                "native_text_status": "available",
                "native_text_relative_path": native_text_relative_path,
                "native_text_sha256": _sha256(native_text_bytes),
                "rotation_degrees": 0,
                "crop_box": [0, 0, 100, 100],
                "width": 100,
                "height": 100,
            }
        )

    manifest = {
        "contract_version": "page-derivative-manifest-v1",
        "source_id": source_id,
        "source_version_id": source_version_id,
        "native_sha256": "a" * 64,
        "page_count": len(pages),
        "configuration": _render_configuration(),
        "pages": pages,
        "safety": {
            "derivative_not_native_source_evidence": True,
            "does_not_establish_source_sufficiency": True,
        },
    }
    return root, manifest, tuple(page_ids)


def _snapshot(
    tmp_path: Path,
    *,
    visual_embeddings: dict[str, tuple[float, ...]] | None = None,
    source_id: str = "SRC-A",
    source_version_id: str = "SRC-A-V1",
):
    root, manifest, page_ids = _derivative_fixture(
        tmp_path,
        source_id=source_id,
        source_version_id=source_version_id,
    )
    snapshot = ingest_page_memory(
        case_namespace="case-alpha",
        manifest=manifest,
        page_root=root,
        visual_embeddings=visual_embeddings,
    )
    return snapshot, root, manifest, page_ids


def _request(
    snapshot: Any,
    *,
    query: str = "target",
    allowed_source_ids: tuple[str, ...] = ("SRC-A",),
    case_namespace: str | None = None,
    source_id: str | None = None,
    source_version_id: str | None = None,
    native_sha256: str = "a" * 64,
    top_k: int = 5,
    visual_query: tuple[float, ...] | None = None,
    visual_backend_id: str | None = None,
    expand_adjacent: bool = False,
    adjacent_radius: int = 1,
) -> PageRetrievalRequest:
    return PageRetrievalRequest(
        request_id="REQ-001",
        case_namespace=case_namespace or snapshot.case_namespace,
        allowed_source_ids=allowed_source_ids,
        source_id=source_id or snapshot.source_id,
        source_version_id=source_version_id or snapshot.source_version_id,
        native_sha256=native_sha256,
        query=query,
        top_k=top_k,
        visual_query=visual_query,
        visual_backend_id=visual_backend_id,
        expand_adjacent=expand_adjacent,
        adjacent_radius=adjacent_radius,
    )


def test_ingest_binds_case_source_version_and_unverified_page_contract(
    tmp_path: Path,
) -> None:
    snapshot, _root, _manifest, _page_ids = _snapshot(tmp_path)

    assert snapshot.contract_version == "page-memory-record-v1"
    assert snapshot.case_namespace == "case-alpha"
    assert snapshot.source_id == "SRC-A"
    assert snapshot.source_version_id == "SRC-A-V1"
    assert snapshot.native_sha256 == "a" * 64
    assert snapshot.lexical_index_status == "ready"
    assert snapshot.visual_index_status == "disabled"
    assert snapshot.verification_status == "exploratory_unverified"

    payload = snapshot.to_dict()
    assert payload["pages"]
    assert all(page["page_manifest_sha256"] == snapshot.page_manifest_sha256 for page in payload["pages"])
    assert all(page["native_text_sha256"] for page in payload["pages"])
    assert "acceptance_status" not in payload
    assert "source_sufficiency" not in payload
    assert "readiness_status" not in payload


def test_ingest_rejects_manifest_path_escape_and_content_hash_mismatch(
    tmp_path: Path,
) -> None:
    root, manifest, _page_ids = _derivative_fixture(tmp_path)
    escaped = manifest.copy()
    escaped["pages"] = [dict(page) for page in manifest["pages"]]
    escaped["pages"][0]["image_relative_path"] = "../outside.png"

    with pytest.raises(PageMemoryContractError, match="path"):
        ingest_page_memory(
            case_namespace="case-alpha",
            manifest=escaped,
            page_root=root,
            visual_embeddings=None,
        )

    (root / manifest["pages"][1]["native_text_relative_path"]).write_text(
        "tampered", encoding="utf-8"
    )
    with pytest.raises(PageMemoryContractError, match="hash"):
        ingest_page_memory(
            case_namespace="case-alpha",
            manifest=manifest,
            page_root=root,
            visual_embeddings=None,
        )


def test_retrieval_rejects_unallowlisted_sources_and_cross_case_requests(
    tmp_path: Path,
) -> None:
    snapshot, _root, _manifest, _page_ids = _snapshot(tmp_path)

    assert retrieve_pages(
        request=_request(snapshot, allowed_source_ids=("SRC-OTHER",)),
        snapshot=snapshot,
    ) == ()
    assert retrieve_pages(
        request=_request(snapshot, case_namespace="case-other"),
        snapshot=snapshot,
    ) == ()


def test_retrieval_rejects_stale_source_version_and_native_hash(
    tmp_path: Path,
) -> None:
    snapshot, _root, _manifest, _page_ids = _snapshot(tmp_path)

    assert retrieve_pages(
        request=_request(snapshot, source_version_id="SRC-A-V2"),
        snapshot=snapshot,
    ) == ()
    assert retrieve_pages(
        request=_request(snapshot, native_sha256="b" * 64),
        snapshot=snapshot,
    ) == ()


def test_duplicate_ingestion_is_idempotent(tmp_path: Path) -> None:
    root, manifest, _page_ids = _derivative_fixture(tmp_path)

    first = ingest_page_memory(
        case_namespace="case-alpha",
        manifest=manifest,
        page_root=root,
        visual_embeddings=None,
    )
    second = ingest_page_memory(
        case_namespace="case-alpha",
        manifest=manifest,
        page_root=root,
        visual_embeddings=None,
    )

    assert second == first
    assert second.memory_snapshot_id == first.memory_snapshot_id


def test_lexical_retrieval_returns_native_locator_and_no_ra_disposition(
    tmp_path: Path,
) -> None:
    snapshot, _root, _manifest, page_ids = _snapshot(tmp_path)

    results = retrieve_pages(
        request=_request(snapshot, query="target", top_k=1),
        snapshot=snapshot,
    )

    assert len(results) == 1
    result = results[0]
    assert result.page_id == page_ids[1]
    assert result.page_number == 2
    assert result.native_page_locator == "SRC-A-V1:p2"
    assert result.match_modes == ("lexical",)
    assert result.verification_status == "unverified"
    assert result.evidence_status == "evidence_lead_only"
    assert result.not_verified_absence is True
    assert result.to_dict()["native_page_locator"] == "SRC-A-V1:p2"
    assert "acceptance_status" not in result.to_dict()
    assert "source_sufficiency" not in result.to_dict()
    assert "readiness_status" not in result.to_dict()


def test_adjacent_page_expansion_is_bounded_to_one_page(tmp_path: Path) -> None:
    snapshot, _root, _manifest, page_ids = _snapshot(tmp_path)

    results = retrieve_pages(
        request=_request(
            snapshot,
            query="target",
            top_k=1,
            expand_adjacent=True,
            adjacent_radius=1,
        ),
        snapshot=snapshot,
    )
    result_by_page_id = {result.page_id: result for result in results}

    assert set(result_by_page_id) == {page_ids[0], page_ids[1], page_ids[2]}
    assert "adjacent_page" in result_by_page_id[page_ids[0]].match_modes
    assert "adjacent_page" in result_by_page_id[page_ids[2]].match_modes
    assert page_ids[3] not in result_by_page_id


def test_deleted_page_is_not_retrievable_or_expanded(tmp_path: Path) -> None:
    snapshot, _root, _manifest, page_ids = _snapshot(tmp_path)
    deleted_snapshot = delete_pages(snapshot, page_ids={page_ids[1]})

    results = retrieve_pages(
        request=_request(
            deleted_snapshot,
            query="methods",
            expand_adjacent=True,
            top_k=5,
        ),
        snapshot=deleted_snapshot,
    )

    assert page_ids[1] not in {result.page_id for result in results}
    assert results == ()


def test_visual_query_requires_exact_precomputed_backend_identity(
    tmp_path: Path,
) -> None:
    root, manifest, page_ids = _derivative_fixture(tmp_path)
    embeddings = {
        page_ids[0]: (0.0, 1.0),
        page_ids[1]: (1.0, 0.0),
        page_ids[2]: (0.8, 0.2),
        page_ids[3]: (0.0, 1.0),
    }
    snapshot = ingest_page_memory(
        case_namespace="case-alpha",
        manifest=manifest,
        page_root=root,
        visual_embeddings=embeddings,
    )

    visual_results = retrieve_pages(
        request=_request(
            snapshot,
            query="",
            visual_query=(1.0, 0.0),
            visual_backend_id="caller_supplied_precomputed_v1",
            top_k=1,
        ),
        snapshot=snapshot,
    )
    assert visual_results[0].page_id == page_ids[1]
    assert visual_results[0].match_modes == ("visual",)

    with pytest.raises(PageMemoryContractError, match="backend"):
        retrieve_pages(
            request=_request(
                snapshot,
                query="",
                visual_query=(1.0, 0.0),
                visual_backend_id="different_backend",
            ),
            snapshot=snapshot,
        )


def test_lexical_only_retrieval_has_no_external_model_or_network_call(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    snapshot, _root, _manifest, _page_ids = _snapshot(tmp_path)

    def fail_external(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("page memory must not call an external service")

    monkeypatch.setattr(socket, "create_connection", fail_external)
    monkeypatch.setattr(urllib.request, "urlopen", fail_external)

    results = retrieve_pages(
        request=_request(snapshot, query="methods", top_k=1),
        snapshot=snapshot,
    )

    assert results[0].page_number == 2
    assert snapshot.external_model_calls is False
    assert snapshot.network_calls is False


def test_empty_retrieval_is_no_result_not_verified_absence(tmp_path: Path) -> None:
    snapshot, _root, _manifest, _page_ids = _snapshot(tmp_path)

    results = retrieve_pages(
        request=_request(snapshot, query="unicorn-zzzz"),
        snapshot=snapshot,
    )

    assert results == ()
    assert classify_retrieval_disposition(results) == "no_result_found"
    assert classify_retrieval_disposition(results) != "verified_absent"


def test_store_invalidates_stale_source_version_without_serving_old_results(
    tmp_path: Path,
) -> None:
    snapshot, _root, _manifest, _page_ids = _snapshot(tmp_path)
    store = PageMemoryStore()
    store.put(snapshot)

    invalidated_ids = store.invalidate_source_version(
        case_namespace="case-alpha",
        source_id="SRC-A",
        source_version_id="SRC-A-V1",
    )

    assert invalidated_ids == (snapshot.memory_snapshot_id,)
    assert store.get(snapshot.memory_snapshot_id, case_namespace="case-alpha") is None
    invalidated_snapshot = store.invalidate_snapshot(snapshot.memory_snapshot_id)
    assert retrieve_pages(
        request=_request(invalidated_snapshot),
        snapshot=invalidated_snapshot,
    ) == ()
