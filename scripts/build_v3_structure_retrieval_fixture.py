"""Build the committed V3 bounded-synthetic retrieval qualification fixture."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from shared.services.retrieval.qualification import (
    run_v3_structure_synthetic_qualification,
)


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (
    ROOT
    / "apps"
    / "worker"
    / "tests"
    / "qualification"
    / "fixtures"
    / "v3_full_layout_v1_2"
    / "fixture-set.json"
)
OUTPUT = (
    ROOT
    / "examples"
    / "qualification"
    / "v3-structure-downstream"
    / "qualification-report.json"
)
FIXTURE_SHA256 = (
    "83b71c5922069208c1c7626dd9ab68dbabc4ba9f63bde253cfb2077e9d3d9cd7"
)


def main() -> None:
    repository_sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()
    fixture = json.loads(SOURCE.read_text(encoding="utf-8"))
    report = run_v3_structure_synthetic_qualification(
        fixture_set=fixture,
        expected_fixture_sha256=FIXTURE_SHA256,
        repository_sha=repository_sha,
    )
    if report["technical_completion"] != "qualified":
        raise RuntimeError("V3 synthetic retrieval qualification failed")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{OUTPUT}: {repository_sha}")


if __name__ == "__main__":
    main()
