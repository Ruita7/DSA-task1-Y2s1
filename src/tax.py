"""Kenya tax calculation helpers for the smart parking system.

This module is a configurable VAT calculator. The default rate is 16%,
which is the general VAT rate published by KRA for taxable supplies.
Whether a particular parking operator should charge VAT depends on the
operator's tax status and the tax treatment of the supply.
"""

from dataclasses import dataclass

from .config import VAT_RATE, VAT_ENABLED


@dataclass(frozen=True)
class TaxBreakdown:
    subtotal: float
    tax_rate: float
    tax_amount: float
    total: float


def calculate_tax(subtotal: float) -> TaxBreakdown:
    """Calculate configurable VAT and the final amount payable."""
    subtotal = max(0.0, float(subtotal))
    rate = VAT_RATE if VAT_ENABLED else 0.0
    tax_amount = round(subtotal * rate, 2)
    total = round(subtotal + tax_amount, 2)

    return TaxBreakdown(
        subtotal=round(subtotal, 2),
        tax_rate=rate,
        tax_amount=tax_amount,
        total=total,
    )
