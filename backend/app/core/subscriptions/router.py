"""HTTP API for platform SaaS subscriptions (Culqi)."""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth.dependencies import (
    ClinicContext,
    get_clinic_context_for_billing,
    require_platform_operator,
)
from app.core.auth.models import User
from app.core.auth.permissions import has_permission
from app.core.schemas import ApiResponse
from app.core.subscriptions.culqi import CulqiError
from app.core.subscriptions.service import (
    SubscriptionService,
    get_clinic_for_update,
    subscription_access_state,
)
from app.database import get_db

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


class FeePreviewRequest(BaseModel):
    amount_cents: int = Field(ge=100, le=10_000_000)
    currency: str = Field(default="PEN", pattern="^[A-Z]{3}$")


class FeePreviewResponse(BaseModel):
    amount_cents: int
    currency: str
    culqi_fee_cents: int
    sunat_igv_cents: int
    net_cents: int
    fee_percent: float
    fee_fixed_cents: int
    igv_percent: float


class SetSubscriptionPriceRequest(BaseModel):
    amount_cents: int = Field(ge=100, le=10_000_000)
    start_trial: bool = True


class PaySubscriptionRequest(BaseModel):
    source_id: str = Field(min_length=10, max_length=64)
    email: EmailStr
    method: str = Field(default="card", pattern="^(card|yape)$")


class ClinicSubscriptionStatus(BaseModel):
    clinic_id: UUID
    clinic_name: str
    price_cents: int | None
    currency: str
    period_ends_at: str | None
    access_state: str
    grace_days: int
    period_days: int
    culqi_public_key: str
    fee_preview: FeePreviewResponse | None = None


@router.get("/config", response_model=ApiResponse[dict])
async def subscription_public_config() -> ApiResponse[dict]:
    """Public Culqi key + fee defaults (no secret)."""
    return ApiResponse(
        data={
            "culqi_public_key": settings.CULQI_PUBLIC_KEY,
            "currency": "PEN",
            "fee_percent": settings.CULQI_FEE_PERCENT,
            "fee_fixed_cents": settings.CULQI_FEE_FIXED_CENTS,
            "igv_percent": settings.CULQI_IGV_PERCENT,
            "period_days": settings.SUBSCRIPTION_PERIOD_DAYS,
            "grace_days": settings.SUBSCRIPTION_GRACE_DAYS,
            "configured": bool(settings.CULQI_PUBLIC_KEY and settings.CULQI_SECRET_KEY),
        }
    )


@router.post("/preview-fees", response_model=ApiResponse[FeePreviewResponse])
async def preview_fees(
    body: FeePreviewRequest,
    _: Annotated[User, Depends(require_platform_operator)],
) -> ApiResponse[FeePreviewResponse]:
    fees = SubscriptionService.preview_price(body.amount_cents, body.currency)
    return ApiResponse(data=FeePreviewResponse(**fees.as_dict()))


@router.get("/dashboard", response_model=ApiResponse[dict])
async def subscriptions_dashboard(
    _: Annotated[User, Depends(require_platform_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[dict]:
    data = await SubscriptionService.dashboard(db)
    return ApiResponse(data=data)


@router.put(
    "/clinics/{clinic_id}/price",
    response_model=ApiResponse[dict],
)
async def set_clinic_subscription_price(
    clinic_id: UUID,
    body: SetSubscriptionPriceRequest,
    _: Annotated[User, Depends(require_platform_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[dict]:
    clinic = await get_clinic_for_update(db, clinic_id)
    if clinic is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clinic not found")
    try:
        await SubscriptionService.set_price(
            db, clinic, body.amount_cents, start_trial=body.start_trial
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc
    await db.commit()
    await db.refresh(clinic)
    fees = SubscriptionService.preview_price(
        clinic.subscription_price_cents or 0, clinic.currency
    )
    return ApiResponse(
        data={
            "clinic_id": clinic.id,
            "subscription_price_cents": clinic.subscription_price_cents,
            "subscription_period_ends_at": (
                clinic.subscription_period_ends_at.isoformat()
                if clinic.subscription_period_ends_at
                else None
            ),
            "access_state": subscription_access_state(clinic),
            "fee_preview": fees.as_dict(),
        }
    )


@router.get("/me", response_model=ApiResponse[ClinicSubscriptionStatus])
async def my_clinic_subscription(
    ctx: Annotated[ClinicContext, Depends(get_clinic_context_for_billing)],
) -> ApiResponse[ClinicSubscriptionStatus]:
    clinic = ctx.clinic
    preview = None
    if clinic.subscription_price_cents:
        preview = FeePreviewResponse(
            **SubscriptionService.preview_price(
                clinic.subscription_price_cents, clinic.currency
            ).as_dict()
        )
    return ApiResponse(
        data=ClinicSubscriptionStatus(
            clinic_id=clinic.id,
            clinic_name=clinic.name,
            price_cents=clinic.subscription_price_cents,
            currency=clinic.currency,
            period_ends_at=(
                clinic.subscription_period_ends_at.isoformat()
                if clinic.subscription_period_ends_at
                else None
            ),
            access_state=subscription_access_state(clinic),
            grace_days=settings.SUBSCRIPTION_GRACE_DAYS,
            period_days=settings.SUBSCRIPTION_PERIOD_DAYS,
            culqi_public_key=settings.CULQI_PUBLIC_KEY,
            fee_preview=preview,
        )
    )


@router.post("/me/pay", response_model=ApiResponse[dict], status_code=201)
async def pay_my_subscription(
    body: PaySubscriptionRequest,
    ctx: Annotated[ClinicContext, Depends(get_clinic_context_for_billing)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[dict]:
    """Clinic admin pays the agreed subscription via Culqi token/Yape."""
    if not has_permission(ctx.role, "admin.users.write"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Permission denied: admin.users.write",
        )
    clinic = await get_clinic_for_update(db, ctx.clinic_id)
    if clinic is None:
        raise HTTPException(status_code=404, detail="Clinic not found")

    try:
        payment = await SubscriptionService.pay_with_culqi(
            db,
            clinic=clinic,
            source_id=body.source_id,
            email=str(body.email),
            method=body.method,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except CulqiError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(exc),
        ) from exc

    await db.commit()
    return ApiResponse(
        data={
            "payment_id": payment.id,
            "culqi_charge_id": payment.culqi_charge_id,
            "amount_cents": payment.amount_cents,
            "net_cents": payment.net_cents,
            "period_end": payment.period_end.isoformat() if payment.period_end else None,
            "status": payment.status,
        }
    )


@router.post("/enforce-overdue", response_model=ApiResponse[dict])
async def enforce_overdue(
    _: Annotated[User, Depends(require_platform_operator)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ApiResponse[dict]:
    """Manually pause clinics past the grace period."""
    count = await SubscriptionService.enforce_overdue_pause(db)
    await db.commit()
    return ApiResponse(data={"paused": count})
