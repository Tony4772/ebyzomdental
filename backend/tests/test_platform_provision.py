"""Platform operator clinic provisioning."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.models import Clinic, ClinicMembership, User
from app.core.auth.permissions import PLATFORM_CLINICS_PROVISION
from app.core.auth.service import create_access_token, hash_password


async def _operator_headers(db: AsyncSession) -> dict[str, str]:
    user = User(
        email=f"ops-{uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TestPass1234"),
        first_name="Ops",
        last_name="Owner",
        is_platform_operator=True,
    )
    db.add(user)
    await db.flush()

    home = Clinic(
        id=uuid4(),
        name="Ops Home Clinic",
        tax_id="B11111111",
        settings={},
    )
    db.add(home)
    await db.flush()
    db.add(ClinicMembership(user_id=user.id, clinic_id=home.id, role="admin"))
    await db.commit()

    token = create_access_token(user.id, clinic_id=home.id, token_version=user.token_version)
    return {"Authorization": f"Bearer {token}"}


async def _clinic_admin_headers(db: AsyncSession) -> dict[str, str]:
    user = User(
        email=f"clinic-admin-{uuid4().hex[:8]}@example.com",
        password_hash=hash_password("TestPass1234"),
        first_name="Clinic",
        last_name="Admin",
        is_platform_operator=False,
    )
    db.add(user)
    await db.flush()

    clinic = Clinic(
        id=uuid4(),
        name="Regular Clinic",
        tax_id="B22222222",
        settings={},
    )
    db.add(clinic)
    await db.flush()
    db.add(ClinicMembership(user_id=user.id, clinic_id=clinic.id, role="admin"))
    await db.commit()

    token = create_access_token(user.id, clinic_id=clinic.id, token_version=user.token_version)
    return {"Authorization": f"Bearer {token}"}


def _provision_payload(**overrides: object) -> dict:
    body = {
        "clinic_name": "Cliente Demo SL",
        "clinic_tax_id": "B87654321",
        "timezone": "Europe/Madrid",
        "currency": "EUR",
        "admin_first_name": "Ana",
        "admin_last_name": "Cliente",
        "admin_email": f"admin-{uuid4().hex[:8]}@cliente.example",
        "admin_password": "SecurePass123",
    }
    body.update(overrides)
    return body


@pytest.mark.asyncio
async def test_setup_marks_first_admin_as_platform_operator(
    client: AsyncClient,
) -> None:
    r = await client.post(
        "/api/v1/auth/setup",
        json={
            "admin_first_name": "Owner",
            "admin_last_name": "User",
            "admin_email": "owner@example.com",
            "admin_password": "SecurePass123",
            "clinic_name": "First Clinic",
            "clinic_tax_id": "B12345678",
        },
    )
    assert r.status_code == 201, r.text
    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {r.json()['access_token']}"},
    )
    assert me.status_code == 200
    data = me.json()["data"]
    assert data["user"]["is_platform_operator"] is True
    assert PLATFORM_CLINICS_PROVISION in data["permissions"]


@pytest.mark.asyncio
async def test_clinic_admin_cannot_provision(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _clinic_admin_headers(db_session)
    r = await client.post(
        "/api/v1/auth/platform/clinics",
        json=_provision_payload(),
        headers=headers,
    )
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_clinic_admin_me_excludes_platform_permission(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _clinic_admin_headers(db_session)
    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    data = me.json()["data"]
    assert data["user"]["is_platform_operator"] is False
    assert PLATFORM_CLINICS_PROVISION not in data["permissions"]
    # Clinic admin still has wildcard-expanded clinic powers.
    assert "admin.users.write" in data["permissions"]


@pytest.mark.asyncio
async def test_operator_provisions_clinic_and_admin(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _operator_headers(db_session)
    payload = _provision_payload()
    r = await client.post(
        "/api/v1/auth/platform/clinics",
        json=payload,
        headers=headers,
    )
    assert r.status_code == 201, r.text
    body = r.json()["data"]
    assert body["clinic"]["name"] == "Cliente Demo SL"
    assert body["admin"]["email"] == payload["admin_email"]
    assert body["admin"]["is_platform_operator"] is False

    # New admin can log in and only sees their clinic.
    login = await client.post(
        "/api/v1/auth/login",
        data={"username": payload["admin_email"], "password": "SecurePass123"},
    )
    assert login.status_code == 200, login.text
    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert me.status_code == 200
    me_data = me.json()["data"]
    assert len(me_data["clinics"]) == 1
    assert me_data["clinics"][0]["name"] == "Cliente Demo SL"
    assert me_data["user"]["is_platform_operator"] is False
    assert PLATFORM_CLINICS_PROVISION not in me_data["permissions"]

    membership = await db_session.scalar(
        select(ClinicMembership).where(ClinicMembership.user_id == body["admin"]["id"])
    )
    assert membership is not None
    assert membership.role == "admin"


@pytest.mark.asyncio
async def test_operator_lists_all_clinics(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _operator_headers(db_session)
    await client.post(
        "/api/v1/auth/platform/clinics",
        json=_provision_payload(clinic_name="Alpha Dental"),
        headers=headers,
    )
    listed = await client.get("/api/v1/auth/platform/clinics", headers=headers)
    assert listed.status_code == 200, listed.text
    names = {c["name"] for c in listed.json()["data"]}
    assert "Ops Home Clinic" in names
    assert "Alpha Dental" in names


@pytest.mark.asyncio
async def test_provision_duplicate_email_conflict(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _operator_headers(db_session)
    email = f"dup-{uuid4().hex[:8]}@example.com"
    first = await client.post(
        "/api/v1/auth/platform/clinics",
        json=_provision_payload(admin_email=email),
        headers=headers,
    )
    assert first.status_code == 201, first.text
    second = await client.post(
        "/api/v1/auth/platform/clinics",
        json=_provision_payload(
            admin_email=email,
            clinic_name="Otro",
            clinic_tax_id="B00000001",
        ),
        headers=headers,
    )
    assert second.status_code == 409, second.text


@pytest.mark.asyncio
async def test_operator_updates_clinic_status(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _operator_headers(db_session)
    created = await client.post(
        "/api/v1/auth/platform/clinics",
        json=_provision_payload(clinic_name="Status Test Clinic"),
        headers=headers,
    )
    assert created.status_code == 201, created.text
    clinic_id = created.json()["data"]["clinic"]["id"]

    paused = await client.patch(
        f"/api/v1/auth/platform/clinics/{clinic_id}",
        json={"status": "paused"},
        headers=headers,
    )
    assert paused.status_code == 200, paused.text
    assert paused.json()["data"]["status"] == "paused"

    blocked = await client.patch(
        f"/api/v1/auth/platform/clinics/{clinic_id}",
        json={"status": "blocked"},
        headers=headers,
    )
    assert blocked.status_code == 200, blocked.text
    assert blocked.json()["data"]["status"] == "blocked"

    active = await client.patch(
        f"/api/v1/auth/platform/clinics/{clinic_id}",
        json={"status": "active"},
        headers=headers,
    )
    assert active.status_code == 200, active.text
    assert active.json()["data"]["status"] == "active"


@pytest.mark.asyncio
async def test_operator_edits_and_soft_deletes_clinic(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _operator_headers(db_session)
    created = await client.post(
        "/api/v1/auth/platform/clinics",
        json=_provision_payload(clinic_name="Editable Clinic"),
        headers=headers,
    )
    assert created.status_code == 201, created.text
    clinic_id = created.json()["data"]["clinic"]["id"]

    edited = await client.patch(
        f"/api/v1/auth/platform/clinics/{clinic_id}",
        json={
            "name": "Clínica Renombrada",
            "tax_id": "20123456789",
            "timezone": "America/Lima",
            "currency": "PEN",
        },
        headers=headers,
    )
    assert edited.status_code == 200, edited.text
    data = edited.json()["data"]
    assert data["name"] == "Clínica Renombrada"
    assert data["tax_id"] == "20123456789"
    assert data["status"] == "active"

    deleted = await client.patch(
        f"/api/v1/auth/platform/clinics/{clinic_id}",
        json={"status": "deleted"},
        headers=headers,
    )
    assert deleted.status_code == 200, deleted.text
    assert deleted.json()["data"]["status"] == "deleted"


@pytest.mark.asyncio
async def test_clinic_admin_cannot_update_platform_status(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    headers = await _clinic_admin_headers(db_session)
    clinic_id = (await db_session.scalar(select(Clinic.id).limit(1)))
    assert clinic_id is not None

    r = await client.patch(
        f"/api/v1/auth/platform/clinics/{clinic_id}",
        json={"status": "paused"},
        headers=headers,
    )
    assert r.status_code == 403, r.text


@pytest.mark.asyncio
async def test_paused_clinic_blocks_member_access(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    admin_headers = await _clinic_admin_headers(db_session)
    me = await client.get("/api/v1/auth/me", headers=admin_headers)
    assert me.status_code == 200
    clinic_id = me.json()["data"]["clinic"]["id"]

    operator_headers = await _operator_headers(db_session)
    pause = await client.patch(
        f"/api/v1/auth/platform/clinics/{clinic_id}",
        json={"status": "paused"},
        headers=operator_headers,
    )
    assert pause.status_code == 200, pause.text

    blocked_me = await client.get("/api/v1/auth/me", headers=admin_headers)
    assert blocked_me.status_code == 403, blocked_me.text
    assert "suspended" in blocked_me.json()["detail"].lower()
