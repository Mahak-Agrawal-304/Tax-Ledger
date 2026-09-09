"""
main.py
-------
FastAPI entrypoint for the India Tax Engine API (FY 2025-26).

Two endpoints:
  POST /api/v1/calculate  -> single-regime computation (discriminated union)
  POST /api/v1/compare    -> both regimes + savings recommendation

Calculation telemetry is logged via BackgroundTasks so database writes
never add latency to the user-facing response.
"""

import os
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

# Load variables from a local .env file (if present) before anything
# else reads os.getenv(...) below. No-op in production where the
# platform (Lambda/App Runner/ECS) injects real env vars directly.
load_dotenv()

from schemas import (
    CalculateRequest,
    ComparisonRequest,
    TaxResponse,
    ComparisonResponse,
    NewRegimeRequest,
)
from calculator import compute_new_regime, compute_old_regime, compute_comparison

try:
    from database import log_calculation_async
except Exception:  # pragma: no cover - DB layer is optional (e.g. local dev without Postgres)
    log_calculation_async = None

logger = logging.getLogger("tax_engine")

ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv(
        "ALLOWED_ORIGINS",
        "http://localhost:5173,http://localhost:3000",
    ).split(",")
    if origin.strip()
]

app = FastAPI(
    title="India Tax Engine API",
    description="Computes Indian Income Tax liability under the Old and New regimes, FY 2025-26.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _to_response(regime: str, result: dict) -> TaxResponse:
    return TaxResponse(
        regime=regime,
        gross_income=result["gross_income"],
        total_deductions=result["total_deductions"],
        taxable_income=result["taxable_income"],
        base_tax=result["base_tax"],
        rebate_87a=result["rebate_87a"],
        marginal_relief=result.get("marginal_relief", 0.0),
        cess=result["cess"],
        total_payable=result["total_payable"],
    )


def _queue_telemetry(background_tasks: BackgroundTasks, **kwargs) -> None:
    """Fire-and-forget calculation logging; silently no-ops if DB layer is unavailable."""
    if log_calculation_async is None:
        return
    try:
        background_tasks.add_task(log_calculation_async, **kwargs)
    except Exception:  # pragma: no cover - telemetry must never break a request
        logger.exception("Failed to queue calculation telemetry")


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/api/v1/calculate", response_model=TaxResponse)
def calculate(payload: CalculateRequest, background_tasks: BackgroundTasks) -> TaxResponse:
    if isinstance(payload, NewRegimeRequest):
        result = compute_new_regime(payload.gross_income)
        response = _to_response("new", result)
    else:
        result = compute_old_regime(payload.gross_income, payload.deductions.model_dump())
        response = _to_response("old", result)

    _queue_telemetry(
        background_tasks,
        regime=payload.regime_type,
        gross_income=payload.gross_income,
        recommended_regime=None,
    )
    return response


@app.post("/api/v1/compare", response_model=ComparisonResponse)
def compare(payload: ComparisonRequest, background_tasks: BackgroundTasks) -> ComparisonResponse:
    deductions = payload.deductions.model_dump() if payload.deductions else {}
    result = compute_comparison(payload.gross_income, deductions)

    response = ComparisonResponse(
        new_regime=_to_response("new", result["new_regime"]),
        old_regime=_to_response("old", result["old_regime"]),
        recommended_regime=result["recommended_regime"],
        savings_amount=result["savings_amount"],
    )

    _queue_telemetry(
        background_tasks,
        regime="compare",
        gross_income=payload.gross_income,
        recommended_regime=result["recommended_regime"],
    )
    return response


# --------------------------------------------------------------------------
# AWS Lambda (API Gateway) adapter -- only active when mangum is installed
# and the app is deployed as a serverless function.
# --------------------------------------------------------------------------
try:
    from mangum import Mangum

    handler = Mangum(app)
except ImportError:  # mangum is only required in the Lambda deployment target
    handler = None
