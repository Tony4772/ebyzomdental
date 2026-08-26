"""Minimal Culqi REST client (charges)."""

from __future__ import annotations

import base64
import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class CulqiError(Exception):
    """Raised when Culqi rejects or fails a request."""

    def __init__(self, message: str, status_code: int | None = None, payload: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


def _auth_header(secret_key: str) -> str:
    token = base64.b64encode(f"{secret_key}:".encode()).decode()
    return f"Basic {token}"


async def create_charge(
    *,
    amount_cents: int,
    currency_code: str,
    email: str,
    source_id: str,
    description: str,
    metadata: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Create a Culqi charge with the platform secret key."""
    secret = settings.CULQI_SECRET_KEY
    if not secret:
        raise CulqiError("CULQI_SECRET_KEY is not configured")

    body: dict[str, Any] = {
        "amount": amount_cents,
        "currency_code": currency_code,
        "email": email,
        "source_id": source_id,
        "description": description[:80],
        "capture": True,
    }
    if metadata:
        body["metadata"] = metadata

    url = f"{settings.CULQI_API_BASE.rstrip('/')}/charges"
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            url,
            json=body,
            headers={
                "Authorization": _auth_header(secret),
                "Content-Type": "application/json",
            },
        )

    try:
        data = response.json()
    except Exception:
        data = {"raw": response.text}

    if response.status_code >= 400:
        msg = (
            data.get("user_message")
            or data.get("merchant_message")
            or data.get("message")
            or "Culqi charge failed"
        )
        logger.warning("culqi_charge_failed status=%s body=%s", response.status_code, data)
        raise CulqiError(str(msg), status_code=response.status_code, payload=data)

    return data
