from __future__ import annotations

import pytest

import app.services.common.device_checks as device_checks


def test_check_internet_skips_network_when_no_probe_url_is_explicit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []

    def fail_if_called(url: str, *, timeout: float) -> object:
        calls.append(url)
        raise AssertionError("implicit connectivity probe should be skipped")

    monkeypatch.setattr(device_checks.requests, "get", fail_if_called)

    assert device_checks.check_internet() is False

    assert calls == []


def test_check_internet_allows_an_explicit_probe_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    requested: dict[str, object] = {}

    class _Response:
        def raise_for_status(self) -> None:
            return None

    def fake_get(url: str, *, timeout: float) -> _Response:
        requested.update(url=url, timeout=timeout)
        return _Response()

    monkeypatch.setattr(device_checks.requests, "get", fake_get)

    assert device_checks.check_internet("https://probe.example") is True
    assert requested["url"] == "https://probe.example"
