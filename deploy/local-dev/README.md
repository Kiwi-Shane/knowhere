# Local Development Stack

This directory contains the Docker Compose stack used for local development.

## Services

- Redis
- PostgreSQL
- LocalStack

## Start the Stack

From the repository root:

```bash
cd deploy/local-dev
./start-dev.sh
```

## Verify the Local API

After you start the API process locally, confirm the service is reachable:

```bash
curl http://localhost:5005/health
```

You can also open the local OpenAPI docs at
`http://localhost:5005/docs`.

## Stop the Stack

From the repository root:

```bash
cd deploy/local-dev
./stop-dev.sh
```

Or run the helper directly:

```bash
cd deploy/local-dev
./stop-dev.sh
```

## Service Endpoints

- PostgreSQL: `127.0.0.1:5432`
- Redis: `127.0.0.1:6379`
- LocalStack: `http://127.0.0.1:4566`

The local stack binds published ports to loopback only, keeps the bridge
network host-accessible for the host-run API/worker, and declares per-service
CPU, memory, and PID ceilings. These are local-development containment
controls; they do not establish host-level egress denial or production
deployment qualification. An internal network is reserved for an isolated D2
runtime harness, not this host-integrated development stack.

## Opt-in D2 dependency harness

The hardened D2 dependency boundary is opt-in and must be run as a separate
Compose project. It uses pinned image digests, an internal-only network, no
published ports, read-only containers with dropped capabilities, resource
ceilings inherited from the base file, and a file-backed synthetic PostgreSQL
secret. LocalStack has no Docker socket, host gateway, Lambda service, or
automatic extension/download path.

Before the first run, create or replace the local-only file
`deploy/local-dev/.d2-secrets/postgres_password`. It is ignored by Git and must
never contain a client or production secret. From the repository root:

```bash
docker compose -p knowhere-d2-hardened \
  -f deploy/local-dev/docker-compose.dev.yml \
  -f deploy/local-dev/docker-compose.d2.yml up -d
```

Validate the effective boundary with `docker compose ... config`, inspect
container health and limits, and run the repeatable verifier before
considering the slice characterized:

```powershell
powershell -ExecutionPolicy Bypass -File deploy/local-dev/verify-d2.ps1
```

The verifier performs positive health probes, checks that no host port is
published, confirms the internal Docker network and runtime limits, validates
the file-backed secret without printing it, expects external HTTPS to fail,
and runs a synthetic PostgreSQL backup/restore round-trip. The default
local-development project and its volumes are separate.

This harness is a D2 dependency/application-runtime implementation slice. It
is not an active/private pilot or reviewer qualification. The verifier now
checks API health, worker heartbeat, file-backed database-secret wiring,
telemetry-disabled startup configuration, application-container egress
denial, synthetic cross-user/namespace lifecycle isolation, archive exclusion,
archived graph-residue cleanup, transaction rollback, and a synthetic
dependency backup/restore sentinel. Full backup and restore coverage, hard
deletion, host-level firewall enforcement, source-owner/gold evidence,
provider/private-data processing, and RA acceptance remain outside this
slice.

## Notes

- The Compose file is `deploy/local-dev/docker-compose.dev.yml`.
- `stop-dev.sh` automatically uses `docker-compose` when available and falls back to `docker compose` otherwise.
- Local development infrastructure belongs here; remote deployment assets do not.
