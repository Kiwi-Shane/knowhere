from __future__ import annotations

import os
from pathlib import Path

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("TMP_PATH", "/tmp/knowhere-test")
os.environ.setdefault("S3_BUCKET_NAME", "test-uploads")
os.environ.setdefault("S3_ACCESS_KEY_ID", "test")
os.environ.setdefault("S3_SECRET_ACCESS_KEY", "test")
os.environ.setdefault("S3_TEMP_PATH", "/tmp")

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LOCAL_MINERU_E2E") != "1",
    reason="set RUN_LOCAL_MINERU_E2E=1 to run the real local MinerU seam",
)


def test_real_local_mineru_runs_through_standard_pdf_provider_seam(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app.services.document_parser.formats.pdf import parser as pdf_parser
    from app.services.document_parser.providers.mineru import provider

    project_value = os.getenv("MINERU_LOCAL_PROJECT_PATH", "").strip()
    uv_value = os.getenv("MINERU_LOCAL_UV_EXECUTABLE", "").strip()
    assert project_value, "MINERU_LOCAL_PROJECT_PATH is required for local MinerU E2E"
    assert uv_value, "MINERU_LOCAL_UV_EXECUTABLE is required for local MinerU E2E"

    project = Path(project_value).expanduser().resolve()
    uv_executable = Path(uv_value).expanduser().resolve()
    source = project / "tests" / "unittest" / "pdfs" / "test.pdf"
    assert project.is_dir()
    assert uv_executable.is_file()
    assert source.is_file()

    monkeypatch.setattr(provider.settings, "MINERU_PROVIDER", "local")
    monkeypatch.setattr(provider.settings, "MINERU_LOCAL_PROJECT_PATH", str(project))
    monkeypatch.setattr(
        provider.settings,
        "MINERU_LOCAL_UV_EXECUTABLE",
        str(uv_executable),
    )
    monkeypatch.setattr(provider.settings, "MINERU_LOCAL_BACKEND", "pipeline")
    monkeypatch.setattr(provider.settings, "MINERU_LOCAL_METHOD", "auto")
    monkeypatch.setattr(provider.settings, "MINERU_LOCAL_LANGUAGE", "en")
    monkeypatch.setattr(provider.settings, "MINERU_LOCAL_OFFLINE", True)
    monkeypatch.setattr(provider.settings, "MINERU_LOCAL_MAX_CONCURRENT_JOBS", 1)
    monkeypatch.setattr(
        provider.settings,
        "MINERU_LOCAL_ADMISSION_TIMEOUT_SECONDS",
        30,
    )

    cloud_calls: list[str] = []
    monkeypatch.setattr(
        provider,
        "parse_via_full",
        lambda *_args, **_kwargs: cloud_calls.append("cloud"),
    )
    downstream_calls: list[Path] = []

    def observe_markdown(
        _output_dir: str,
        *,
        file_path: str,
        **_kwargs: object,
    ) -> str:
        markdown_path = Path(file_path)
        assert markdown_path.is_file()
        downstream_calls.append(markdown_path)
        return "downstream-ok"

    monkeypatch.setattr(pdf_parser, "parse_md", observe_markdown)
    output = tmp_path / "provider-output"

    result = pdf_parser.parse_pdfs(
        str(source),
        source.name,
        str(output),
        {},
    )

    assert result == "downstream-ok"
    assert downstream_calls == [output / "full.md"]
    assert (output / "full.md").is_file()
    assert (output / "logs" / "mineru.log").is_file()
    assert cloud_calls == []
    assert not any(path.name.startswith(".mineru-local-") for path in output.iterdir())
