"""Print a content-free readiness status for the configured MinerU provider."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Sequence

WORKER_ROOT = Path(__file__).resolve().parents[1]
if str(WORKER_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKER_ROOT))

from app.services.document_parser.providers.mineru.runtime_preflight import (  # noqa: E402
    check_local_mineru_runtime,
)
from shared.core.config import settings  # noqa: E402


def main(argv: Sequence[str] | None = None) -> int:
    del argv
    status = check_local_mineru_runtime(settings)
    print(json.dumps(status.to_dict(), sort_keys=True))
    return 0 if status.ready else 1


if __name__ == "__main__":
    raise SystemExit(main())
