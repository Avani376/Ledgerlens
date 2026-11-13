"""R2 — Contract price leakage detector.

Spec: docs/04_DETECTION_RULES.md §R2.

Why it fires:
    Invoiced unit prices above the negotiated contract rate (or missed
    agreed discounts) are silent overcharges — the invoice looks normal,
    the PO may even approve it, but the contract governs.

TODO(C, Day 2): implement per spec. Return [] until then:
    join invoice line -> contract line on (vendor_id, normalized item)
    where contract.status = 'active' and contract covers invoice_date
    fire when unit_price > contracted_unit_price
    amount_at_risk = (unit_price - contracted_unit_price) * quantity * (1 + tax_pct/100)
    severity: high if unpaid, critical if paid
    reference example: INV-9102 bills LED Panel @ 465.00 vs C-001 @ 420.00
    -> 318.60 INR at risk (docs/04 §R2).
"""
from __future__ import annotations

from ..registry import DetectionContext, register
from ..types import Finding


@register("R2")
def detect_contract_price_leakage(ctx: DetectionContext) -> list[Finding]:
    return []
