# Local MinerU production canary

Use this runbook only for a dedicated local MinerU worker deployment. Cloud
remains the default provider, and the local deployment must use its own queue.
Do not change `MINERU_PROVIDER` in place on a busy worker.

## 1. Qualify the integrated D2 local Worker

This gate is the container-integrated qualification required before the
private pilot. It uses the opt-in overlay and replaces the cloud-default D2
Worker in the same compose project; stop or otherwise quiesce the cloud Worker
before starting it. Do not run cloud and local Workers against the same
ingestion queues.

Use a clean MinerU checkout whose revision is pinned for the image, and a
prepared pipeline model root. Keep both outside the Knowhere Git worktree:

```powershell
$env:MINERU_SOURCE_CONTEXT = 'C:\path\to\pinned\MinerU'
$env:MINERU_SOURCE_REVISION = (& git -C $env:MINERU_SOURCE_CONTEXT rev-parse HEAD).Trim()
$env:KNOWHERE_SOURCE_REVISION = (& git rev-parse HEAD).Trim()
$env:MINERU_MODEL_ROOT = 'C:\path\to\PDF-Extract-Kit-1.0\snapshot'

if ((git status --short).Trim()) {
    throw 'The Knowhere checkout must be clean for a traceable image build'
}
if ((git -C $env:MINERU_SOURCE_CONTEXT status --short).Trim()) {
    throw 'MINERU_SOURCE_CONTEXT must be clean'
}
if (-not (Test-Path -LiteralPath $env:MINERU_MODEL_ROOT -PathType Container)) {
    throw 'MINERU_MODEL_ROOT must be an existing pipeline model directory'
}
```

From the Knowhere repository root, render, build, start, and verify the
overlay:

```powershell
$compose = @(
  'compose', '-p', 'knowhere-d2-hardened',
  '-f', 'deploy/local-dev/docker-compose.dev.yml',
  '-f', 'deploy/local-dev/docker-compose.d2.yml',
  '-f', 'deploy/local-dev/docker-compose.d2-local-mineru.yml'
)
docker @compose config --quiet
docker @compose build worker
docker @compose up -d
.\deploy\local-dev\verify-d2.ps1 -LocalMineru
```

The verifier must report local startup preflight ready, healthy API/Worker,
five services on the internal network, no published ports, read-only model
mount, synthetic scope/lifecycle/deletion/rollback/backup-restore success,
and failed external HTTPS probes from API and Worker. Preserve the image
source-revision label, preflight JSON, verifier output, and sanitized logs as
local qualification evidence. Do not add them to Git.

This gate does not prove host-level no-egress, start a real provider session,
submit an external review job, or close RA accept/reject/defer. Keep
`offline_requested` separate from `offline_verified`.

## 2. Confirm content-free readiness

Set the local provider, MinerU project, uv executable, and optional MinerU
Python executable in the current process. Then run:

```powershell
python -m uv run python apps/worker/scripts/check_local_mineru_runtime.py
```

Proceed only when the JSON response has `ready: true` and every check is true.
The preflight must remain content-free and must not load models or access the
network.

## 3. Run the repeat-three public canary

From the Knowhere repository root:

```powershell
python -m uv run python apps/worker/scripts/validate_codex_export_corpus.py `
  --corpus apps/worker/tests/fixtures/codex_export/local-mineru-canary-corpus.json `
  --output .codex-review/production-canary `
  --mineru-project C:\path\to\MinerU `
  --repeat 3 --backend pipeline --method auto --dpi 144 --offline --force
```

Keep application offline mode enabled, use the CPU `pipeline` backend, and keep
independent-job and shard concurrency at 1. Accept the canary only when all nine
runs complete, expectation mismatches and reproducibility failures are both
zero, no temporary output remains, and sampled peak RSS stays below the
deployment memory limit.

This application offline flag is not external network isolation. Firewall
isolation verification remains a separate operator-run backlog item (BL-001).

## 4. Start the dedicated worker

Start a new local-only deployment and queue with worker concurrency 1. Configure
`MINERU_PROVIDER=local`, startup preflight enabled, local job capacity 1, and
the validated project and executable paths. Route only explicitly approved,
non-confidential PDFs between 1 and 20 pages. Do not route DOCX files.

Never increase worker, local-job, or shard concurrency during the canary. Never
automatically retry a local failure through the cloud provider.

## 5. Observe for 24 hours

Observe the dedicated queue and the allowlisted `mineru.provider` events for a
full 24 hours. Require zero unexpected failures and p95 extraction duration
below `MINERU_LOCAL_TIMEOUT_SECONDS`. Also watch admission timeouts, worker
restarts, memory, disk, queue age, and leftover `.mineru-local-*` directories.

Do not advance to a customer-wide rollout. Increase approved volume only by a
manual decision after reviewing the canary evidence, and keep document type,
page range, confidentiality, and concurrency gates unchanged.

## 6. Roll back safely

Stop routing new work to the local queue, drain or explicitly fail its remaining
jobs, and route new jobs to a separately configured cloud worker. Do not mutate
`MINERU_PROVIDER` on a busy worker and do not silently replay failed local jobs
through cloud processing. Preserve content-free metrics and sanitized logs for
the incident review, then remove the generated canary output.
