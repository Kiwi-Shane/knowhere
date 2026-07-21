[CmdletBinding()]
param(
    [switch] $LocalMineru
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$expectedWorkerRevision = "e0502809"
if ($LocalMineru) {
    $expectedWorkerRevision = [string]$env:KNOWHERE_SOURCE_REVISION
    if ($expectedWorkerRevision -notmatch "^[0-9a-f]{40}$") {
        throw "KNOWHERE_SOURCE_REVISION must be a full 40-character commit SHA for local verification"
    }
}

$d2RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$d2BaseCompose = Join-Path $d2RepoRoot "deploy\local-dev\docker-compose.dev.yml"
$d2OverrideCompose = Join-Path $d2RepoRoot "deploy\local-dev\docker-compose.d2.yml"
$d2LocalMineruOverlay = Join-Path $d2RepoRoot "deploy\local-dev\docker-compose.d2-local-mineru.yml"
$d2ComposeArgs = @(
    "compose"
    "-p"
    "knowhere-d2-hardened"
    "-f"
    $d2BaseCompose
    "-f"
    $d2OverrideCompose
)
if ($LocalMineru) {
    $d2ComposeArgs += @("-f", $d2LocalMineruOverlay)
}

function Invoke-D2DockerText {
    param(
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments
    )

    $text = (& docker @Arguments 2>&1 | Out-String).Trim()
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "docker command failed with exit ${exitCode}: $text"
    }
    return $text
}

function Invoke-D2ComposeText {
    param(
        [Parameter(Mandatory = $true)]
        [string[]] $Arguments
    )

    return Invoke-D2DockerText ($d2ComposeArgs + $Arguments)
}

function Assert-D2 {
    param(
        [Parameter(Mandatory = $true)]
        [bool] $Condition,
        [Parameter(Mandatory = $true)]
        [string] $Message
    )

    if (-not $Condition) {
        throw $Message
    }
}

try {
    $effective = Invoke-D2ComposeText @("config", "--format", "json") | ConvertFrom-Json
    Assert-D2 ($effective.networks.knowhere_network.internal -eq $true) `
        "effective D2 network is not internal"

    if ($LocalMineru) {
        $effectiveWorker = $effective.services.worker
        $effectiveWorkerEnvironment = $effectiveWorker.environment
        Assert-D2 ($effectiveWorkerEnvironment.MINERU_PROVIDER -eq "local") `
            "MINERU_PROVIDER=local is required for local verification"
        Assert-D2 ($effectiveWorkerEnvironment.MINERU_LOCAL_MODEL_ROOT -eq "/mnt/models/mineru") `
            "MINERU_LOCAL_MODEL_ROOT=/mnt/models/mineru is required for local verification"
        $effectiveModelMount = @(
            $effectiveWorker.volumes | Where-Object { $_.target -eq "/mnt/models/mineru" }
        )
        Assert-D2 ($effectiveModelMount.Count -eq 1) `
            "local verification requires exactly one MinerU model mount"
        Assert-D2 ($effectiveModelMount[0].read_only -eq $true) `
            "local MinerU model mount is not read-only"
    }

    $serviceNames = @("redis", "postgres", "localstack", "api", "worker")
    foreach ($serviceName in $serviceNames) {
        $containerName = "knowhere_d2_$serviceName"
        $inspect = (Invoke-D2DockerText @("inspect", $containerName) | ConvertFrom-Json)[0]
        Assert-D2 ($inspect.State.Status -eq "running") "$containerName is not running"
        Assert-D2 ($inspect.State.Health.Status -eq "healthy") "$containerName is not healthy"
        Assert-D2 ($inspect.HostConfig.Memory -gt 0) "$containerName has no memory limit"
        Assert-D2 ($inspect.HostConfig.NanoCpus -gt 0) "$containerName has no CPU limit"
        Assert-D2 ($inspect.HostConfig.PidsLimit -gt 0) "$containerName has no PID limit"
        Assert-D2 ($inspect.HostConfig.ReadonlyRootfs -eq $true) "$containerName is not read-only"
        Assert-D2 (@($inspect.HostConfig.CapDrop) -contains "ALL") "$containerName does not drop all capabilities"
        Assert-D2 (@($inspect.HostConfig.SecurityOpt) -contains "no-new-privileges:true") `
            "$containerName does not enable no-new-privileges"

        $publishedPorts = (& docker port $containerName 2>&1 | Out-String).Trim()
        $portExitCode = $LASTEXITCODE
        Assert-D2 ($portExitCode -eq 0 -and [string]::IsNullOrWhiteSpace($publishedPorts)) `
            "$containerName has a published host port: $publishedPorts"
    }
    Write-Output "D2 stage: container restrictions and host-port checks completed."

    $network = (Invoke-D2DockerText @("network", "inspect", "knowhere_d2_internal") | ConvertFrom-Json)[0]
    Assert-D2 ($network.Internal -eq $true) "Docker network is not internal"
    Assert-D2 (@($network.Containers.PSObject.Properties).Count -eq 5) `
        "D2 network does not contain three dependencies and two application services"
    Write-Output "D2 stage: internal network checks completed."

    $null = Invoke-D2DockerText @("exec", "knowhere_d2_redis", "redis-cli", "ping")
    $null = Invoke-D2DockerText @("exec", "knowhere_d2_postgres", "pg_isready", "-U", "root", "-d", "Knowhere")
    $null = Invoke-D2DockerText @("exec", "knowhere_d2_localstack", "curl", "-fsS", "--max-time", "5", "http://127.0.0.1:4566/_localstack/health")
    $null = Invoke-D2DockerText @("exec", "knowhere_d2_postgres", "sh", "-c", "test -s /run/secrets/postgres_password")
    Write-Output "D2 stage: dependency health and secret checks completed."

    foreach ($bucketName in @("d2-synthetic-uploads", "d2-synthetic-results")) {
        $bucketCommand = "awslocal s3api head-bucket --bucket $bucketName >/dev/null 2>&1 || awslocal s3 mb s3://$bucketName >/dev/null"
        $null = Invoke-D2DockerText @("exec", "knowhere_d2_localstack", "sh", "-c", $bucketCommand)
    }
    Write-Output "D2 stage: internal S3 synthetic buckets are ready."

    $expectedDatabaseUrl = "DATABASE_URL=postgresql+asyncpg://root@postgres:5432/Knowhere"
    foreach ($serviceName in @("api", "worker")) {
        $containerName = "knowhere_d2_$serviceName"
        $inspect = (Invoke-D2DockerText @("inspect", $containerName) | ConvertFrom-Json)[0]
        $environment = @($inspect.Config.Env)
        Assert-D2 ($environment -contains "TELEMETRY_ENABLED=false") `
            "$containerName does not have telemetry disabled at runtime"
        Assert-D2 ($environment -contains "DATABASE_PASSWORD_FILE=/run/secrets/postgres_password") `
            "$containerName does not use the file-backed database password"
        Assert-D2 ($environment -contains $expectedDatabaseUrl) `
            "$containerName exposes a database URL with an embedded password or unexpected host"
        if ($serviceName -eq "worker") {
            Assert-D2 ($environment -contains "GIT_COMMIT=$expectedWorkerRevision") `
                "$containerName is not bound to the characterized source revision"
            Assert-D2 ($environment -contains "WORKER_HEARTBEAT_FILE=/tmp/knowhere-worker-heartbeat.json") `
                "$containerName does not expose the expected heartbeat path"
            if ($LocalMineru) {
                Assert-D2 ($environment -contains "MINERU_PROVIDER=local") `
                    "$containerName does not have MINERU_PROVIDER=local"
                Assert-D2 ($environment -contains "MINERU_LOCAL_MODEL_ROOT=/mnt/models/mineru") `
                    "$containerName does not have MINERU_LOCAL_MODEL_ROOT=/mnt/models/mineru"
                $modelMount = @(
                    $inspect.Mounts | Where-Object { $_.Destination -eq "/mnt/models/mineru" }
                )
                Assert-D2 ($modelMount.Count -eq 1 -and $modelMount[0].RW -eq $false) `
                    "$containerName MinerU model mount is not read-only"
            }
        } else {
            Assert-D2 ($environment -contains "GIT_COMMIT=e0502809") `
                "$containerName is not bound to the characterized source revision"
        }
        $null = Invoke-D2DockerText @("exec", $containerName, "sh", "-c", "test -s /run/secrets/postgres_password")
    }
    Write-Output "D2 stage: application runtime environment checks completed."

    $apiHealth = Invoke-D2DockerText @("exec", "knowhere_d2_api", "curl", "-fsS", "http://127.0.0.1:5005/health") |
        ConvertFrom-Json
    Assert-D2 ($apiHealth.status -eq "healthy") "API health endpoint did not report healthy"
    $null = Invoke-D2DockerText @(
        "exec", "knowhere_d2_worker", "python", "-c",
        "from shared.services.worker_health import assert_worker_healthy; assert_worker_healthy()"
    )
    $null = Invoke-D2DockerText @(
        "exec", "knowhere_d2_worker", "sh", "-c",
        "test -s /tmp/knowhere-worker-heartbeat.json"
    )
    Write-Output "D2 stage: API and worker health checks completed."

    if ($LocalMineru) {
        $integratedMineruProbe = @'
import asyncio
import hashlib
import json
import time
import zipfile
from pathlib import Path
from uuid import uuid4

from sqlalchemy import delete, select, text

from app.services.documents.lifecycle_service import DocumentService
from shared.core.celery_app import get_celery_app
from shared.core.celery_router import task_router
from shared.core.database import AsyncSessionFactory
from shared.core.database_sync import get_sync_engine
from shared.models.database.document import (
    Document,
    DocumentChunk,
    DocumentSection,
    GraphEdge,
    GraphNode,
)
from shared.models.database.job import Job
from shared.models.database.job_result import JobResult
from shared.models.database.user import User
from shared.services.retrieval.app_service import run_retrieval_query
from shared.services.storage.job_file_storage import JobFileStorage


_TASK_NAME = "app.core.tasks.document_ingestion_tasks.parse_task"
_JOB_TYPE = "document_ingestion"


def _pdf_escape(value: str) -> bytes:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("ascii")


def _write_synthetic_pdf(path: Path, *, title: str, marker: str) -> None:
    stream = b"\n".join(
        [
            b"BT",
            b"/F1 18 Tf",
            b"72 730 Td",
            b"(" + _pdf_escape(title) + b") Tj",
            b"0 -34 Td",
            b"/F1 14 Tf",
            b"(1. Integrated Locator) Tj",
            b"0 -30 Td",
            b"/F1 10 Tf",
            b"(" + _pdf_escape(marker) + b") Tj",
            b"0 -26 Td",
            b"(Synthetic public qualification content; no client data.) Tj",
            b"ET",
        ]
    )
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    document = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"
    offsets = [0]
    for object_number, payload in enumerate(objects, start=1):
        offsets.append(len(document))
        document += f"{object_number} 0 obj\n".encode("ascii")
        document += payload + b"\nendobj\n"
    xref_offset = len(document)
    document += b"xref\n0 6\n0000000000 65535 f \n"
    document += b"".join(
        f"{offset:010d} 00000 n \n".encode("ascii") for offset in offsets[1:]
    )
    document += (
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n"
        + str(xref_offset).encode("ascii")
        + b"\n%%EOF\n"
    )
    path.write_bytes(document)


def _poll_job(engine, job_id: str) -> dict[str, object]:
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        with engine.connect() as connection:
            row = connection.execute(
                text(
                    """
                    SELECT status, error_code, error_message, page_count
                    FROM jobs
                    WHERE job_id = :job_id
                    """
                ),
                {"job_id": job_id},
            ).mappings().one()
        if row["status"] in {"done", "failed"}:
            return dict(row)
        time.sleep(2)
    raise AssertionError(f"local MinerU parse task timed out: job_id={job_id}")


def _result_snapshot(engine, *, job_id: str) -> dict[str, object]:
    with engine.connect() as connection:
        result_row = connection.execute(
            text(
                """
                SELECT id, document_id, result_s3_key, document_metadata
                FROM job_results
                WHERE job_id = :job_id
                """
            ),
            {"job_id": job_id},
        ).mappings().one_or_none()
        assert result_row is not None, "successful parse did not publish a job result"
        document_id = result_row["document_id"]
        assert document_id, "successful parse did not publish a document id"
        document_row = connection.execute(
            text(
                """
                SELECT document_id, status, source_file_name, document_metadata
                FROM documents
                WHERE document_id = :document_id
                """
            ),
            {"document_id": document_id},
        ).mappings().one()
        chunk_rows = connection.execute(
            text(
                """
                SELECT content, source_chunk_path, chunk_metadata
                FROM document_chunks
                WHERE document_id = :document_id
                ORDER BY sort_order
                """
            ),
            {"document_id": document_id},
        ).mappings().all()
        section_rows = connection.execute(
            text(
                """
                SELECT section_path
                FROM document_sections
                WHERE document_id = :document_id
                ORDER BY sort_order
                """
            ),
            {"document_id": document_id},
        ).mappings().all()
    return {
        "result": dict(result_row),
        "document": dict(document_row),
        "chunks": [dict(row) for row in chunk_rows],
        "sections": [dict(row) for row in section_rows],
    }


def _enqueue_parse(*, job_id: str, user_id: str) -> None:
    queue_name = task_router.get_queue_for_job(_JOB_TYPE, user_id)
    signature = get_celery_app().signature(
        _TASK_NAME,
        args=[job_id],
        kwargs={"user_id": user_id, "job_type": _JOB_TYPE},
    ).set(queue=queue_name)
    signature.apply_async()


def _matching_results(response: dict[str, object], document_id: str) -> list[dict[str, object]]:
    raw_results = response.get("results")
    if not isinstance(raw_results, list):
        return []
    matches: list[dict[str, object]] = []
    for raw_result in raw_results:
        if not isinstance(raw_result, dict):
            continue
        source = raw_result.get("source")
        if isinstance(source, dict) and source.get("document_id") == document_id:
            matches.append(raw_result)
    return matches


async def _retrieval(
    db,
    *,
    user_id: str,
    namespace: str,
    marker: str,
) -> dict[str, object]:
    return await run_retrieval_query(
        db=db,
        user_id=user_id,
        namespace=namespace,
        query=marker,
        top_k=10,
        exclude_document_ids=[],
        exclude_sections=[],
        channels=["content"],
        use_agentic=False,
    )


async def _cleanup_rows(
    *,
    user_id: str,
    job_id: str,
    document_id: str | None,
) -> None:
    async with AsyncSessionFactory() as db:
        if document_id:
            await db.execute(
                delete(GraphEdge).where(
                    (GraphEdge.owner_document_id == document_id)
                    | (GraphEdge.source_node_id == f"doc:{document_id}")
                    | (GraphEdge.target_node_id == f"doc:{document_id}")
                )
            )
            await db.execute(delete(GraphNode).where(GraphNode.owner_document_id == document_id))
            await db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
            await db.execute(delete(DocumentSection).where(DocumentSection.document_id == document_id))
            await db.execute(delete(Document).where(Document.document_id == document_id))
        await db.execute(delete(JobResult).where(JobResult.job_id == job_id))
        await db.execute(delete(Job).where(Job.job_id == job_id))
        await db.execute(delete(User).where(User.id == user_id))
        await db.commit()


async def main() -> None:
    engine = get_sync_engine()
    storage = JobFileStorage()
    service = DocumentService()
    user_id = f"d2-local-mineru-{uuid4().hex[:12]}"
    namespace = f"d2-local-mineru-{uuid4().hex[:12]}"
    job_id = str(uuid4())
    source_file_name = "d2-local-mineru-integrated.pdf"
    source_key = f"uploads/{job_id}.pdf"
    source_path = Path(f"/tmp/{job_id}-source.pdf")
    result_zip_path = Path(f"/tmp/{job_id}-result.zip")
    document_id: str | None = None
    marker = f"D2LOCALMINERURETRIEVALMARKER{uuid4().hex}"

    try:
        _write_synthetic_pdf(
            source_path,
            title="D2 Local MinerU Integrated Retrieval Fixture",
            marker=marker,
        )
        source_sha256 = hashlib.sha256(source_path.read_bytes()).hexdigest()
        job_metadata = {
            "namespace": namespace,
            "source_type": "file",
            "source_file_name": source_file_name,
            "parse_track": "chunk",
            "document_metadata": {
                "synthetic": True,
                "fixture": "d2-local-mineru-integrated-retrieval",
                "source_sha256": source_sha256,
            },
            "parsing_params": {
                "doc_type": "auto",
                "smart_title_parse": False,
                "summary_image": False,
                "summary_table": False,
                "summary_txt": False,
                "summary_use_llm": False,
            },
        }
        async with AsyncSessionFactory() as db:
            db.add(
                User(
                    id=user_id,
                    name="D2 local MinerU synthetic user",
                    email=f"{user_id}@example.invalid",
                )
            )
            await db.flush()
            db.add(
                Job(
                    job_id=job_id,
                    user_id=user_id,
                    job_type=_JOB_TYPE,
                    status="pending",
                    source_type="file",
                    file_path=source_file_name,
                    s3_key=source_key,
                    webhook_enabled=False,
                    job_metadata=job_metadata,
                    credits_charged=0,
                    billing_status="pending",
                )
            )
            await db.commit()

        upload_result = storage.upload_source_file(str(source_path), source_key)
        assert upload_result.get("status") == "success", upload_result
        assert storage.verify_upload_exists(source_key)["exists"] is True
        _enqueue_parse(job_id=job_id, user_id=user_id)

        job_status = _poll_job(engine, job_id)
        assert job_status["status"] == "done", (
            f"local MinerU parse failed: status={job_status['status']} "
            f"error_code={job_status['error_code']} error={job_status['error_message']}"
        )
        snapshot = _result_snapshot(engine, job_id=job_id)
        result_row = snapshot["result"]
        document_row = snapshot["document"]
        assert isinstance(result_row, dict)
        assert isinstance(document_row, dict)
        document_id = str(result_row["document_id"])
        assert document_row["status"] == "active"
        assert document_row["source_file_name"] == source_file_name
        assert document_row["document_metadata"]["source_sha256"] == source_sha256

        chunk_rows = snapshot["chunks"]
        section_rows = snapshot["sections"]
        assert isinstance(chunk_rows, list) and chunk_rows, "no document chunks were published"
        chunk_samples = [
            {
                "content_prefix": str(row.get("content") or "")[:240],
                "source_chunk_path": row.get("source_chunk_path"),
            }
            for row in chunk_rows[:5]
        ]
        assert any(marker in str(row.get("content") or "") for row in chunk_rows), (
            "synthetic retrieval marker was not preserved in published content: "
            + json.dumps(chunk_samples, ensure_ascii=False)
        )
        locator_paths = [
            str(row.get("source_chunk_path"))
            for row in chunk_rows
            if row.get("source_chunk_path")
        ] + [
            str(row.get("section_path"))
            for row in section_rows
            if row.get("section_path")
        ]
        assert locator_paths, "no published locator path was recorded"
        assert any(path.strip().lower() != "root" for path in locator_paths)

        result_s3_key = result_row["result_s3_key"]
        assert isinstance(result_s3_key, str) and result_s3_key
        storage.download_to_path(
            result_s3_key,
            str(result_zip_path),
            bucket=storage.results_bucket,
        )
        with zipfile.ZipFile(result_zip_path) as archive:
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            chunks_payload = json.loads(archive.read("chunks.json").decode("utf-8"))
        assert manifest["job_id"] == job_id
        assert manifest["source_file_name"] == source_file_name
        assert manifest["statistics"]["total_chunks"] > 0
        assert chunks_payload["chunks"]

        async with AsyncSessionFactory() as db:
            retrieval_before = await _retrieval(
                db,
                user_id=user_id,
                namespace=namespace,
                marker=marker,
            )
            matches = _matching_results(retrieval_before, document_id)
            assert matches, "integrated retrieval did not return the published document"
            marker_matches = [
                item
                for item in matches
                if marker in json.dumps(item, ensure_ascii=False)
            ]
            assert marker_matches, "integrated retrieval did not return the marker content"
            retrieval_hit = marker_matches[0]
            source = retrieval_hit.get("source")
            assert isinstance(source, dict)
            retrieval_locator = source.get("section_path") or retrieval_hit.get("source_chunk_path")
            assert retrieval_locator and str(retrieval_locator).strip().lower() != "root"

            other_user_results = await _retrieval(
                db,
                user_id=f"{user_id}-other",
                namespace=namespace,
                marker=marker,
            )
            other_namespace_results = await _retrieval(
                db,
                user_id=user_id,
                namespace=f"{namespace}-other",
                marker=marker,
            )
            assert not _matching_results(other_user_results, document_id)
            assert not _matching_results(other_namespace_results, document_id)

            archived = await service.archive_document(
                db,
                user_id=user_id,
                document_id=document_id,
            )
            assert archived is not None and archived["status"] == "archived"
            after_archive = await _retrieval(
                db,
                user_id=user_id,
                namespace=namespace,
                marker=marker,
            )
            assert not _matching_results(after_archive, document_id)

            deleted = await service.delete_document(
                db,
                user_id=user_id,
                document_id=document_id,
            )
            assert deleted == {"document_id": document_id, "deleted": True}
            after_delete = await _retrieval(
                db,
                user_id=user_id,
                namespace=namespace,
                marker=marker,
            )
            assert not _matching_results(after_delete, document_id)

        assert not storage.verify_upload_exists(source_key)["exists"]
        assert not storage.verify_exists(
            result_s3_key,
            bucket=storage.results_bucket,
        )["exists"]
        assert not list(
            storage.storage_adapter.list_objects(
                prefix=f"results/{job_id}/",
                bucket=storage.results_bucket,
            )
        )
        with engine.connect() as connection:
            assert connection.execute(
                text("SELECT COUNT(*) FROM jobs WHERE job_id = :job_id"),
                {"job_id": job_id},
            ).scalar_one() == 0
            assert connection.execute(
                text("SELECT COUNT(*) FROM job_results WHERE job_id = :job_id"),
                {"job_id": job_id},
            ).scalar_one() == 0
        print(
            "D2 local MinerU integrated retrieval probe passed: parse task, "
            "publication, source hash, locator, cross-scope isolation, archive "
            "exclusion, hard-delete storage cleanup, and retrieval non-visibility."
        )
    finally:
        try:
            storage.delete_upload_file(source_key)
            storage.delete_result_bundle(job_id=job_id)
        finally:
            await _cleanup_rows(
                user_id=user_id,
                job_id=job_id,
                document_id=document_id,
            )
            source_path.unlink(missing_ok=True)
            result_zip_path.unlink(missing_ok=True)


asyncio.run(main())
'@
        Write-Output "D2 stage: local MinerU integrated retrieval probe starting."
        $integratedMineruPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            $integratedMineruOutput = ($integratedMineruProbe | & docker exec -i knowhere_d2_api env PYTHONWARNINGS=ignore python - 2>&1 | Out-String).Trim()
            $integratedMineruExitCode = $LASTEXITCODE
        }
        finally {
            $ErrorActionPreference = $integratedMineruPreference
        }
        if ($integratedMineruExitCode -ne 0 -or $integratedMineruOutput -notlike "*D2 local MinerU integrated retrieval probe passed*") {
            Write-Output "D2 local MinerU integrated retrieval probe diagnostic (exit=$integratedMineruExitCode):"
            Write-Output $integratedMineruOutput
        }
        Assert-D2 ($integratedMineruExitCode -eq 0) "D2 local MinerU integrated retrieval probe failed: $integratedMineruOutput"
        Assert-D2 ($integratedMineruOutput -like "*D2 local MinerU integrated retrieval probe passed*") `
            "D2 local MinerU integrated retrieval probe did not report success: $integratedMineruOutput"
        Write-Output "D2 local MinerU integrated retrieval probe completed."
    }

    $lifecycleProbe = @'
import asyncio
from uuid import uuid4

from sqlalchemy import delete, select

from app.services.documents.lifecycle_service import DocumentService
from shared.core.database import AsyncSessionFactory
from shared.models.database.document import Document, DocumentChunk, GraphEdge, GraphNode
from shared.models.database.job import Job
from shared.models.database.job_result import JobResult
from shared.services.retrieval.app_service import run_retrieval_query
from shared.services.storage.job_file_storage import JobFileStorage
from shared.services.storage.result_storage import JobResultStorage
from shared.models.database.user import User
from pathlib import Path


def _document_id() -> str:
    return f"doc_{uuid4().hex[:12]}"


async def _rollback_probe() -> None:
    sentinel_id = f"d2-rollback-{uuid4().hex[:8]}"
    async with AsyncSessionFactory() as db:
        try:
            async with db.begin():
                db.add(
                    User(
                        id=sentinel_id,
                        name="D2 rollback sentinel",
                        email=f"{sentinel_id}@example.invalid",
                    )
                )
                await db.flush()
                raise RuntimeError("synthetic rollback sentinel")
        except RuntimeError:
            pass

        remaining = await db.scalar(select(User.id).where(User.id == sentinel_id))
        assert remaining is None, "failed transaction left a user row behind"


async def _lifecycle_probe() -> None:
    user_a_id = f"d2-scope-a-{uuid4().hex[:8]}"
    user_b_id = f"d2-scope-b-{uuid4().hex[:8]}"
    namespace_a = f"d2-scope-a-{uuid4().hex[:8]}"
    namespace_b = f"d2-scope-b-{uuid4().hex[:8]}"
    users = [
        User(
            id=user_a_id,
            name="D2 scope user A",
            email=f"{user_a_id}@example.invalid",
        ),
        User(
            id=user_b_id,
            name="D2 scope user B",
            email=f"{user_b_id}@example.invalid",
        ),
    ]
    specs = [
        (user_a_id, namespace_a, "target"),
        (user_a_id, namespace_a, "peer"),
        (user_b_id, namespace_a, "other-user"),
        (user_a_id, namespace_b, "other-namespace"),
    ]
    document_ids: list[str] = []
    job_ids: list[str] = []
    result_ids: list[str] = []
    chunk_ids: list[str] = []
    retrieval_marker = f"d2-hard-delete-marker-{uuid4().hex}"
    documents: list[Document] = []
    jobs: list[Job] = []
    results: list[JobResult] = []
    nodes: list[GraphNode] = []

    for user_id, namespace, label in specs:
        document_id = _document_id()
        job_id = str(uuid4())
        result_id = str(uuid4())
        document_ids.append(document_id)
        job_ids.append(job_id)
        result_ids.append(result_id)
        upload_key = f"uploads/{job_id}.pdf" if label == "target" else None
        result_key = f"results/{job_id}.zip" if label == "target" else None
        jobs.append(
            Job(
                job_id=job_id,
                user_id=user_id,
                job_type="document_ingestion",
                status="done",
                source_type="direct_upload",
                file_path=f"/synthetic/{label}.pdf",
                s3_key=upload_key,
            )
        )
        results.append(
            JobResult(
                id=result_id,
                job_id=job_id,
                delivery_mode="inline",
                inline_payload={"synthetic": label},
                result_s3_key=result_key,
            )
        )
        documents.append(
            Document(
                document_id=document_id,
                user_id=user_id,
                namespace=namespace,
                status="active",
                current_job_result_id=result_id,
                source_file_name=f"{label}.pdf",
            )
        )
        nodes.append(
            GraphNode(
                node_id=f"doc:{document_id}",
                user_id=user_id,
                namespace=namespace,
                node_kind="document",
                owner_document_id=document_id,
                job_result_id=result_id,
                ref_document_id=document_id,
                properties={"synthetic": True, "label": label},
            )
        )

    target_id, peer_id, other_user_id, other_namespace_id = document_ids
    edge_id = f"d2-edge-{uuid4().hex[:12]}"

    async with AsyncSessionFactory() as db:
        try:
            db.add_all(users)
            await db.flush()
            db.add_all(jobs)
            await db.flush()
            db.add_all(results)
            await db.flush()
            db.add_all(documents)
            await db.flush()
            for result, document in zip(results, documents):
                result.document_id = document.document_id
            await db.flush()
            db.add_all(nodes)
            await db.flush()
            db.add(
                GraphEdge(
                    edge_id=edge_id,
                    user_id=user_a_id,
                    namespace=namespace_a,
                    edge_kind="related",
                    source_node_id=f"doc:{target_id}",
                    target_node_id=f"doc:{peer_id}",
                    owner_document_id=target_id,
                    job_result_id=results[0].id,
                    is_directed=False,
                )
            )
            chunk_id = f"dchk_{uuid4().hex[:12]}"
            chunk_ids.append(chunk_id)
            db.add(
                DocumentChunk(
                    id=chunk_id,
                    chunk_id=f"d2-hard-delete-chunk-{uuid4().hex[:8]}",
                    user_id=user_a_id,
                    namespace=namespace_a,
                    document_id=target_id,
                    job_result_id=results[0].id,
                    chunk_type="text",
                    content=retrieval_marker,
                    content_lexical_text=retrieval_marker,
                    content_search_text=retrieval_marker,
                    term_search_text=retrieval_marker,
                    source_chunk_path="D2/Hard Delete",
                    chunk_metadata={"synthetic": True},
                    sort_order=0,
                )
            )
            await db.commit()

            service = DocumentService()
            file_storage = JobFileStorage()
            result_storage = JobResultStorage(
                results_bucket=file_storage.results_bucket,
                storage_adapter=file_storage.storage_adapter,
            )
            target_job = jobs[0]
            assert target_job.s3_key is not None
            upload_key = target_job.s3_key
            result_zip_key = result_storage.build_zip_key(job_id=target_job.job_id)
            local_fixture = Path(f"/tmp/d2-hard-delete-{target_job.job_id}.pdf")
            local_fixture.write_bytes(b"d2 synthetic hard-delete artifact")
            try:
                file_storage.upload_local_file(
                    str(local_fixture),
                    upload_key,
                    bucket=file_storage.uploads_bucket,
                )
                file_storage.upload_local_file(
                    str(local_fixture),
                    result_zip_key,
                    bucket=result_storage.results_bucket,
                )
                result_storage.upload_raw_file(
                    job_id=target_job.job_id,
                    relative_path="source.pdf",
                    local_file_path=str(local_fixture),
                )
            finally:
                local_fixture.unlink(missing_ok=True)

            retrieval_before = await run_retrieval_query(
                db=db,
                user_id=user_a_id,
                namespace=namespace_a,
                query=retrieval_marker,
                top_k=10,
                exclude_document_ids=[],
                exclude_sections=[],
                channels=["content"],
                use_agentic=False,
            )
            retrieval_before_ids = {
                item["source"]["document_id"]
                for item in retrieval_before["results"]
            }
            assert target_id in retrieval_before_ids

            async def visible(user_id: str, namespace: str) -> set[str]:
                response = await service.list_documents(
                    db,
                    user_id=user_id,
                    namespace=namespace,
                    page=1,
                    page_size=20,
                )
                return {item["document_id"] for item in response["documents"]}

            assert await visible(user_a_id, namespace_a) == {target_id, peer_id}
            assert await visible(user_b_id, namespace_a) == {other_user_id}
            assert await visible(user_a_id, namespace_b) == {other_namespace_id}
            assert (
                await service.get_document(
                    db,
                    user_id=user_b_id,
                    document_id=target_id,
                )
                is None
            ), "cross-user document lookup bypassed ownership scope"

            archived = await service.archive_document(
                db,
                user_id=user_a_id,
                document_id=target_id,
            )
            assert archived is not None and archived["status"] == "archived"
            assert await visible(user_a_id, namespace_a) == {peer_id}
            assert await visible(user_b_id, namespace_a) == {other_user_id}
            assert await visible(user_a_id, namespace_b) == {other_namespace_id}

            archived_row = await db.scalar(
                select(Document).where(Document.document_id == target_id)
            )
            assert archived_row is not None and archived_row.status == "archived"
            target_nodes = (
                await db.execute(
                    select(GraphNode).where(GraphNode.owner_document_id == target_id)
                )
            ).scalars().all()
            assert not target_nodes, "archived graph node residue remains"
            target_edges = (
                await db.execute(
                    select(GraphEdge).where(
                        (GraphEdge.owner_document_id == target_id)
                        | (GraphEdge.source_node_id == f"doc:{target_id}")
                        | (GraphEdge.target_node_id == f"doc:{target_id}")
                    )
                )
            ).scalars().all()
            assert not target_edges, "archived graph edge residue remains"
            peer_node = await db.scalar(
                select(GraphNode).where(GraphNode.owner_document_id == peer_id)
            )
            other_user_node = await db.scalar(
                select(GraphNode).where(GraphNode.owner_document_id == other_user_id)
            )
            other_namespace_node = await db.scalar(
                select(GraphNode).where(
                    GraphNode.owner_document_id == other_namespace_id
                )
            )
            assert peer_node is not None
            assert other_user_node is not None
            assert other_namespace_node is not None

            deleted = await service.delete_document(
                db,
                user_id=user_a_id,
                document_id=target_id,
            )
            assert deleted == {"document_id": target_id, "deleted": True}
            assert (
                await service.get_document(
                    db,
                    user_id=user_a_id,
                    document_id=target_id,
                )
                is None
            )
            assert await visible(user_a_id, namespace_a) == {peer_id}
            assert (
                await db.scalar(select(Job).where(Job.job_id == target_job.job_id))
                is None
            )
            assert (
                await db.scalar(
                    select(JobResult).where(JobResult.id == results[0].id)
                )
                is None
            )
            assert not file_storage.verify_exists(
                upload_key,
                bucket=file_storage.uploads_bucket,
            )["exists"]
            assert not file_storage.verify_exists(
                result_zip_key,
                bucket=result_storage.results_bucket,
            )["exists"]
            assert not result_storage.verify_raw_exists(
                job_id=target_job.job_id,
                relative_path="source.pdf",
            )
            retrieval_after = await run_retrieval_query(
                db=db,
                user_id=user_a_id,
                namespace=namespace_a,
                query=retrieval_marker,
                top_k=10,
                exclude_document_ids=[],
                exclude_sections=[],
                channels=["content"],
                use_agentic=False,
            )
            retrieval_after_ids = {
                item["source"]["document_id"]
                for item in retrieval_after["results"]
            }
            assert target_id not in retrieval_after_ids
        finally:
            await db.rollback()
            await db.execute(
                delete(GraphEdge).where(GraphEdge.owner_document_id.in_(document_ids))
            )
            await db.execute(
                delete(GraphNode).where(GraphNode.owner_document_id.in_(document_ids))
            )
            await db.execute(
                delete(Document).where(Document.document_id.in_(document_ids))
            )
            await db.execute(delete(DocumentChunk).where(DocumentChunk.id.in_(chunk_ids)))
            await db.execute(delete(JobResult).where(JobResult.id.in_(result_ids)))
            await db.execute(delete(Job).where(Job.job_id.in_(job_ids)))
            await db.execute(delete(User).where(User.id.in_([user_a_id, user_b_id])))
            await db.commit()


async def main() -> None:
    await _rollback_probe()
    await _lifecycle_probe()
    print(
        "D2 synthetic application lifecycle probe passed: cross-scope isolation, "
        "archive exclusion, archived graph residue cleanup, hard-delete storage "
        "cleanup, and retrieval non-visibility."
    )


asyncio.run(main())
'@
    Write-Output "D2 stage: lifecycle probe starting."
    $lifecyclePreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        $lifecycleOutput = ($lifecycleProbe | & docker exec -i knowhere_d2_api env PYTHONWARNINGS=ignore python - 2>&1 | Out-String).Trim()
        $lifecycleExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $lifecyclePreference
    }
    if ($lifecycleExitCode -ne 0 -or $lifecycleOutput -notlike "*D2 synthetic application lifecycle probe passed*") {
        Write-Output "D2 lifecycle probe diagnostic (exit=$lifecycleExitCode):"
        Write-Output $lifecycleOutput
    }
    Assert-D2 ($lifecycleExitCode -eq 0) "D2 synthetic application lifecycle probe failed: $lifecycleOutput"
    Assert-D2 ($lifecycleOutput -like "*D2 synthetic application lifecycle probe passed*") `
        "D2 synthetic application lifecycle probe did not report success: $lifecycleOutput"
    Write-Output "D2 synthetic application lifecycle probe completed."

    foreach ($containerName in @("knowhere_d2_localstack", "knowhere_d2_api", "knowhere_d2_worker")) {
        & docker exec $containerName sh -c "curl -fsS --connect-timeout 2 --max-time 4 https://example.com >/dev/null 2>&1"
        $egressExitCode = $LASTEXITCODE
        Assert-D2 ($egressExitCode -ne 0) "$containerName external HTTPS unexpectedly succeeded"
    }
    Write-Output "D2 external HTTPS negative checks completed."

    $restoreDatabase = "d2_restore_smoke"
    try {
        $null = Invoke-D2DockerText @("exec", "knowhere_d2_postgres", "sh", "-c", "dropdb -U root --if-exists d2_restore_smoke 2>/dev/null")
        $null = Invoke-D2DockerText @(
            "exec", "knowhere_d2_postgres", "psql", "-v", "ON_ERROR_STOP=1", "-U", "root", "-d", "Knowhere",
            "-c", "CREATE TABLE IF NOT EXISTS d2_backup_smoke (id integer PRIMARY KEY, payload text NOT NULL); TRUNCATE d2_backup_smoke; INSERT INTO d2_backup_smoke VALUES (1, 'synthetic-d2-sentinel');"
        )
        $null = Invoke-D2DockerText @("exec", "knowhere_d2_postgres", "pg_dump", "-U", "root", "--format=custom", "--file=/tmp/d2-backup.dump", "Knowhere")
        $null = Invoke-D2DockerText @("exec", "knowhere_d2_postgres", "createdb", "-U", "root", $restoreDatabase)
        $null = Invoke-D2DockerText @("exec", "knowhere_d2_postgres", "pg_restore", "-U", "root", "--exit-on-error", "--dbname=$restoreDatabase", "/tmp/d2-backup.dump")
        $restored = Invoke-D2DockerText @("exec", "knowhere_d2_postgres", "psql", "-At", "-U", "root", "-d", $restoreDatabase, "-c", "SELECT payload FROM d2_backup_smoke WHERE id=1")
        Assert-D2 ($restored -eq "synthetic-d2-sentinel") "backup/restore sentinel did not round-trip"

        $null = Invoke-D2DockerText @(
            "exec", "knowhere_d2_postgres", "psql", "-q", "-v", "ON_ERROR_STOP=1", "-U", "root", "-d", "Knowhere",
            "-c", "CREATE TABLE IF NOT EXISTS d2_rollback_smoke (id integer PRIMARY KEY, payload text NOT NULL); TRUNCATE d2_rollback_smoke;"
        )
        $rollbackResult = Invoke-D2DockerText @(
            "exec", "knowhere_d2_postgres", "psql", "-qAt", "-v", "ON_ERROR_STOP=1", "-U", "root", "-d", "Knowhere",
            "-c", "BEGIN; INSERT INTO d2_rollback_smoke VALUES (1, 'rolled-back'); ROLLBACK; SELECT count(*) FROM d2_rollback_smoke;"
        )
        Assert-D2 ($rollbackResult -eq "0") "transaction rollback sentinel left committed data: $rollbackResult"
        Write-Output "D2 backup/restore and rollback checks completed."
    }
    finally {
        $null = Invoke-D2DockerText @("exec", "knowhere_d2_postgres", "psql", "-q", "-v", "ON_ERROR_STOP=1", "-U", "root", "-d", "Knowhere", "-c", "SET client_min_messages=warning; DROP TABLE IF EXISTS d2_backup_smoke; DROP TABLE IF EXISTS d2_rollback_smoke")
        $null = Invoke-D2DockerText @("exec", "knowhere_d2_postgres", "sh", "-c", "dropdb -U root --if-exists d2_restore_smoke 2>/dev/null")
        $null = Invoke-D2DockerText @("exec", "knowhere_d2_postgres", "rm", "-f", "/tmp/d2-backup.dump")
    }

    Write-Output "D2 hardened harness verification passed: dependency/application health, cross-scope lifecycle isolation, runtime controls, file-backed secret, telemetry disabled, no external HTTPS, backup/restore, and rollback smoke."
}
catch {
    $failureMessage = ($_.Exception.Message -replace "\s+", " ").Trim()
    Write-Error ("D2 dependency harness verification failed: " + $failureMessage)
    exit 1
}
