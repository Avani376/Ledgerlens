"""R5 — Cancelled-service leakage detector.

Spec: docs/04_DETECTION_RULES.md §R5.

Why it fires:
    Vendors keep billing recurring charges for cancelled software,
    terminated contracts, or returned goods. Nobody in AP connects the
    cancellation memo to next month's invoice — LedgerLens does.

TODO(C, Day 2): implement per spec. Return [] until then:
    join invoice line -> contract line on (vendor_id, normalized item)
    fire when contract.status = 'cancelled' and invoice_date > contract.end_date
      amount_at_risk = line_total
      severity: critical if paid (recovery task), high if unpaid
    also fire when the referenced po has status 'cancelled'
    FP guard: require ITEM-LEVEL match with the cancelled contract line;
    one-off (non-recurring) items get medium instead of critical.
    reference example: INV-9250 CloudSuite 29,500.00 INR paid 2026-10-10,
    contract C-005 cancelled effective 2026-09-30.
"""
from __future__ import annotations

from ..registry import DetectionContext, register
from ..types import Finding


@register("R5")
def detect_cancelled_service_leakage(ctx: DetectionContext) -> list[Finding]:
    return []
