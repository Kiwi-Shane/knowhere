[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$d2RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$d2BaseCompose = Join-Path $d2RepoRoot "deploy\local-dev\docker-compose.dev.yml"
$d2OverrideCompose = Join-Path $d2RepoRoot "deploy\local-dev\docker-compose.d2.yml"
$d2ComposeArgs = @(
    "compose"
    "-p"
    "knowhere-d2-hardened"
    "-f"
    $d2BaseCompose
    "-f"
    $d2OverrideCompose
)

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

    $serviceNames = @("redis", "postgres", "localstack")
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

    $network = (Invoke-D2DockerText @("network", "inspect", "knowhere_d2_internal") | ConvertFrom-Json)[0]
    Assert-D2 ($network.Internal -eq $true) "Docker network is not internal"
    Assert-D2 (@($network.Containers.PSObject.Properties).Count -eq 3) "D2 network does not contain three dependencies"

    $null = Invoke-D2DockerText @("exec", "knowhere_d2_redis", "redis-cli", "ping")
    $null = Invoke-D2DockerText @("exec", "knowhere_d2_postgres", "pg_isready", "-U", "root", "-d", "Knowhere")
    $null = Invoke-D2DockerText @("exec", "knowhere_d2_localstack", "curl", "-fsS", "--max-time", "5", "http://127.0.0.1:4566/_localstack/health")
    $null = Invoke-D2DockerText @("exec", "knowhere_d2_postgres", "sh", "-c", "test -s /run/secrets/postgres_password")

    & docker exec knowhere_d2_localstack sh -c "curl -fsS --connect-timeout 2 --max-time 4 https://example.com >/dev/null 2>&1"
    $egressExitCode = $LASTEXITCODE
    Assert-D2 ($egressExitCode -ne 0) "external HTTPS unexpectedly succeeded"

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
    }
    finally {
        $null = Invoke-D2DockerText @("exec", "knowhere_d2_postgres", "psql", "-q", "-v", "ON_ERROR_STOP=1", "-U", "root", "-d", "Knowhere", "-c", "SET client_min_messages=warning; DROP TABLE IF EXISTS d2_backup_smoke")
        $null = Invoke-D2DockerText @("exec", "knowhere_d2_postgres", "sh", "-c", "dropdb -U root --if-exists d2_restore_smoke 2>/dev/null")
        $null = Invoke-D2DockerText @("exec", "knowhere_d2_postgres", "rm", "-f", "/tmp/d2-backup.dump")
    }

    Write-Output "D2 dependency harness verification passed: health, isolation, runtime controls, no external HTTPS, and backup/restore smoke."
}
catch {
    Write-Error ("D2 dependency harness verification failed: " + $_.Exception.Message)
    exit 1
}
