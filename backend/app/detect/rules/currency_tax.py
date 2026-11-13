"""R4 — Currency & tax error detector.

Spec: docs/04_DETECTION_RULES.md §R4.

Why it fires:
    Wrong currency, stale FX conversion, duplicate tax lines, or tax applied
    where an exemption applies each silently inflate what the company pays.
    Data-entry errors and currency mismatches account for ~20% each of
    enterprise payment-error value.

TODO(C, Day 2): implement per spec. Return [] until then:
    currency-mismatch: invoice.currency != po.currency for the same item (high)
    fx-error:          payment.fx_rate_to_inr deviates > 2% from the
                       reference rate (app.normalize.REFERENCE_FX_RATES) (high)
    tax-error:         invoice.tax_pct != contract.tax_pct for the item
                       amount_at_risk = tax delta (high)
    duplicate-tax:     same (invoice, item) charged tax twice (high)
    reference examples: INV-9201 billed in EUR against USD PO-1003;
                        INV-9301 applies 18% GST to freight that C-004
                        marks exempt -> 2,700.00 INR tax at risk.
"""
from __future__ import annotations

from ..registry import DetectionContext, register
from ..types import Finding


@register("R4")
def detect_currency_tax_errors(ctx: DetectionContext) -> list[Finding]:
    return []
