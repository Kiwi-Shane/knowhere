# D2 local MinerU worker integration design

## Status

Approved for implementation under the standing operator authorization on
2026-07-20. This design is limited to the integrated local-worker
qualification gate (BL-093). It does not start a private pilot, create a real
provider session, or enable upstream synchronization.

## Context

The standalone MinerU measurement and the local provider seam have passed, but
the D2 application harness still runs `MINERU_PROVIDER=cloud`. The existing
worker image also has no Linux MinerU runtime or model bundle, so changing one
environment variable would not constitute an integrated local qualification.
The normal D2 worker must continue to preserve its cloud-default behavior.

## Goals

- Build a repeatable, pinned Linux worker image containing the Knowhere worker
  and the selected MinerU source revision.
- Run MinerU in the worker's local child-process seam with no cloud fallback.
- Keep the standard D2 compose contract unchanged for cloud-default synthetic
  tests.
- Add an opt-in local overlay that replaces the D2 worker service, so a D2
  local run cannot accidentally leave a second cloud worker consuming the same
  queues.
- Require a read-only model-root bind mount and startup preflight; missing
  source, runtime, adapter, model root, disk, or memory must fail closed.
- Preserve existing D2 network and container restrictions and provide static
  and runtime verification hooks without storing private source or model files
  in Git.

## Non-goals

- No default-provider change, application percentage routing, cloud fallback,
  DOCX local routing, or concurrency increase.
- No real private-pilot corpus execution in this implementation slice.
- No provider API credentials, destination/retention configuration, external
  review job, or RA disposition.
- No host-level no-egress attestation; that remains an operator/system gate.
- No upstream sync, reset, rebase, force-push, or changes to existing dirty
  worktrees.

## Considered approaches

1. **Mutate the existing D2 worker environment to local.** Rejected: it makes
   the characterized D2 harness depend on a host-specific source checkout and
   model cache, and it permits cloud/local worker overlap when both harnesses
   are running.
2. **Add a MinerU HTTP sidecar.** Rejected: it creates a new network provider
   boundary and weakens the local-only/no-egress interpretation.
3. **Use an opt-in local worker image and compose overlay.** Selected: the
   worker is the same integrated task consumer, but its source and runtime are
   pinned at image build time and its model root is explicitly mounted at
   runtime. The normal D2 compose file remains cloud-default; the overlay is a
   separate deployment choice.

## Design

### Image and source boundary

Add `deploy/docker/Dockerfile.worker.local-mineru`. It reuses the current
Knowhere worker build inputs and adds a separate MinerU build stage from a
named Docker build context. The build installs only the pinned `pipeline`
extra with `uv sync --locked --no-dev`, copies the selected MinerU project into
`/opt/mineru`, and records the required `MINERU_SOURCE_REVISION` as an image
label and content-free runtime metadata. The compose overlay requires both the
named source context and its expected revision; a host-side validation command
must verify that the context is a Git checkout at that revision before build.

The image contains source and Python dependencies but not customer documents
or private pilot evidence. Models are supplied by a host/operator-managed
read-only bind mount. The image config points MinerU to a fixed in-container
model path and selects `MINERU_MODEL_SOURCE=local`, so an offline parse cannot
silently download models.

### Compose overlay

Add `deploy/local-dev/docker-compose.d2-local-mineru.yml`. It is applied after
`docker-compose.dev.yml` and `docker-compose.d2.yml`, and replaces only the
`worker` service build/image/runtime configuration. The resulting local D2
project still has the five existing services, the same internal network, no
published ports, read-only roots, dropped capabilities, no-new-privileges,
resource limits, and file-backed database secret.

The overlay sets:

- `MINERU_PROVIDER=local`;
- startup preflight enabled;
- local project `/opt/mineru` and uv `/usr/local/bin/uv`;
- local Python `/opt/mineru/.venv/bin/python`;
- local model root `/mnt/models/mineru`;
- local offline/model-source environment;
- worker and local MinerU concurrency of one;
- the same worker heartbeat path and D2 queue set.

The local overlay is mutually exclusive with the cloud D2 worker for a given
project name. Its same service/container identity is intentional: applying
the overlay replaces the cloud worker instead of starting a second consumer
on the same queues. A runbook command will make the compose file ordering and
required `MINERU_SOURCE_CONTEXT`, `MINERU_SOURCE_REVISION`, and
`MINERU_MODEL_ROOT` inputs explicit.

### Model configuration and fail-closed startup

Add a checked-in, path-stable MinerU configuration template for the image. It
contains no credentials and maps the local pipeline model root to
`/mnt/models/mineru`. Add an optional `MINERU_LOCAL_MODEL_ROOT` setting to the
Knowhere local runtime preflight. When set (as it is in the local overlay),
preflight requires the directory to exist and records only a boolean `models`
check and the stable `models_missing` error code. It must not enumerate model
files, log paths, or load models.

The worker's existing local preflight and no-fallback provider boundary remain
the execution control. The overlay's runtime environment must make the local
provider selection explicit; the standard cloud D2 contract must continue to
assert `MINERU_PROVIDER=cloud`.

### Verification

Extend the existing D2 contract coverage with a local-overlay contract that
checks the service replacement, named build context, pinned revision input,
local provider settings, read-only model mount, and unchanged restrictions.
Add preflight contract cases for a missing model root and a ready model root.
Add a local-D2 verification entry point or explicit verifier mode that checks
the effective Compose configuration, worker environment, model mount mode,
network restrictions, worker health, and the existing synthetic D2 lifecycle
probes. It must not call `docker compose down` or destroy evidence.

The implementation gate passes only after:

1. static contracts, Ruff, targeted worker tests, and the existing D2 contract
   suite pass;
2. the local overlay renders successfully with supplied source/model inputs;
3. the image starts with local preflight ready and no external HTTPS probe
   succeeds from API or Worker;
4. one integrated synthetic retrieval flow exercises the local provider seam,
   and output/locator/stale/cross-case controls remain attributable to the
   local worker; and
5. the revision, image metadata, preflight status, test results, and any
   warnings are recorded in the qualification evidence before BL-093 can be
   closed.

The public 9-run canary and standalone measurement remain supporting evidence;
they do not substitute for this container-integrated gate. Offline remains a
requested mode until a separate host-level no-egress proof is recorded.

## Rollback

Do not alter the standard D2 compose file or cloud default. Stop the local D2
project and restart the characterized cloud D2 project without the local
overlay. A local parsing failure remains a local failure and is not replayed
through cloud automatically.

## Traceability

- RA backlog: BL-093, followed by BL-094 only after this gate passes.
- Knowhere source baseline: `188027c4` (`docs: record D2 hard-delete verifier
  evidence`).
- Supporting measurements: the user-provided 2026-07-20 private-shadow summary
  and its local evidence paths; raw evidence remains outside Git.
