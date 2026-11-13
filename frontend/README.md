# LedgerLens Frontend

React + Vite + Tailwind dashboard. Backend API: `docs/05_API_SPEC.md` · Data model: `docs/03_DATA_MODEL.md`.

Owner: **D · Frontend lead** (see `docs/07_BUILD_PLAN.md`).

## Scaffold (run once — the app folder is not committed, only this spec)

```bash
cd frontend
npm create vite@latest app -- --template react
cd app
npm install
npm install tailwindcss @tailwindcss/vite
# then: add tailwind plugin to vite.config.js, `@import "tailwindcss";` in index.css
npm run dev
```

Point the app at the backend (Vite env, `.env.local`):

```
VITE_API_BASE=http://127.0.0.1:8000
```

## Pages to build

| Page | Route | What it shows | API used |
|------|-------|---------------|----------|
| **Upload** | `/` | Drag-drop CSV/PDF per kind (invoices, POs, contracts, payments); batch status; "Run detect" button | `POST /api/ingest/upload`, `POST /api/run/{batch}/detect` |
| **Dashboard** (exception queue) | `/findings` | Table sorted by amount at risk DESC: severity badge, rule, title, amount, status; filters by severity/rule/status; total-at-risk banner | `GET /api/findings` |
| **Finding detail** | `/findings/:id` | The explainability card: headline, explanation, recommended action, confidence; **evidence panel** listing every EvidenceRef as a chip (source · record_id · field · value); side-by-side source rows (invoice lines, PO line, contract line, payments); Approve / Reject / Request docs / Recovery buttons with note input | `GET /api/findings/{id}`, `POST /api/findings/{id}/decision` |
| **Audit memo** | `/memo` | Rendered markdown memo + copy button | `GET /api/memo` |

## Component sketch

```
<App>
 ├─ <Layout>            top bar: LedgerLens logo, total-at-risk badge
 ├─ <UploadPage>        <Dropzone kind=.../> ×4 · <BatchList/> · <RunDetectButton/>
 ├─ <FindingsTable>     <SeverityBadge/> <RuleTag/> <AmountCell/> <StatusPill/>
 ├─ <FindingDetail>     <ExplanationCard/> <EvidencePanel/> <DecisionButtons/>
 └─ <MemoPage>          <MarkdownView/> <CopyButton/>
```

## Design rules (this is an enterprise finance product)

- Calm, dense, professional: white background, one accent color, severity colors only for badges (`critical`=red, `high`=amber, `medium`=blue, `low`=gray).
- Amounts always show currency (`₹4,956.00`) — never a bare float.
- Every number on screen must trace to an EvidenceRef — if a designer can't cite the source, the number doesn't render.
- No scare words (the backend already avoids "fraud").
- Loading and empty states are part of the demo: queue with zero findings should say "No exceptions found — all clear" (that's a feature, not a blank screen).

## Nice-to-have (only if Day-2 Checkpoint 3 is done early)

- CSV export of findings
- "Explain again" button (re-calls explain stage)
- Rule filter chips on the dashboard
