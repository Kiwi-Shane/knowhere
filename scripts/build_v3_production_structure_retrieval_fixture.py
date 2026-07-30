"""Build the V3 production-profile bounded-synthetic retrieval report."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Sequence
from pathlib import Path

from shared.services.retrieval.qualification import (
    run_v3_production_structure_synthetic_qualification,
)


ROOT = Path(__file__).resolve().parents[1]
FIXTURE_ROOT = (
    ROOT
    / "apps"
    / "worker"
    / "tests"
    / "qualification"
    / "fixtures"
    / "v3_production_structure"
)
SOURCE = FIXTURE_ROOT / "fixture-set.json"
OUTPUT = (
    ROOT
    / "examples"
    / "qualification"
    / "v3-production-structure-retrieval"
    / "qualification-report.json"
)
FIXTURE_SHA256 = (
    "6d368aa27e4dc8f82ff19ec02436b6a4ed53190f324028bfe2aedb198d1de8ec"
)


def _repository_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        cwd=ROOT,
        text=True,
    ).strip()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository-sha",
        default=None,
        help="Override the exact qualification implementation revision.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=OUTPUT,
        help="Report destination.",
    )
    args = parser.parse_args(argv)
    fixture = json.loads(SOURCE.read_text(encoding="utf-8"))
    report = run_v3_production_structure_synthetic_qualification(
        fixture_set=fixture,
        fixture_root=FIXTURE_ROOT,
        expected_fixture_sha256=FIXTURE_SHA256,
        repository_sha=args.repository_sha or _repository_sha(),
    )
    if report["technical_completion"] != "qualified":
        raise RuntimeError("V3 production retrieval qualification failed")
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"{output}: {report['repository_sha']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
