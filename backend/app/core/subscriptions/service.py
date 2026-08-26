"""Subscription lifecycle service for SaaS clinic billing."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.auth.models import Clinic
from app.core.subscriptions.culqi import CulqiError, create_charge
from app.core.subscriptions.fees import FeeBreakdown, estimate_fees
from app.core.subscriptions.models import PlatformSubscriptionPayment


def grace_deadline(clinic: Clinic) -> datetime | None:
    """Last instant the clinic may operate after period end (inclusive grace)."""
    if clinic.subscription_period_ends_at is None:
        return None
    days = settings.SUBSCRIPTION_GRACE_DAYS
    return clinic.subscription_period_ends_at + timedelta(days=days)


def subscription_access_state(clinic: Clinic, *, now: datetime | None = None) -> str:
    """Return ok | due | grace | overdue | unpriced."""
    now = now or datetime.now(UTC)
    if clinic.subscription_price_cents is None or clinic.subscription_price_cents <= 0:
        return "unpriced"
    ends = clinic.subscription_period_ends_at
    if ends is None:
        return "unpriced"
    if ends.tzinfo is None:
        ends = ends.replace(tzinfo=UTC)
    if now <= ends:
        # Due window: last day of period still "ok" until end; after end → grace
        return "ok"
    deadline = grace_deadline(clinic)
    if deadline and now <= deadline:
        return "grace"
    return "overdue"


def assert_subscription_allows_access(clinic: Clinic) -> None:
    """Raise if clinic staff must be locked out for unpaid subscription."""
    from fastapi import HTTPException, status

    state = subscription_access_state(clinic)
    if state == "overdue":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Clinic subscription is overdue",
        )


class SubscriptionService:
    @staticmethod
    def preview_price(amount_cents: int, currency: str = "PEN") -> FeeBreakdown:
        return estimate_fees(amount_cents, currency)

    @staticmethod
    async def set_price(
        db: AsyncSession,
        clinic: Clinic,
        amount_cents: int,
        *,
        start_trial: bool = False,
    ) -> Clinic:
        if amount_cents < 100:
            raise ValueError("Minimum subscription is 1.00")
        clinic.subscription_price_cents = amount_cents
        if start_trial or clinic.subscription_period_ends_at is None:
            clinic.subscription_period_ends_at = datetime.now(UTC) + timedelta(
                days=settings.SUBSCRIPTION_PERIOD_DAYS
            )
        await db.flush()
        return clinic

    @staticmethod
    async def pay_with_culqi(
        db: AsyncSession,
        *,
        clinic: Clinic,
        source_id: str,
        email: str,
        method: str,
    ) -> PlatformSubscriptionPayment:
        if not clinic.subscription_price_cents or clinic.subscription_price_cents < 100:
            raise ValueError("Clinic has no subscription price configured")

        amount = clinic.subscription_price_cents
        currency = clinic.currency or "PEN"
        fees = estimate_fees(amount, currency)

        now = datetime.now(UTC)
        base = clinic.subscription_period_ends_at
        if base is None or base < now:
            period_start = now
        else:
            period_start = base
        if period_start.tzinfo is None:
            period_start = period_start.replace(tzinfo=UTC)
        period_end = period_start + timedelta(days=settings.SUBSCRIPTION_PERIOD_DAYS)

        try:
            charge = await create_charge(
                amount_cents=amount,
                currency_code=currency,
                email=email,
                source_id=source_id,
                description=f"Suscripción EBYZOM {clinic.name}"[:80],
                metadata={
                    "clinic_id": str(clinic.id),
                    "kind": "saas_subscription",
                },
            )
        except CulqiError:
            raise

        charge_id = charge.get("id")
        outcome = charge.get("outcome") or {}
        charge_ok = charge.get("object") == "charge" and (
            outcome.get("type") in (None, "venta_exitosa")
            or charge.get("amount") == amount
        )
        # Culqi returns 201 with charge object on success
        if not charge_id:
            raise CulqiError("Culqi response missing charge id", payload=charge)

        payment = PlatformSubscriptionPayment(
            clinic_id=clinic.id,
            amount_cents=amount,
            currency=currency,
            method=method if method in ("card", "yape") else "card",
            status="paid",
            culqi_charge_id=charge_id,
            culqi_fee_cents=fees.culqi_fee_cents,
            sunat_igv_cents=fees.sunat_igv_cents,
            net_cents=fees.net_cents,
            period_start=period_start,
            period_end=period_end,
            paid_at=now,
            payer_email=email,
            raw_response=charge if isinstance(charge, dict) else None,
        )
        db.add(payment)
        clinic.subscription_period_ends_at = period_end
        # Paying restores access if it was paused for overdue subscription
        if clinic.status == "paused" and clinic.settings.get("paused_for_subscription"):
            clinic.status = "active"
            settings_copy = dict(clinic.settings or {})
            settings_copy.pop("paused_for_subscription", None)
            clinic.settings = settings_copy

        await db.flush()
        _ = charge_ok  # reserved for stricter outcome checks
        return payment

    @staticmethod
    async def dashboard(db: AsyncSession) -> dict:
        payments = (
            await db.execute(
                select(PlatformSubscriptionPayment)
                .where(PlatformSubscriptionPayment.status == "paid")
                .order_by(PlatformSubscriptionPayment.paid_at.desc())
            )
        ).scalars().all()

        clinics = (await db.execute(select(Clinic).order_by(Clinic.name))).scalars().all()

        totals = await db.execute(
            select(
                func.coalesce(func.sum(PlatformSubscriptionPayment.amount_cents), 0),
                func.coalesce(func.sum(PlatformSubscriptionPayment.culqi_fee_cents), 0),
                func.coalesce(func.sum(PlatformSubscriptionPayment.sunat_igv_cents), 0),
                func.coalesce(func.sum(PlatformSubscriptionPayment.net_cents), 0),
                func.count(PlatformSubscriptionPayment.id),
            ).where(PlatformSubscriptionPayment.status == "paid")
        )
        amount_sum, culqi_sum, sunat_sum, net_sum, count = totals.one()

        per_clinic: list[dict] = []
        for clinic in clinics:
            row = await db.execute(
                select(
                    func.coalesce(func.sum(PlatformSubscriptionPayment.amount_cents), 0),
                    func.coalesce(func.sum(PlatformSubscriptionPayment.net_cents), 0),
                    func.count(PlatformSubscriptionPayment.id),
                ).where(
                    PlatformSubscriptionPayment.clinic_id == clinic.id,
                    PlatformSubscriptionPayment.status == "paid",
                )
            )
            paid_total, net_total, pay_count = row.one()
            per_clinic.append(
                {
                    "clinic_id": clinic.id,
                    "clinic_name": clinic.name,
                    "status": clinic.status,
                    "subscription_price_cents": clinic.subscription_price_cents,
                    "subscription_period_ends_at": (
                        clinic.subscription_period_ends_at.isoformat()
                        if clinic.subscription_period_ends_at
                        else None
                    ),
                    "access_state": subscription_access_state(clinic),
                    "payments_count": int(pay_count),
                    "paid_total_cents": int(paid_total),
                    "net_total_cents": int(net_total),
                    "currency": clinic.currency,
                }
            )

        recent = [
            {
                "id": p.id,
                "clinic_id": p.clinic_id,
                "amount_cents": p.amount_cents,
                "currency": p.currency,
                "method": p.method,
                "culqi_fee_cents": p.culqi_fee_cents,
                "sunat_igv_cents": p.sunat_igv_cents,
                "net_cents": p.net_cents,
                "paid_at": p.paid_at.isoformat() if p.paid_at else None,
                "period_end": p.period_end.isoformat() if p.period_end else None,
            }
            for p in payments[:50]
        ]

        return {
            "totals": {
                "payments_count": int(count),
                "amount_cents": int(amount_sum),
                "culqi_fee_cents": int(culqi_sum),
                "sunat_igv_cents": int(sunat_sum),
                "net_cents": int(net_sum),
                "currency": "PEN",
            },
            "clinics": per_clinic,
            "recent_payments": recent,
            "fee_defaults": {
                "fee_percent": settings.CULQI_FEE_PERCENT,
                "fee_fixed_cents": settings.CULQI_FEE_FIXED_CENTS,
                "igv_percent": settings.CULQI_IGV_PERCENT,
                "period_days": settings.SUBSCRIPTION_PERIOD_DAYS,
                "grace_days": settings.SUBSCRIPTION_GRACE_DAYS,
            },
        }

    @staticmethod
    async def enforce_overdue_pause(db: AsyncSession) -> int:
        """Pause clinics past grace. Returns how many were paused."""
        clinics = (await db.execute(select(Clinic))).scalars().all()
        paused = 0
        for clinic in clinics:
            if subscription_access_state(clinic) != "overdue":
                continue
            if clinic.status in ("blocked", "deleted", "paused"):
                continue
            clinic.status = "paused"
            settings_copy = dict(clinic.settings or {})
            settings_copy["paused_for_subscription"] = True
            clinic.settings = settings_copy
            paused += 1
        if paused:
            await db.flush()
        return paused


async def get_clinic_for_update(db: AsyncSession, clinic_id: UUID) -> Clinic | None:
    result = await db.execute(select(Clinic).where(Clinic.id == clinic_id))
    return result.scalar_one_or_none()
