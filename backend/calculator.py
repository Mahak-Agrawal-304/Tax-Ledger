"""
calculator.py
--------------
Pure mathematical tax computation engine for Indian Income Tax,
Union Budget FY 2025-26 (Assessment Year 2026-27).

Design note: this module has ZERO dependencies on FastAPI, Pydantic,
SQLAlchemy, or any web/ORM layer. It is plain Python so it can be
unit-tested in complete isolation and reused from any interface
(HTTP API, CLI, notebook, etc).
"""

from typing import Optional, List, Tuple

# --------------------------------------------------------------------------
# Constants (Budget FY 2025-26)
# --------------------------------------------------------------------------

NEW_REGIME_STANDARD_DEDUCTION = 75_000
OLD_REGIME_STANDARD_DEDUCTION = 50_000

# Each slab: (lower_bound_inclusive, upper_bound_exclusive_ceiling, rate)
NEW_REGIME_SLABS: List[Tuple[float, float, float]] = [
    (0, 400_000, 0.00),
    (400_000, 800_000, 0.05),
    (800_000, 1_200_000, 0.10),
    (1_200_000, 1_600_000, 0.15),
    (1_600_000, 2_000_000, 0.20),
    (2_000_000, 2_400_000, 0.25),
    (2_400_000, float("inf"), 0.30),
]

OLD_REGIME_SLABS: List[Tuple[float, float, float]] = [
    (0, 250_000, 0.00),
    (250_000, 500_000, 0.05),
    (500_000, 1_000_000, 0.20),
    (1_000_000, float("inf"), 0.30),
]

NEW_REGIME_REBATE_THRESHOLD = 1_200_000   # taxable income ceiling for full 87A rebate
NEW_REGIME_REBATE_CAP = 60_000            # max rebate amount under New Regime

OLD_REGIME_REBATE_THRESHOLD = 500_000     # taxable income ceiling for full 87A rebate
OLD_REGIME_REBATE_CAP = 12_500            # max rebate amount under Old Regime

CESS_RATE = 0.04                          # Health & Education Cess

SECTION_80C_CAP = 150_000
SECTION_24B_CAP = 200_000


# --------------------------------------------------------------------------
# Shared helpers
# --------------------------------------------------------------------------

def _slab_tax(taxable_income: float, slabs: List[Tuple[float, float, float]]) -> float:
    """
    Compute tax strictly via progressive slab rates. Does NOT apply any
    rebate, marginal relief, or cess -- those are handled by the caller.
    """
    if taxable_income <= 0:
        return 0.0

    tax = 0.0
    for lower, upper, rate in slabs:
        if taxable_income <= lower:
            break
        slab_amount = min(taxable_income, upper) - lower
        tax += slab_amount * rate

    return round(tax, 2)


# --------------------------------------------------------------------------
# New Regime (default regime, FY 2025-26)
# --------------------------------------------------------------------------

def compute_new_regime(gross_income: float) -> dict:
    """
    Compute tax liability under the New Regime.

    Pipeline:
      1. Subtract flat standard deduction (Rs 75,000).
      2. Apply progressive slab rates -> base_tax.
      3. Section 87A rebate: if taxable_income <= Rs 12,00,000, the
         entire base_tax is rebated (capped at Rs 60,000 -- which is
         exactly the tax due at Rs 12,00,000, so the cap never actually
         binds under current slabs, but is kept explicit per the law's
         wording and as a safety net against future slab changes).
      4. Marginal relief: for taxable_income just above Rs 12,00,000,
         tax payable is capped at (taxable_income - Rs 12,00,000) so a
         person is never left worse off than someone earning exactly
         the threshold amount.
      5. 4% Health & Education Cess on the post-rebate/relief tax.
    """
    if gross_income < 0:
        raise ValueError("gross_income cannot be negative")

    standard_deduction = min(gross_income, NEW_REGIME_STANDARD_DEDUCTION)
    taxable_income = max(0.0, gross_income - standard_deduction)

    base_tax = _slab_tax(taxable_income, NEW_REGIME_SLABS)

    rebate_87a = 0.0
    marginal_relief = 0.0

    if taxable_income <= NEW_REGIME_REBATE_THRESHOLD:
        rebate_87a = min(base_tax, NEW_REGIME_REBATE_CAP)
        tax_after_rebate = round(base_tax - rebate_87a, 2)
    else:
        excess_income = taxable_income - NEW_REGIME_REBATE_THRESHOLD
        if base_tax > excess_income:
            marginal_relief = round(base_tax - excess_income, 2)
            tax_after_rebate = round(excess_income, 2)
        else:
            tax_after_rebate = base_tax

    cess = round(tax_after_rebate * CESS_RATE, 2)
    total_payable = round(tax_after_rebate + cess, 2)

    return {
        "regime": "new",
        "gross_income": round(gross_income, 2),
        "standard_deduction": round(standard_deduction, 2),
        "total_deductions": round(standard_deduction, 2),
        "taxable_income": round(taxable_income, 2),
        "base_tax": base_tax,
        "rebate_87a": rebate_87a,
        "marginal_relief": marginal_relief,
        "tax_after_rebate": tax_after_rebate,
        "cess": cess,
        "total_payable": total_payable,
    }


# --------------------------------------------------------------------------
# Old Regime
# --------------------------------------------------------------------------

def compute_old_regime(gross_income: float, deductions: Optional[dict] = None) -> dict:
    """
    Compute tax liability under the Old Regime, including Chapter VI-A
    deductions (80C, 80D, 24(b)) and HRA exemption.

    `deductions` accepts a plain dict with keys:
        section_80c, section_80d, section_24b, hra_exemption
    Any missing key defaults to 0. 80C and 24(b) are hard-capped
    regardless of what the caller supplies, mirroring statutory limits.
    """
    if gross_income < 0:
        raise ValueError("gross_income cannot be negative")

    deductions = deductions or {}
    section_80c = min(float(deductions.get("section_80c", 0) or 0), SECTION_80C_CAP)
    section_80d = float(deductions.get("section_80d", 0) or 0)
    section_24b = min(float(deductions.get("section_24b", 0) or 0), SECTION_24B_CAP)
    hra_exemption = float(deductions.get("hra_exemption", 0) or 0)

    standard_deduction = min(gross_income, OLD_REGIME_STANDARD_DEDUCTION)
    chapter_via_total = section_80c + section_80d + section_24b + hra_exemption

    total_deductions = standard_deduction + chapter_via_total
    # Deductions can never reduce taxable income below zero.
    total_deductions = min(total_deductions, gross_income)

    taxable_income = max(0.0, gross_income - total_deductions)

    base_tax = _slab_tax(taxable_income, OLD_REGIME_SLABS)

    rebate_87a = 0.0
    if taxable_income <= OLD_REGIME_REBATE_THRESHOLD:
        rebate_87a = min(base_tax, OLD_REGIME_REBATE_CAP)

    tax_after_rebate = round(base_tax - rebate_87a, 2)
    cess = round(tax_after_rebate * CESS_RATE, 2)
    total_payable = round(tax_after_rebate + cess, 2)

    return {
        "regime": "old",
        "gross_income": round(gross_income, 2),
        "standard_deduction": round(standard_deduction, 2),
        "chapter_via_deductions": round(chapter_via_total, 2),
        "total_deductions": round(total_deductions, 2),
        "taxable_income": round(taxable_income, 2),
        "base_tax": base_tax,
        "rebate_87a": rebate_87a,
        "marginal_relief": 0.0,
        "tax_after_rebate": tax_after_rebate,
        "cess": cess,
        "total_payable": total_payable,
    }


# --------------------------------------------------------------------------
# Comparison
# --------------------------------------------------------------------------

def compute_comparison(gross_income: float, deductions: Optional[dict] = None) -> dict:
    """
    Run both regimes against the same gross income and recommend
    whichever produces the lower total tax payable.
    """
    new_result = compute_new_regime(gross_income)
    old_result = compute_old_regime(gross_income, deductions)

    delta = round(old_result["total_payable"] - new_result["total_payable"], 2)

    if delta > 0:
        recommended_regime = "new"
        savings_amount = delta
    elif delta < 0:
        recommended_regime = "old"
        savings_amount = round(-delta, 2)
    else:
        recommended_regime = "either"
        savings_amount = 0.0

    return {
        "new_regime": new_result,
        "old_regime": old_result,
        "recommended_regime": recommended_regime,
        "savings_amount": savings_amount,
    }
