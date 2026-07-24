"""Run the bounded Knowhere D4 synthetic qualification control plane."""

from __future__ import annotations

import argparse
import json
import subprocess
from collections.abc import Sequence

from shared.services.retrieval.qualification import run_d4_synthetic_qualification


def _repository_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"],
        text=True,
    ).strip()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repository-sha",
        default=None,
        help="Override the source revision used in the synthetic result context.",
    )
    parser.add_argument(
        "--fault",
        action="append",
        default=[],
        help="Inject a named control fault; repeat for multiple controls.",
    )
    args = parser.parse_args(argv)
    report = run_d4_synthetic_qualification(
        repository_sha=args.repository_sha or _repository_sha(),
        faults=args.fault,
    )
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["technical_completion"] == "qualified" else 1


if __name__ == "__main__":
    raise SystemExit(main())
