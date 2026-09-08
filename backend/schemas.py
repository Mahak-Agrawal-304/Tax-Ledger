"""
schemas.py
----------
Pydantic v2 request/response models for the India Tax Engine API.

Uses a discriminated union (on `regime_type`) so FastAPI can validate
and route New vs Old regime payloads to the correct branch with a
single endpoint, while keeping strict numeric bounds on every field.
"""

from typing import Literal, Union, Optional

from pydantic import BaseModel, Field
from typing_extensions import Annotated


# --------------------------------------------------------------------------
# Shared sub-models
# --------------------------------------------------------------------------

class OldRegimeDeductions(BaseModel):
    """Chapter VI-A style deductions applicable only under the Old Regime."""

    section_80c: float = Field(
        default=0, ge=0, le=150_000,
        description="Sec 80C: PF, ELSS, life insurance premium, PPF, etc. Capped at Rs 1,50,000.",
    )
    section_80d: float = Field(
        default=0, ge=0, le=100_000,
        description="Sec 80D: health insurance premium (self/family/parents).",
    )
    section_24b: float = Field(
        default=0, ge=0, le=200_000,
        description="Sec 24(b): home loan interest on a self-occupied property. Capped at Rs 2,00,000.",
    )
    hra_exemption: float = Field(
        default=0, ge=0,
        description="Exempt portion of House Rent Allowance as per Sec 10(13A) computation.",
    )


# --------------------------------------------------------------------------
# /api/v1/calculate — discriminated union request
# --------------------------------------------------------------------------

class NewRegimeRequest(BaseModel):
    regime_type: Literal["new"] = "new"
    gross_income: float = Field(..., ge=0, le=1_000_000_000, description="Gross annual income in INR")


class OldRegimeRequest(BaseModel):
    regime_type: Literal["old"] = "old"
    gross_income: float = Field(..., ge=0, le=1_000_000_000, description="Gross annual income in INR")
    deductions: OldRegimeDeductions = Field(default_factory=OldRegimeDeductions)


CalculateRequest = Annotated[
    Union[NewRegimeRequest, OldRegimeRequest],
    Field(discriminator="regime_type"),
]


# --------------------------------------------------------------------------
# /api/v1/compare — unified request evaluating both regimes at once
# --------------------------------------------------------------------------

class ComparisonRequest(BaseModel):
    gross_income: float = Field(..., ge=0, le=1_000_000_000)
    deductions: Optional[OldRegimeDeductions] = Field(default_factory=OldRegimeDeductions)


# --------------------------------------------------------------------------
# Responses
# --------------------------------------------------------------------------

class TaxResponse(BaseModel):
    regime: Literal["new", "old"]
    gross_income: float
    total_deductions: float
    taxable_income: float
    base_tax: float
    rebate_87a: float
    marginal_relief: float = 0.0
    cess: float
    total_payable: float


class ComparisonResponse(BaseModel):
    new_regime: TaxResponse
    old_regime: TaxResponse
    recommended_regime: Literal["new", "old", "either"]
    savings_amount: float
