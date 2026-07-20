from __future__ import annotations

from pathlib import Path

from shared.services.http import pinned_outbound


def test_upload_pinned_outbound_file_keeps_host_header_and_pins_socket_ip(
    tmp_path: Path,
    monkeypatch,
) -> None:
    payload_path = tmp_path / "source.pdf"
    payload_path.write_bytes(b"pdf-bytes")
    captured: dict[str, object] = {}

    class FakeResponse:
        status = 201

        def release_conn(self) -> None:
            captured["released"] = True

        def close(self) -> None:
            captured["closed"] = True

    class FakePool:
        def __init__(self, *args, pinned_ip: str, **kwargs) -> None:
            captured["pool_args"] = args
            captured["pinned_ip"] = pinned_ip
            captured["pool_kwargs"] = kwargs

        def urlopen(self, method: str, path: str, **kwargs):
            captured["method"] = method
            captured["path"] = path
            captured["redirect"] = kwargs["redirect"]
            captured["headers"] = kwargs["headers"]
            captured["body"] = kwargs["body"].read()
            captured["timeout"] = kwargs["timeout"]
            return FakeResponse()

    monkeypatch.setattr(pinned_outbound, "PinnedHTTPSConnectionPool", FakePool)

    response = pinned_outbound.upload_pinned_outbound_file(
        url="https://objects.example/upload?signature=abc",
        pinned_ip="198.51.100.20",
        file_path=str(payload_path),
        connect_timeout_seconds=10,
        read_timeout_seconds=60,
    )

    assert response.status == 201
    assert captured["pool_args"] == ("objects.example", 443)
    assert captured["pinned_ip"] == "198.51.100.20"
    assert captured["method"] == "PUT"
    assert captured["path"] == "/upload?signature=abc"
    assert captured["redirect"] is False
    assert captured["body"] == b"pdf-bytes"
    assert captured["headers"] == {
        "Content-Length": str(len(b"pdf-bytes")),
        "Host": "objects.example",
    }
    assert captured["released"] is True
    assert captured["closed"] is True
