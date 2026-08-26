"""Platform SaaS subscription payments (Culqi)."""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, TimestampMixin


class PlatformSubscriptionPayment(Base, TimestampMixin):
    """One Culqi charge for a clinic's SaaS subscription period."""

    __tablename__ = "platform_subscription_payments"

    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    clinic_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("clinics.id"),
        nullable=False,
        index=True,
    )
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, server_default="PEN")
    # card | yape
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, server_default="pending")
    culqi_charge_id: Mapped[str | None] = mapped_column(String(64), nullable=True, unique=True)
    culqi_fee_cents: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    sunat_igv_cents: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    net_cents: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    period_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    period_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_response: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
