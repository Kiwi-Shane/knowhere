"""Validation for the versioned local MinerU artifact boundary."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


MINERU_ARTIFACT_SCHEMA_VERSION = "knowhere-mineru-artifacts/1.0"
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_REQUIRED_FILE_ARTIFACTS = (
    "markdown",
    "middle_json",
    "content_list",
    "content_list_v2",
)


class MinerUArtifactContractError(RuntimeError):
    """Raised when a MinerU artifact bundle violates its contract."""


@dataclass(frozen=True)
class CanonicalManifestRequest:
    """Explicit source identity used for an opt-in canonical manifest run."""

    source_id: str
    source_version_id: str
    extraction_run_id: str
    accelerator_profile: str = "unknown"


@dataclass(frozen=True)
class CanonicalMinerUManifest:
    """Validated source-owned manifest metadata consumed by Knowhere."""

    path: Path
    raw: dict[str, Any]


@dataclass(frozen=True)
class MinerUArtifactManifest:
    schema_version: str
    status: str
    source: dict[str, Any]
    parser: dict[str, Any]
    execution: dict[str, Any]
    document: dict[str, Any]
    artifacts: dict[str, Any]
    warnings: tuple[Any, ...]
    raw: dict[str, Any]


@dataclass(frozen=True)
class MinerUArtifactBundle:
    manifest_path: Path
    output_root: Path
    markdown_path: Path
    middle_json_path: Path
    content_list_path: Path
    content_list_v2_path: Path
    images_dir: Path
    manifest: MinerUArtifactManifest
    canonical_manifest_path: Path | None = None
    canonical_manifest: CanonicalMinerUManifest | None = None


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _require_mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MinerUArtifactContractError(f"Manifest field {name!r} must be an object.")
    return value


def _resolve_relative_artifact(output_root: Path, raw_path: Any, name: str) -> Path:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise MinerUArtifactContractError(
            f"Artifact {name!r} must declare a non-empty relative path."
        )
    portable = PurePosixPath(raw_path.replace("\\", "/"))
    if (
        portable.is_absolute()
        or PureWindowsPath(raw_path).is_absolute()
        or ".." in portable.parts
    ):
        raise MinerUArtifactContractError(
            f"Artifact {name!r} must declare a safe relative path."
        )

    root = output_root.resolve()
    candidate = (root / Path(*portable.parts)).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as error:
        raise MinerUArtifactContractError(
            f"Artifact {name!r} must declare a safe relative path."
        ) from error
    return candidate


def _validate_file_artifact(
    output_root: Path,
    artifacts: dict[str, Any],
    name: str,
) -> Path:
    declaration = _require_mapping(artifacts.get(name), f"artifacts.{name}")
    path = _resolve_relative_artifact(output_root, declaration.get("path"), name)
    if not path.is_file():
        raise MinerUArtifactContractError(
            f"Required artifact {name!r} is missing: {path.name}"
        )
    expected_hash = declaration.get("sha256")
    if not isinstance(expected_hash, str) or not _SHA256_PATTERN.fullmatch(
        expected_hash
    ):
        raise MinerUArtifactContractError(
            f"Artifact {name!r} must declare a valid SHA-256 hash."
        )
    if _sha256_file(path) != expected_hash:
        raise MinerUArtifactContractError(f"Artifact hash mismatch for {name!r}.")
    return path


def _load_json_artifact(path: Path, name: str, expected_type: type) -> Any:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MinerUArtifactContractError(
            f"Artifact {name!r} is not valid JSON."
        ) from error
    if not isinstance(payload, expected_type):
        raise MinerUArtifactContractError(
            f"Artifact {name!r} has an invalid JSON structure."
        )
    return payload


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise MinerUArtifactContractError("MinerU manifest is missing.")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise MinerUArtifactContractError(
            "MinerU manifest is not valid JSON."
        ) from error
    return _require_mapping(payload, "manifest")


def validate_canonical_manifest_request(request: CanonicalManifestRequest) -> None:
    """Validate identity before an opt-in producer process is started."""
    for field_name in ("source_id", "source_version_id", "extraction_run_id"):
        value = getattr(request, field_name)
        if not isinstance(value, str) or not value.strip():
            raise MinerUArtifactContractError(
                f"Canonical manifest requires a non-empty {field_name}."
            )
    if (
        not isinstance(request.accelerator_profile, str)
        or not request.accelerator_profile.strip()
    ):
        raise MinerUArtifactContractError(
            "Canonical manifest requires a non-empty accelerator_profile."
        )


def validate_canonical_manifest(
    *,
    manifest_path: Path,
    output_root: Path,
    source_path: Path,
    request: CanonicalManifestRequest,
) -> CanonicalMinerUManifest:
    """Validate producer lineage and hashes without re-owning the source schema."""
    validate_canonical_manifest_request(request)
    root = output_root.expanduser().resolve()
    source = source_path.expanduser().resolve()
    manifest_file = manifest_path.expanduser().resolve()
    if not source.is_file():
        raise MinerUArtifactContractError("Canonical source file is missing.")
    try:
        manifest_file.relative_to(root)
    except ValueError as error:
        raise MinerUArtifactContractError(
            "Canonical manifest must be located under the output root."
        ) from error

    raw = _load_manifest(manifest_file)
    if raw.get("contract_version") != "document-extraction-manifest-v1":
        raise MinerUArtifactContractError(
            "Unsupported canonical manifest contract version."
        )
    if raw.get("status") != "completed":
        raise MinerUArtifactContractError(
            "Canonical manifest status must be completed."
        )
    for field_name in ("source_id", "source_version_id", "extraction_run_id"):
        if raw.get(field_name) != getattr(request, field_name).strip():
            raise MinerUArtifactContractError(
                f"Canonical manifest {field_name} does not match the request."
            )
    if raw.get("input_sha256") != _sha256_file(source):
        raise MinerUArtifactContractError(
            "Canonical manifest source SHA-256 does not match the input."
        )
    if raw.get("derivative_not_native_source_evidence") is not True:
        raise MinerUArtifactContractError(
            "Canonical manifest must identify derivatives as non-native evidence."
        )
    if raw.get("does_not_establish_source_sufficiency") is not True:
        raise MinerUArtifactContractError(
            "Canonical manifest must preserve its source-sufficiency boundary."
        )

    outputs = raw.get("outputs")
    if not isinstance(outputs, list):
        raise MinerUArtifactContractError(
            "Canonical manifest outputs must be an array."
        )
    seen_paths: set[str] = set()
    for index, output in enumerate(outputs):
        declaration = _require_mapping(output, f"outputs[{index}]")
        relative_path = declaration.get("relative_path")
        if not isinstance(relative_path, str) or not relative_path.strip():
            raise MinerUArtifactContractError(
                f"Canonical output {index} must declare a relative path."
            )
        normalized_path = PurePosixPath(relative_path.replace("\\", "/")).as_posix()
        if normalized_path in seen_paths:
            raise MinerUArtifactContractError(
                f"Canonical output path is duplicated: {relative_path}"
            )
        seen_paths.add(normalized_path)
        output_path = _resolve_relative_artifact(
            root,
            relative_path,
            f"canonical output {index}",
        )
        if not output_path.is_file():
            raise MinerUArtifactContractError(
                f"Canonical output is missing: {relative_path}"
            )
        expected_hash = declaration.get("sha256")
        if not isinstance(expected_hash, str) or not _SHA256_PATTERN.fullmatch(
            expected_hash
        ):
            raise MinerUArtifactContractError(
                f"Canonical output has an invalid SHA-256: {relative_path}"
            )
        if _sha256_file(output_path) != expected_hash:
            raise MinerUArtifactContractError(
                f"Canonical output hash mismatch: {relative_path}"
            )

    return CanonicalMinerUManifest(path=manifest_file, raw=raw)


def validate_mineru_artifact_bundle(
    manifest_path: Path,
    output_root: Path,
    source_path: Path,
) -> MinerUArtifactBundle:
    """Validate all declared artifacts and return confined, typed paths."""
    root = output_root.expanduser().resolve()
    source = source_path.expanduser().resolve()
    manifest_file = manifest_path.expanduser().resolve()
    try:
        manifest_file.relative_to(root)
    except ValueError as error:
        raise MinerUArtifactContractError(
            "MinerU manifest must be located under the output root."
        ) from error

    raw = _load_manifest(manifest_file)
    schema_version = raw.get("schema_version")
    if schema_version != MINERU_ARTIFACT_SCHEMA_VERSION:
        raise MinerUArtifactContractError(
            f"Unsupported MinerU artifact schema version: {schema_version!r}"
        )
    if raw.get("status") != "completed":
        raise MinerUArtifactContractError("MinerU manifest status must be completed.")

    source_declaration = _require_mapping(raw.get("source"), "source")
    if source_declaration.get("filename") != source.name:
        raise MinerUArtifactContractError("MinerU manifest source filename mismatch.")
    if source_declaration.get("size_bytes") != source.stat().st_size:
        raise MinerUArtifactContractError("MinerU manifest source size mismatch.")
    expected_source_hash = source_declaration.get("sha256")
    if not isinstance(expected_source_hash, str) or not _SHA256_PATTERN.fullmatch(
        expected_source_hash
    ):
        raise MinerUArtifactContractError("MinerU manifest source SHA-256 is invalid.")
    if _sha256_file(source) != expected_source_hash:
        raise MinerUArtifactContractError("MinerU manifest source hash mismatch.")

    parser = _require_mapping(raw.get("parser"), "parser")
    execution = _require_mapping(raw.get("execution"), "execution")
    document = _require_mapping(raw.get("document"), "document")
    artifacts = _require_mapping(raw.get("artifacts"), "artifacts")
    warnings = raw.get("warnings", [])
    if not isinstance(warnings, list):
        raise MinerUArtifactContractError("Manifest field 'warnings' must be an array.")

    paths = {
        name: _validate_file_artifact(root, artifacts, name)
        for name in _REQUIRED_FILE_ARTIFACTS
    }
    _load_json_artifact(paths["middle_json"], "middle_json", dict)
    _load_json_artifact(paths["content_list"], "content_list", list)
    content_list_v2 = _load_json_artifact(
        paths["content_list_v2"], "content_list_v2", list
    )
    if any(not isinstance(page, list) for page in content_list_v2):
        raise MinerUArtifactContractError(
            "Artifact 'content_list_v2' must contain one array per logical page."
        )

    images_declaration = _require_mapping(
        artifacts.get("images_dir"), "artifacts.images_dir"
    )
    images_dir = _resolve_relative_artifact(
        root, images_declaration.get("path"), "images_dir"
    )
    images_status = images_declaration.get("status")
    if images_status == "not_generated":
        if images_dir.exists():
            raise MinerUArtifactContractError(
                "images_dir is marked not_generated but exists."
            )
    elif images_status is not None:
        raise MinerUArtifactContractError(
            f"Unsupported images_dir status: {images_status!r}"
        )
    elif not images_dir.is_dir():
        raise MinerUArtifactContractError("Required images_dir artifact is missing.")

    manifest = MinerUArtifactManifest(
        schema_version=schema_version,
        status="completed",
        source=source_declaration,
        parser=parser,
        execution=execution,
        document=document,
        artifacts=artifacts,
        warnings=tuple(warnings),
        raw=raw,
    )
    return MinerUArtifactBundle(
        manifest_path=manifest_file,
        output_root=root,
        markdown_path=paths["markdown"],
        middle_json_path=paths["middle_json"],
        content_list_path=paths["content_list"],
        content_list_v2_path=paths["content_list_v2"],
        images_dir=images_dir,
        manifest=manifest,
    )
