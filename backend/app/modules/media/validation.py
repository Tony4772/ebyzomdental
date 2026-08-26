"""File validation utilities.

Validates size (bounded read) and content type via magic-byte sniffing
so the client-supplied ``Content-Type`` cannot disguise an executable
as a JPEG/PDF.
"""

from __future__ import annotations

from fastapi import HTTPException, UploadFile

from app.config import settings

# Document types enum
DOCUMENT_TYPES = ["consent", "id_scan", "insurance", "report", "referral", "other"]

# Modern image formats not in the default config allowlist but commonly
# uploaded from clinical phones / tablets. The base allowlist covers
# JPEG / PNG / PDF; we extend for HEIC (iOS), WebP and GIF so the photo
# gallery accepts them without per-clinic config changes.
_PHOTO_MIME_EXTRA = frozenset(
    {
        "image/heic",
        "image/heif",
        "image/webp",
        "image/gif",
    }
)

_HEIF_FAMILY = frozenset({"image/heic", "image/heif"})

# ISO BMFF brands that map to HEIC / HEIF (ftyp box at offset 4).
_HEIF_BRANDS = frozenset(
    {
        b"heic",
        b"heix",
        b"hevc",
        b"hevx",
        b"heim",
        b"heis",
        b"hevm",
        b"hevs",
        b"mif1",
        b"msf1",
        b"heif",
    }
)

_READ_CHUNK_SIZE = 64 * 1024


def _allowed_mime_types() -> set[str]:
    return set(settings.storage_allowed_mime_types_list) | _PHOTO_MIME_EXTRA


def _size_limit_detail(max_size: int) -> str:
    return f"File size exceeds limit of {max_size // (1024 * 1024)}MB"


def validate_file_size(file: UploadFile, content_length: int | None = None) -> None:
    """Reject early when a known byte length already exceeds the limit.

    ``content_length`` must be the **file** size (e.g. ``UploadFile.size``),
    never the raw request ``Content-Length`` of a multipart body — that
    includes form fields and boundaries and would false-reject valid
    uploads.
    """
    max_size = settings.STORAGE_MAX_FILE_SIZE
    if content_length is not None and content_length > max_size:
        raise HTTPException(status_code=400, detail=_size_limit_detail(max_size))


def reject_oversized_multipart_body(content_length: int | None) -> None:
    """Cheap pre-check on the whole multipart request body.

    Multipart overhead (boundaries + form fields) is small relative to
    clinical uploads, so a body already larger than
    ``STORAGE_MAX_FILE_SIZE + 1 MiB`` cannot contain a valid file.
    """
    if content_length is None:
        return
    max_size = settings.STORAGE_MAX_FILE_SIZE
    overhead_budget = 1024 * 1024
    if content_length > max_size + overhead_budget:
        raise HTTPException(status_code=400, detail=_size_limit_detail(max_size))


async def read_upload_bounded(
    file: UploadFile,
    *,
    content_length: int | None = None,
    chunk_size: int = _READ_CHUNK_SIZE,
) -> bytes:
    """Read an upload aborting as soon as it exceeds ``STORAGE_MAX_FILE_SIZE``.

    Prefer this over ``await file.read()`` so a multi-GB upload cannot
    exhaust process RAM before a post-hoc ``len()`` check runs.
    """
    # Prefer the multipart part size when Starlette exposes it.
    part_size = content_length if content_length is not None else file.size
    validate_file_size(file, part_size)

    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(chunk_size)
        if not chunk:
            break
        total += len(chunk)
        if total > settings.STORAGE_MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=_size_limit_detail(settings.STORAGE_MAX_FILE_SIZE),
            )
        chunks.append(chunk)
    return b"".join(chunks)


def sniff_mime_type(data: bytes) -> str | None:
    """Return the MIME type implied by magic bytes, or ``None`` if unknown."""
    if data.startswith(b"%PDF"):
        return "application/pdf"
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if data.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    if len(data) >= 12 and data[4:8] == b"ftyp":
        brand = data[8:12]
        if brand in _HEIF_BRANDS:
            # ``mif1`` / ``msf1`` are generic HEIF; the rest are HEIC brands.
            return "image/heif" if brand in {b"mif1", b"msf1", b"heif"} else "image/heic"
    return None


def _mimes_compatible(declared: str, sniffed: str) -> bool:
    if declared == sniffed:
        return True
    if declared in _HEIF_FAMILY and sniffed in _HEIF_FAMILY:
        return True
    return False


def resolve_mime_type(data: bytes, declared: str | None = None) -> str:
    """Resolve MIME from file bytes; optionally cross-check the client claim.

    The sniffed type is the source of truth for storage. A mismatched
    client ``Content-Type`` (when present and not a generic octet-stream)
    is rejected so spoofed uploads fail closed.
    """
    allowed = _allowed_mime_types()
    sniffed = sniff_mime_type(data)
    if sniffed is None:
        raise HTTPException(
            status_code=400,
            detail="Unrecognized file format (magic bytes do not match an allowed type)",
        )
    if sniffed not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{sniffed}' not allowed. Allowed: {', '.join(sorted(allowed))}",
        )

    if declared and declared not in {"application/octet-stream", ""}:
        if declared not in allowed:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"File type '{declared}' not allowed. Allowed: {', '.join(sorted(allowed))}"
                ),
            )
        if not _mimes_compatible(declared, sniffed):
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Content-Type '{declared}' does not match file content "
                    f"(detected '{sniffed}')"
                ),
            )

    return sniffed


def validate_mime_type(file: UploadFile) -> str:
    """Validate the client-declared MIME only (pre-read gate).

    Prefer :func:`resolve_mime_type` after reading bytes. Kept for
    callers that still need a cheap declared-type check.
    """
    allowed = _allowed_mime_types()
    content_type = file.content_type or "application/octet-stream"

    if content_type not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{content_type}' not allowed. Allowed: {', '.join(sorted(allowed))}",
        )

    return content_type


def validate_document_type(document_type: str) -> None:
    """Validate document type.

    Args:
        document_type: Document type to validate

    Raises:
        HTTPException: If document type invalid
    """
    if document_type not in DOCUMENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid document type. Allowed: {', '.join(DOCUMENT_TYPES)}",
        )


def get_file_extension(filename: str) -> str:
    """Extract file extension from filename.

    Args:
        filename: Original filename

    Returns:
        Extension without dot (e.g., "pdf")
    """
    if "." in filename:
        return filename.rsplit(".", 1)[1].lower()
    return ""
