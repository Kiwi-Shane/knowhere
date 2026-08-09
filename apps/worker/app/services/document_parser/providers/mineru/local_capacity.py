"""Process-wide admission control for independent local MinerU jobs."""

from __future__ import annotations

import threading
from contextlib import contextmanager
from typing import Iterator


class LocalMinerUCapacityError(RuntimeError):
    """Raised when local MinerU capacity cannot be acquired in time."""


class LocalMinerUCapacityGuard:
    def __init__(self, limit: int, timeout_seconds: float) -> None:
        if limit < 1 or timeout_seconds <= 0:
            raise ValueError("Local MinerU capacity values must be positive")
        self.timeout_seconds = timeout_seconds
        self._semaphore = threading.BoundedSemaphore(limit)

    @contextmanager
    def acquire(self) -> Iterator[None]:
        acquired = self._semaphore.acquire(timeout=self.timeout_seconds)
        if not acquired:
            raise LocalMinerUCapacityError("Local MinerU capacity is unavailable")
        try:
            yield
        finally:
            self._semaphore.release()


_guard_lock = threading.Lock()
_guards: dict[tuple[int, float], LocalMinerUCapacityGuard] = {}


def get_local_capacity_guard(
    limit: int,
    timeout_seconds: float,
) -> LocalMinerUCapacityGuard:
    """Return the process singleton for one bounded capacity configuration."""

    key = (limit, float(timeout_seconds))
    with _guard_lock:
        guard = _guards.get(key)
        if guard is None:
            guard = LocalMinerUCapacityGuard(limit, timeout_seconds)
            _guards[key] = guard
        return guard
