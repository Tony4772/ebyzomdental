"""Estimated Culqi + SUNAT fee breakdown for subscription pricing.

Culqi (CulqiOnline / CulqiLink, official precios as of 2026):
  - National cards / Yape: 3.44% + USD 0.20
  - Culqi commissions are *inafectas a IGV* (no IGV on the Culqi fee itself)

SUNAT / IGV on the SaaS sale (Peru):
  - Subscription price is treated as IGV-inclusive at 18%:
      igv = amount * 18 / 118
  - That is what you remit to SUNAT if you invoice the clinic with IGV.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from app.config import settings


def _cents(value: Decimal) -> int:
    return int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))


@dataclass(frozen=True)
class FeeBreakdown:
    """Operator-facing estimate of Culqi fee, sale IGV, and net."""

    amount_cents: int
    currency: str
    culqi_fee_cents: int
    sunat_igv_cents: int
    net_cents: int
    fee_percent: float
    fee_fixed_cents: int
    igv_percent: float
    culqi_igv_exempt: bool = True

    def as_dict(self) -> dict:
        return {
            "amount_cents": self.amount_cents,
            "currency": self.currency,
            "culqi_fee_cents": self.culqi_fee_cents,
            "sunat_igv_cents": self.sunat_igv_cents,
            "net_cents": self.net_cents,
            "fee_percent": self.fee_percent,
            "fee_fixed_cents": self.fee_fixed_cents,
            "igv_percent": self.igv_percent,
            "culqi_igv_exempt": self.culqi_igv_exempt,
        }


def estimate_fees(amount_cents: int, currency: str = "PEN") -> FeeBreakdown:
    """Estimate Culqi commission + IGV on the subscription sale.

    Formula (CulqiOnline national / Yape defaults):
      culqi_fee = amount * percent/100 + fixed_pen
      # Culqi fee itself is IGV-exempt (inafecta)
      sunat_igv = amount * igv / (100 + igv)   # IGV included in price
      net = amount - culqi_fee - sunat_igv
    """
    if amount_cents < 0:
        raise ValueError("amount_cents must be >= 0")

    percent = Decimal(str(settings.CULQI_FEE_PERCENT))
    fixed = Decimal(settings.CULQI_FEE_FIXED_CENTS)
    igv = Decimal(str(settings.CULQI_IGV_PERCENT))

    amount = Decimal(amount_cents)
    culqi = (amount * percent / Decimal(100)) + fixed
    # Sale IGV inclusive (not IGV-on-Culqi-fee — Culqi is inafecta).
    sunat = amount * igv / (Decimal(100) + igv) if igv > 0 else Decimal(0)
    net = amount - culqi - sunat

    return FeeBreakdown(
        amount_cents=amount_cents,
        currency=currency,
        culqi_fee_cents=_cents(culqi),
        sunat_igv_cents=_cents(sunat),
        net_cents=max(0, _cents(net)),
        fee_percent=float(percent),
        fee_fixed_cents=int(fixed),
        igv_percent=float(igv),
        culqi_igv_exempt=True,
    )
