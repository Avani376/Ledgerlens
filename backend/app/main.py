"""LedgerLens API — routes follow docs/05_API_SPEC.md.

Endpoint status (see docs/07_BUILD_PLAN.md for who implements what):
  [done] GET  /health
  [done] POST /api/ingest/upload            — stores file, validates CSV, creates batch
  [done] POST /api/run/{batch_id}/detect    — normalize + R1..R5 over the DB
  [done] GET  /api/findings                 — exception queue
  [done] GET  /api/findings/{id}            — finding + evidence detail
  [done] POST /api/findings/{id}/decision   — approve/reject/request_docs/recovery
  [done] GET  /api/memo                     — deterministic audit memo
  [todo] POST /api/run/{batch_id}/extract   — Gemini extraction (AI lead, docs/06)
"""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile

from . import config
from .db import get_connection, init_schema
from .ingest.router import VALID_KINDS, save_stream_to_upload, validate_csv
from .models import DecisionIn
from .services import build_memo, record_decision, run_detection


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_schema(get_connection())
    yield


app = FastAPI(
    title="LedgerLens API",
    version=config.APP_VERSION,
    description="Explainable AI money-leak auditor. Gemini extracts and explains; "
                "the rules engine decides; the workflow logs.",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "version": config.APP_VERSION}


@app.post("/api/ingest/upload")
async def upload(kind: str = Form(...), file: UploadFile = File(...)) -> dict:
    """Store an uploaded CSV/PDF, validate CSV headers, register a batch (docs/05)."""
    if kind not in VALID_KINDS:
        raise HTTPException(status_code=400, detail=f"unknown kind: {kind}")

    conn = get_connection()
    try:
        cur = conn.execute("SELECT COUNT(*) AS n FROM batches")
        batch_id = f"B-{cur.fetchone()['n'] + 1:04d}"
        dest = save_stream_to_upload(file.file, file.filename or "upload", batch_id)

        problems: list[str] = []
        rows_detected = 0
        if dest.suffix.lower() == ".csv":
            problems = validate_csv(dest, kind)
            with dest.open("r", encoding="utf-8", errors="replace") as fh:
                rows_detected = max(sum(1 for _ in fh) - 1, 0)

        conn.execute(
            "INSERT INTO batches (batch_id, kind, stored_path, rows_detected) "
            "VALUES (?, ?, ?, ?)",
            (batch_id, kind, str(dest), rows_detected),
        )
        conn.commit()
        return {"batch_id": batch_id, "kind": kind, "stored": str(dest),
                "rows_detected": rows_detected, "problems": problems}
    finally:
        conn.close()


@app.post("/api/run/{batch_id}/extract")
def run_extract(batch_id: str) -> dict:
    # TODO(B, Day 1): iterate batch files, call app.extract.gemini_extract,
    # write parsed rows into tables, mark batch state='extracted'. See docs/06.
    raise HTTPException(status_code=501,
                        detail="Gemini extraction not implemented yet — docs/06_GEMINI_INTEGRATION.md")


@app.post("/api/run/{batch_id}/detect")
def run_detect(batch_id: str) -> dict:
    conn = get_connection()
    try:
        result = run_detection(conn)
        conn.execute("UPDATE batches SET state = 'detected' WHERE batch_id = ?", (batch_id,))
        conn.commit()
        result["batch_id"] = batch_id
        return result
    finally:
        conn.close()


@app.get("/api/findings")
def list_findings(status: str | None = None, severity: str | None = None,
                  rule_id: str | None = None) -> list[dict]:
    query = "SELECT * FROM findings WHERE 1=1"
    params: list = []
    if status:
        query += " AND status = ?"
        params.append(status)
    if severity:
        query += " AND severity = ?"
        params.append(severity)
    if rule_id:
        query += " AND rule_id = ?"
        params.append(rule_id)
    query += " ORDER BY amount_at_risk DESC"

    conn = get_connection()
    try:
        rows = [dict(r) for r in conn.execute(query, params).fetchall()]
    finally:
        conn.close()
    for row in rows:
        row["entity_refs"] = json.loads(row.get("entity_refs") or "{}")
        row["evidence"] = json.loads(row.get("evidence") or "[]")
    return rows


@app.get("/api/findings/{finding_id}")
def get_finding(finding_id: str) -> dict:
    conn = get_connection()
    try:
        row = conn.execute("SELECT * FROM findings WHERE finding_id = ?",
                           (finding_id,)).fetchone()
    finally:
        conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"finding not found: {finding_id}")
    finding = dict(row)
    finding["entity_refs"] = json.loads(finding.get("entity_refs") or "{}")
    finding["evidence"] = json.loads(finding.get("evidence") or "[]")
    if finding.get("explanation"):
        finding["explanation"] = json.loads(finding["explanation"])
    return finding


@app.post("/api/findings/{finding_id}/decision")
def decide(finding_id: str, body: DecisionIn) -> dict:
    conn = get_connection()
    try:
        return record_decision(conn, finding_id, body.action, body.reviewer, body.note)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        conn.close()


@app.get("/api/memo")
def memo() -> dict:
    conn = get_connection()
    try:
        return {"memo_markdown": build_memo(conn)}
    finally:
        conn.close()
