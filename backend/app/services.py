"""Service layer between the API routes and the deterministic core.

Everything in this module is deliberately framework-free (stdlib + app.detect only)
so the full pipeline is unit-testable without installing FastAPI.
"""
from __future__ import annotations

import json
import sqlite3

from .detect import DetectionContext, run_all


def _rows(conn: sqlite3.Connection, table: str) -> list[dict]:
    return [dict(row) for row in conn.execute(f"SELECT * FROM {table}").fetchall()]


def run_detection(conn: sqlite3.Connection) -> dict:
    """Load normalized tables, run every registered rule, persist findings.

    Returns {"findings_created": int, "finding_ids": [...]}.
    """
    ctx = DetectionContext(
        invoices=_rows(conn, "invoices"),
        payments=_rows(conn, "payments"),
        purchase_orders=_rows(conn, "purchase_orders"),
        contracts=_rows(conn, "contracts"),
        vendors=_rows(conn, "vendors"),
    )
    findings = run_all(ctx)

    existing = conn.execute("SELECT COUNT(*) AS n FROM findings").fetchone()["n"]
    created: list[str] = []
    for offset, finding in enumerate(findings):
        finding_id = f"F-{existing + offset + 1:04d}"
        conn.execute(
            """INSERT OR REPLACE INTO findings
               (finding_id, rule_id, title, severity, amount_at_risk, currency,
                status, entity_refs, evidence, confidence, summary)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                finding_id,
                finding.rule_id,
                finding.title,
                finding.severity,
                finding.amount_at_risk,
                finding.currency,
                "open",
                json.dumps(finding.entity_refs),
                json.dumps([e.as_dict() for e in finding.evidence]),
                finding.confidence,
                finding.summary,
            ),
        )
        created.append(finding_id)
    conn.commit()
    return {"findings_created": len(created), "finding_ids": created}


def record_decision(conn: sqlite3.Connection, finding_id: str, action: str,
                    reviewer: str, note: str = "") -> dict:
    """Apply a reviewer decision, update the finding status, append to audit_log."""
    status_by_action = {
        "approve": "approved",
        "reject": "rejected",
        "request_docs": "open",
        "recovery": "recovery",
    }
    if action not in status_by_action:
        raise ValueError(f"unknown action: {action}")

    row = conn.execute("SELECT finding_id FROM findings WHERE finding_id = ?",
                       (finding_id,)).fetchone()
    if row is None:
        raise LookupError(f"finding not found: {finding_id}")

    conn.execute("UPDATE findings SET status = ? WHERE finding_id = ?",
                 (status_by_action[action], finding_id))
    conn.execute(
        "INSERT INTO decisions (finding_id, action, reviewer, note) VALUES (?, ?, ?, ?)",
        (finding_id, action, reviewer, note),
    )
    conn.execute(
        """INSERT INTO audit_log (actor, action, object_type, object_id, detail)
           VALUES (?, ?, 'finding', ?, ?)""",
        (reviewer, action, finding_id, note),
    )
    conn.commit()
    return {"finding_id": finding_id, "status": status_by_action[action]}


def build_memo(conn: sqlite3.Connection) -> str:
    """Deterministic one-page audit memo (markdown). Gemini may polish only the
    executive summary — the numbers always come from here (docs/06 §5)."""
    findings = [dict(r) for r in conn.execute(
        "SELECT * FROM findings ORDER BY amount_at_risk DESC").fetchall()]

    total_at_risk = sum(f["amount_at_risk"] for f in findings
                        if f["status"] in ("open", "approved", "recovery"))
    by_rule: dict[str, float] = {}
    for f in findings:
        by_rule[f["rule_id"]] = by_rule.get(f["rule_id"], 0.0) + f["amount_at_risk"]

    lines = [
        "# LedgerLens Audit Memo",
        "",
        f"**Total at risk:** {total_at_risk:,.2f} across {len(findings)} finding(s).",
        "",
        "## Findings by rule",
    ]
    for rule_id in sorted(by_rule):
        lines.append(f"- **{rule_id}** — {by_rule[rule_id]:,.2f} at risk")
    lines += ["", "## Top findings"]
    for f in findings:
        lines.append(
            f"- [{f['severity'].upper()}] {f['finding_id']} · {f['title']} — "
            f"{f['amount_at_risk']:,.2f} {f['currency']} ({f['status']})"
        )
    return "\n".join(lines)
