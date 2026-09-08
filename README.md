# Tax Ledger — India Income Tax Calculator (FY 2025–26)

A full-stack calculator for Indian personal income tax under the **New Regime**
(default) and **Old Regime**, implementing the Union Budget FY 2025–26 rules:
a ₹75,000 standard deduction, a Section 87A rebate up to ₹12,00,000 taxable
income (with marginal relief above it), and Old Regime Chapter VI-A
deductions (80C / 80D / 24(b) / HRA).

The backend is a pure computation engine behind a thin FastAPI layer; the
frontend is a React + Vite + Tailwind single-page app. The two are fully
decoupled and can be deployed independently.

## Project structure

```
tax-calculator/
├── backend/
│   ├── main.py          # FastAPI app, CORS, routes
│   ├── schemas.py        # Pydantic v2 models (discriminated union requests)
│   ├── calculator.py      # Pure tax-math engine, no framework dependencies
│   ├── database.py        # SQLAlchemy engine/session (PostgreSQL)
│   ├── models.py           # CalculationLog ORM entity
│   ├── requirements.txt
│   └── tests/
│       └── test_calculator.py
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── src/
│       ├── main.jsx
│       ├── App.jsx
│       ├── api/client.js
│       ├── utils/format.js
│       └── components/
│           ├── TaxForm.jsx
│           ├── ResultCard.jsx
│           └── Comparison.jsx
└── infra/
    ├── Dockerfile.backend
    ├── Dockerfile.frontend
    ├── nginx.conf
    └── docker-compose.yml
```

## Tax rules implemented

### New Regime (default)
| Taxable income slab | Rate |
|---|---|
| ₹0 – ₹4,00,000 | Nil |
| ₹4,00,001 – ₹8,00,000 | 5% |
| ₹8,00,001 – ₹12,00,000 | 10% |
| ₹12,00,001 – ₹16,00,000 | 15% |
| ₹16,00,001 – ₹20,00,000 | 20% |
| ₹20,00,001 – ₹24,00,000 | 25% |
| Above ₹24,00,000 | 30% |

- Standard deduction: ₹75,000.
- Section 87A rebate: full rebate (up to ₹60,000) if taxable income ≤ ₹12,00,000.
- **Marginal relief**: for taxable income just above ₹12,00,000, tax payable
  (before cess) is capped at `taxable_income − ₹12,00,000`, so nobody earning
  slightly over the threshold ends up worse off than someone earning exactly
  ₹12,00,000. See `compute_new_regime` in `backend/calculator.py`.
- 4% Health & Education Cess on the post-rebate/relief tax.

### Old Regime
| Taxable income slab | Rate |
|---|---|
| Up to ₹2,50,000 | Nil |
| ₹2,50,001 – ₹5,00,000 | 5% |
| ₹5,00,001 – ₹10,00,000 | 20% |
| Above ₹10,00,000 | 30% |

- Standard deduction: ₹50,000.
- Deductions: 80C (capped ₹1,50,000), 80D, 24(b) (capped ₹2,00,000), HRA exemption.
- Section 87A rebate: full rebate (up to ₹12,500) if taxable income ≤ ₹5,00,000.
- 4% Health & Education Cess.

## Backend — local setup

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Run the API (http://localhost:8000, docs at /docs)
uvicorn main:app --reload

# Run the test suite
pytest tests/test_calculator.py -v
```

Environment variables (all optional, sensible defaults provided):

| Variable | Default | Purpose |
|---|---|---|
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:3000` | Comma-separated CORS allow-list |
| `DATABASE_URL` | `postgresql+psycopg2://tax_user:tax_pass@localhost:5432/tax_calculator` | Telemetry DB connection string |

### API reference

**POST `/api/v1/calculate`** — single-regime computation (discriminated on `regime_type`)

```bash
curl -X POST http://localhost:8000/api/v1/calculate \
  -H "Content-Type: application/json" \
  -d '{"regime_type": "new", "gross_income": 1500000}'
```

```json
{
  "regime": "new",
  "gross_income": 1500000,
  "total_deductions": 75000,
  "taxable_income": 1425000,
  "base_tax": 97500,
  "rebate_87a": 0,
  "marginal_relief": 0,
  "cess": 3900,
  "total_payable": 101400
}
```

For the Old Regime, add `"deductions": {"section_80c": 150000, "section_80d": 25000, "section_24b": 200000, "hra_exemption": 120000}`.

**POST `/api/v1/compare`** — evaluates both regimes and recommends the cheaper one:

```bash
curl -X POST http://localhost:8000/api/v1/compare \
  -H "Content-Type: application/json" \
  -d '{"gross_income": 1500000, "deductions": {"section_80c": 150000}}'
```

Returns `new_regime`, `old_regime`, `recommended_regime`, and `savings_amount`.

## Frontend — local setup

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173, proxies /api/* to localhost:8000
```

The UI has three tabs — New Regime, Old Regime, Compare Both — each backed by
the corresponding API call, with Indian Rupee formatting via
`Intl.NumberFormat('en-IN')` and inline validation-error surfacing for HTTP 422s.

## Deployment

**Backend**
- *Serverless*: `main.py` exposes a `handler` via `mangum.Mangum(app)` whenever
  `mangum` is installed — wire it to an AWS Lambda function behind API Gateway.
- *Container*: `infra/Dockerfile.backend` is a two-stage build
  (`python:3.11-slim`) suitable for AWS App Runner or Google Cloud Run.

**Frontend**
- `npm run build` produces `frontend/dist/`, deployable to AWS Amplify,
  Vercel, or Netlify with CI/CD from GitHub. `infra/Dockerfile.frontend`
  builds and serves the same bundle via nginx for container-based hosting.

**Database**
- `infra/docker-compose.yml` wires backend + frontend + a local Postgres
  container together for one-command local testing. In production, point
  `DATABASE_URL` at an AWS RDS PostgreSQL instance. Calculation telemetry
  (timestamp, regime, gross income, recommendation) is written via FastAPI
  `BackgroundTasks` in `main.py`, so a slow or unreachable database never
  adds latency to a user's request — see `log_calculation_async` in
  `backend/database.py`.

```bash
cd infra
docker compose up --build
```
