"""Unit tests for media upload validation (size + magic bytes)."""

from __future__ import annotations

from io import BytesIO
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException, UploadFile

from app.modules.media.validation import (
    read_upload_bounded,
    resolve_mime_type,
    sniff_mime_type,
    validate_file_size,
)


def _minimal_pdf() -> bytes:
    return b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n"


def _minimal_jpeg() -> bytes:
    # SOI + APP0 stub is enough for sniffing
    return b"\xff\xd8\xff\xe0" + b"\x00" * 16


def _minimal_png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"\x00" * 8


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (_minimal_pdf(), "application/pdf"),
        (_minimal_jpeg(), "image/jpeg"),
        (_minimal_png(), "image/png"),
        (b"GIF89a" + b"\x00" * 4, "image/gif"),
        (b"RIFF" + b"\x00" * 4 + b"WEBP" + b"\x00" * 4, "image/webp"),
        (b"\x00\x00\x00\x18ftypheic" + b"\x00" * 8, "image/heic"),
        (b"\x00\x00\x00\x18ftypmif1" + b"\x00" * 8, "image/heif"),
        (b"MZ\x90\x00this-is-not-an-image", None),
        (b"", None),
    ],
)
def test_sniff_mime_type(data: bytes, expected: str | None) -> None:
    assert sniff_mime_type(data) == expected


def test_resolve_mime_accepts_matching_declared() -> None:
    assert resolve_mime_type(_minimal_pdf(), declared="application/pdf") == "application/pdf"


def test_resolve_mime_rejects_spoofed_content_type() -> None:
    with pytest.raises(HTTPException) as exc:
        resolve_mime_type(b"MZ\x90\x00executable", declared="image/jpeg")
    assert exc.value.status_code == 400
    assert "Unrecognized" in exc.value.detail or "does not match" in exc.value.detail


def test_resolve_mime_rejects_pdf_claiming_jpeg_bytes() -> None:
    with pytest.raises(HTTPException) as exc:
        resolve_mime_type(_minimal_jpeg(), declared="application/pdf")
    assert exc.value.status_code == 400
    assert "does not match" in exc.value.detail


def test_resolve_mime_uses_sniffed_when_declared_generic() -> None:
    assert resolve_mime_type(_minimal_png(), declared="application/octet-stream") == "image/png"


def test_validate_file_size_rejects_content_length(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.media.validation.settings.STORAGE_MAX_FILE_SIZE", 100)
    file = MagicMock(spec=UploadFile)
    with pytest.raises(HTTPException) as exc:
        validate_file_size(file, content_length=101)
    assert exc.value.status_code == 400
    assert "exceeds limit" in exc.value.detail


def test_reject_oversized_multipart_body(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.modules.media.validation import reject_oversized_multipart_body

    monkeypatch.setattr("app.modules.media.validation.settings.STORAGE_MAX_FILE_SIZE", 100)
    # Within max + 1 MiB overhead → allowed (multipart wrapper).
    reject_oversized_multipart_body(100 + 1024)
    with pytest.raises(HTTPException) as exc:
        reject_oversized_multipart_body(100 + 1024 * 1024 + 1)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_read_upload_bounded_aborts_oversize(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.media.validation.settings.STORAGE_MAX_FILE_SIZE", 50)
    file = MagicMock(spec=UploadFile)
    # First chunk under limit, second pushes over — must not concatenate all.
    file.read = AsyncMock(side_effect=[b"x" * 40, b"y" * 20, b""])

    with pytest.raises(HTTPException) as exc:
        await read_upload_bounded(file, chunk_size=40)
    assert exc.value.status_code == 400
    assert "exceeds limit" in exc.value.detail


@pytest.mark.asyncio
async def test_read_upload_bounded_returns_bytes(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.modules.media.validation.settings.STORAGE_MAX_FILE_SIZE", 1024)
    payload = _minimal_pdf()
    file = UploadFile(filename="doc.pdf", file=BytesIO(payload))
    assert await read_upload_bounded(file) == payload
