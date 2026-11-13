"""R3 — PO mismatch & overbilling detector.

Spec: docs/04_DETECTION_RULES.md §R3.

Why it fires:
    Billing above PO quantity, before delivery, or for items not on the PO
    means the company pays for goods/services it never agreed to receive
    at that volume.

TODO(C, Day 1): implement per spec. Return [] until then:
    sum(invoice quantity) per (po_id, normalized item) across invoices
    fire overbilling when summed qty > po.quantity
      amount_at_risk = excess * po.unit_price * (1 + tax_pct/100)
    fire billed-before-delivery when invoice_date < po.expected_delivery (medium)
    fire unbilled-item when the invoiced item has no line on the PO (high)
    FP guard: partial billing across several invoices is legitimate —
    SUM first, then compare (docs/04 §R3).
    reference example: INV-9155 bills 60 x A4 Paper Box against PO-1008 qty 50
    -> 2,832.00 INR at risk.
"""
from __future__ import annotations

from ..registry import DetectionContext, register
from ..types import Finding


@register("R3")
def detect_po_mismatch(ctx: DetectionContext) -> list[Finding]:
    return []
