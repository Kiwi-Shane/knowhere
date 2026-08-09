"""Validation helpers for the bounded page-memory assist contracts."""

from __future__ import annotations

import hashlib
import json
import math
import re
import stat
from collections.abc import Mapping, Sequence
from pathlib import Path, PurePosixPath
from typing import Any

PAGE_MEMORY_CONTRACT_VERSION = "page-memory-record-v1"
PAGE_RETRIEVAL_CONTRACT_VERSION = "page-retrieval-result-v1"
PRECOMPUTED_VISUAL_BACKEND_ID = "caller_supplied_precomputed_v1"

LEXICAL_WEIGHT = 0.50
VISUAL_WEIGHT = 0.35
SECTION_PROXIMITY_WEIGHT = 0.10
ADJACENT_PAGE_WEIGHT = 0.05
RANKING_WEIGHTS = {
    "lexical_weight": LEXICAL_WEIGHT,
    "visual_weight": VISUAL_WEIGHT,
    "section_proximity_weight": SECTION_PROXIMITY_WEIGHT,
    "adjacent_page_weight": ADJACENT_PAGE_WEIGHT,
}

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_PAGE_ID_RE = re.compile(r"^page-[0-9a-f]{64}$")
_DRIVE_RE = re.compile(r"^[A-Za-z]:")
_REPARSE_POINT = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)


class PageMemoryContractError(ValueError):
    """Raised when page-memory input or retrieval context cannot be trusted."""


def required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PageMemoryContractError(f"{field_name} must be a non-empty string")
    return value.strip()


def validated_sha256(value: object, field_name: str) -> str:
    normalized = required_text(value, field_name)
    if _SHA256_RE.fullmatch(normalized) is None:
        raise PageMemoryContractError(f"{field_name} must be lowercase sha256")
    return normalized


def canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise PageMemoryContractError("value must be canonical JSON data") from error


def canonical_sha256(value: object) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def safe_relative_path(value: object, field_name: str) -> str:
    normalized = required_text(value, field_name).replace("\\", "/")
    if normalized.startswith("/") or _DRIVE_RE.match(normalized):
        raise PageMemoryContractError(f"{field_name} must be a relative path")
    parts = normalized.split("/")
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise PageMemoryContractError(f"{field_name} contains an unsafe path")
    PurePosixPath(*parts)
    return "/".join(parts)


def _has_reparse_component(root: Path, candidate: Path) -> bool:
    try:
        relative_parts = candidate.relative_to(root).parts
    except ValueError as error:
        raise PageMemoryContractError("declared path escapes page root") from error

    current = root
    for part in relative_parts:
        current /= part
        try:
            if current.is_symlink():
                return True
            attributes = getattr(
                current.stat(follow_symlinks=False), "st_file_attributes", 0
            )
        except FileNotFoundError:
            return False
        if attributes & _REPARSE_POINT:
            return True
    return False


def read_declared_file(
    *,
    page_root: Path,
    relative_path: object,
    expected_sha256: object,
    field_name: str,
) -> bytes:
    safe_path = safe_relative_path(relative_path, field_name)
    expected_hash = validated_sha256(expected_sha256, f"{field_name} hash")
    root = page_root.resolve(strict=True)
    unresolved_candidate = root / Path(*safe_path.split("/"))
    if _has_reparse_component(root, unresolved_candidate):
        raise PageMemoryContractError(f"{field_name} must not use a reparse path")
    try:
        candidate = unresolved_candidate.resolve(strict=True)
    except FileNotFoundError as error:
        raise PageMemoryContractError(f"{field_name} file was not found") from error
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise PageMemoryContractError("declared path escapes page root") from error
    if _has_reparse_component(root, candidate):
        raise PageMemoryContractError(f"{field_name} must not use a reparse path")
    if not candidate.is_file():
        raise PageMemoryContractError(f"{field_name} must identify a regular file")
    content = candidate.read_bytes()
    if sha256_bytes(content) != expected_hash:
        raise PageMemoryContractError(f"{field_name} content hash mismatch")
    return content


def validate_manifest(manifest: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    if not isinstance(manifest, Mapping):
        raise PageMemoryContractError("manifest must be a mapping")
    if manifest.get("contract_version") != "page-derivative-manifest-v1":
        raise PageMemoryContractError("unsupported page derivative manifest contract")

    source_id = required_text(manifest.get("source_id"), "source_id")
    source_version_id = required_text(
        manifest.get("source_version_id"), "source_version_id"
    )
    native_sha256 = validated_sha256(manifest.get("native_sha256"), "native_sha256")
    pages = manifest.get("pages")
    if isinstance(pages, (str, bytes)) or not isinstance(pages, Sequence):
        raise PageMemoryContractError("manifest pages must be a sequence")
    page_count = manifest.get("page_count")
    if isinstance(page_count, bool) or not isinstance(page_count, int):
        raise PageMemoryContractError("page_count must be an integer")
    if page_count != len(pages):
        raise PageMemoryContractError("page_count does not match pages")
    safety = manifest.get("safety")
    if not isinstance(safety, Mapping) or not all(
        safety.get(field_name) is True
        for field_name in (
            "derivative_not_native_source_evidence",
            "does_not_establish_source_sufficiency",
        )
    ):
        raise PageMemoryContractError("manifest safety flags are required")

    seen_page_ids: set[str] = set()
    seen_page_numbers: set[int] = set()
    normalized_pages: list[Mapping[str, Any]] = []
    for raw_page in pages:
        if not isinstance(raw_page, Mapping):
            raise PageMemoryContractError("each manifest page must be a mapping")
        identity = raw_page.get("identity")
        if not isinstance(identity, Mapping):
            raise PageMemoryContractError("page identity is required")
        if identity.get("source_id") != source_id:
            raise PageMemoryContractError("page source_id does not match manifest")
        if identity.get("source_version_id") != source_version_id:
            raise PageMemoryContractError(
                "page source_version_id does not match manifest"
            )
        if identity.get("native_sha256") != native_sha256:
            raise PageMemoryContractError("page native_sha256 does not match manifest")
        page_id = required_text(identity.get("page_id"), "page_id")
        if _PAGE_ID_RE.fullmatch(page_id) is None:
            raise PageMemoryContractError("page_id must be a page sha256 identifier")
        if page_id in seen_page_ids:
            raise PageMemoryContractError("manifest page_id values must be unique")
        seen_page_ids.add(page_id)
        page_number = identity.get("page_number")
        if isinstance(page_number, bool) or not isinstance(page_number, int):
            raise PageMemoryContractError("page_number must be an integer")
        if page_number < 1 or page_number in seen_page_numbers:
            raise PageMemoryContractError("manifest page_number values must be unique")
        seen_page_numbers.add(page_number)
        validated_sha256(identity.get("render_sha256"), "render_sha256")
        safe_relative_path(raw_page.get("image_relative_path"), "image_relative_path")
        status = required_text(raw_page.get("native_text_status"), "native_text_status")
        if status not in {"available", "empty", "extraction_warning", "unavailable"}:
            raise PageMemoryContractError("unsupported native_text_status")
        native_text_path = raw_page.get("native_text_relative_path")
        native_text_hash = raw_page.get("native_text_sha256")
        if native_text_path is None:
            if status == "available":
                raise PageMemoryContractError(
                    "available native text requires a native text path"
                )
            if native_text_hash is not None:
                raise PageMemoryContractError(
                    "native_text_sha256 requires a native text path"
                )
        else:
            safe_relative_path(native_text_path, "native_text_relative_path")
            validated_sha256(native_text_hash, "native_text_sha256")
        normalized_pages.append(raw_page)

    return tuple(normalized_pages)


def validate_vector(value: object, field_name: str) -> tuple[float, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise PageMemoryContractError(f"{field_name} must be a numeric sequence")
    vector: list[float] = []
    for item in value:
        if isinstance(item, bool):
            raise PageMemoryContractError(f"{field_name} must contain numbers")
        try:
            number = float(item)
        except (TypeError, ValueError) as error:
            raise PageMemoryContractError(f"{field_name} must contain numbers") from error
        if not math.isfinite(number):
            raise PageMemoryContractError(f"{field_name} must contain finite numbers")
        vector.append(number)
    if not vector:
        raise PageMemoryContractError(f"{field_name} must not be empty")
    return tuple(vector)


def ensure_no_reparse_root(page_root: Path) -> Path:
    raw_root = Path(page_root)
    try:
        raw_attributes = getattr(
            raw_root.stat(follow_symlinks=False), "st_file_attributes", 0
        )
    except FileNotFoundError as error:
        raise PageMemoryContractError("page root was not found") from error
    if raw_root.is_symlink() or raw_attributes & _REPARSE_POINT:
        raise PageMemoryContractError("page root must not be a reparse path")
    root = raw_root.resolve(strict=True)
    if not root.is_dir():
        raise PageMemoryContractError("page root must be a directory")
    return root


def is_valid_case_namespace(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    return "\x00" not in value and len(value.strip()) <= 256


__all__ = [
    "ADJACENT_PAGE_WEIGHT",
    "LEXICAL_WEIGHT",
    "PAGE_MEMORY_CONTRACT_VERSION",
    "PAGE_RETRIEVAL_CONTRACT_VERSION",
    "PageMemoryContractError",
    "PRECOMPUTED_VISUAL_BACKEND_ID",
    "RANKING_WEIGHTS",
    "SECTION_PROXIMITY_WEIGHT",
    "VISUAL_WEIGHT",
    "canonical_json_bytes",
    "canonical_sha256",
    "ensure_no_reparse_root",
    "is_valid_case_namespace",
    "read_declared_file",
    "required_text",
    "safe_relative_path",
    "sha256_bytes",
    "validate_manifest",
    "validate_vector",
    "validated_sha256",
]
