"""
Pytest suite for backend/calculator.py
Covers slab boundaries, the Section 87A rebate cliff, marginal relief,
and Old Regime Chapter VI-A deduction handling for FY 2025-26.

Run from the `backend/` directory with:
    pytest tests/test_calculator.py -v
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from calculator import (
    compute_new_regime,
    compute_old_regime,
    compute_comparison,
    NEW_REGIME_STANDARD_DEDUCTION,
    OLD_REGIME_STANDARD_DEDUCTION,
)


# --------------------------------------------------------------------------
# New Regime
# --------------------------------------------------------------------------

class TestNewRegime:

    def test_zero_income(self):
        r = compute_new_regime(0)
        assert r["total_payable"] == 0

    def test_below_standard_deduction_is_fully_wiped(self):
        r = compute_new_regime(50_000)
        assert r["taxable_income"] == 0
        assert r["total_payable"] == 0

    def test_fully_rebated_at_12_75_lakh_gross(self):
        # 12,75,000 gross - 75,000 standard deduction = 12,00,000 taxable
        # -> exactly at the 87A threshold, tax fully rebated.
        r = compute_new_regime(1_275_000)
        assert r["taxable_income"] == 1_200_000
        assert r["base_tax"] == 60_000
        assert r["rebate_87a"] == 60_000
        assert r["total_payable"] == 0

    def test_within_5_percent_slab_still_rebated(self):
        # Gross 5,00,000 -> taxable 4,25,000 -> 5% of 25,000 = 1,250
        r = compute_new_regime(500_000)
        assert r["taxable_income"] == 425_000
        assert r["base_tax"] == pytest.approx(1_250)
        assert r["total_payable"] == 0  # still under the 12L rebate ceiling

    def test_marginal_relief_just_above_threshold(self):
        # Taxable income = 12,01,000 (Rs 1,000 over the rebate threshold).
        gross = 1_200_000 + NEW_REGIME_STANDARD_DEDUCTION + 1_000
        r = compute_new_regime(gross)
        assert r["taxable_income"] == 1_201_000
        # Without relief, base tax would be Rs 60,150 -- an unfair jump.
        assert r["base_tax"] == pytest.approx(60_150)
        assert r["marginal_relief"] > 0
        # Relief caps tax at the amount by which income exceeds Rs 12,00,000.
        assert r["tax_after_rebate"] == 1_000
        assert r["cess"] == pytest.approx(40)
        assert r["total_payable"] == pytest.approx(1_040)

    def test_marginal_relief_fades_out_further_from_threshold(self):
        # Once real slab tax exceeds the relief ceiling, relief no longer applies.
        r = compute_new_regime(2_000_000)
        assert r["marginal_relief"] == 0
        assert r["taxable_income"] == 2_000_000 - NEW_REGIME_STANDARD_DEDUCTION

    def test_top_slab_30_percent(self):
        r = compute_new_regime(5_000_000)
        taxable = 5_000_000 - NEW_REGIME_STANDARD_DEDUCTION
        assert r["taxable_income"] == taxable
        assert r["cess"] == pytest.approx(r["tax_after_rebate"] * 0.04, rel=1e-6)

    def test_negative_income_raises(self):
        with pytest.raises(ValueError):
            compute_new_regime(-100)


# --------------------------------------------------------------------------
# Old Regime
# --------------------------------------------------------------------------

class TestOldRegime:

    def test_zero_income(self):
        r = compute_old_regime(0, {})
        assert r["total_payable"] == 0

    def test_full_87a_rebate_at_5_lakh_taxable(self):
        gross = 500_000 + OLD_REGIME_STANDARD_DEDUCTION
        r = compute_old_regime(gross, {})
        assert r["taxable_income"] == 500_000
        assert r["rebate_87a"] == 12_500
        assert r["total_payable"] == 0

    def test_just_above_87a_threshold_no_rebate(self):
        gross = 500_001 + OLD_REGIME_STANDARD_DEDUCTION
        r = compute_old_regime(gross, {})
        assert r["taxable_income"] == 500_001
        assert r["rebate_87a"] == 0
        assert r["total_payable"] > 0

    def test_80c_cap_enforced_even_if_caller_overshoots(self):
        r = compute_old_regime(1_000_000, {"section_80c": 300_000})
        assert r["total_deductions"] == OLD_REGIME_STANDARD_DEDUCTION + 150_000

    def test_24b_cap_enforced_even_if_caller_overshoots(self):
        r = compute_old_regime(1_000_000, {"section_24b": 500_000})
        assert r["total_deductions"] == OLD_REGIME_STANDARD_DEDUCTION + 200_000

    def test_deductions_cannot_push_taxable_income_negative(self):
        r = compute_old_regime(60_000, {"section_80c": 150_000})
        assert r["taxable_income"] == 0
        assert r["total_payable"] == 0

    def test_top_slab_30_percent(self):
        r = compute_old_regime(1_500_000, {})
        taxable = 1_500_000 - OLD_REGIME_STANDARD_DEDUCTION
        # Slabs: 0-2.5L @0%, 2.5L-5L @5% (on 2.5L), 5L-10L @20% (on 5L), >10L @30%
        expected_base = (250_000 * 0.05) + (500_000 * 0.20) + ((taxable - 1_000_000) * 0.30)
        assert r["taxable_income"] == taxable
        assert r["base_tax"] == pytest.approx(expected_base)

    def test_negative_income_raises(self):
        with pytest.raises(ValueError):
            compute_old_regime(-1, {})


# --------------------------------------------------------------------------
# Comparison
# --------------------------------------------------------------------------

class TestComparison:

    def test_recommends_new_regime_for_high_income_no_deductions(self):
        r = compute_comparison(1_800_000, {})
        assert r["recommended_regime"] == "new"
        assert r["savings_amount"] > 0

    def test_recommends_old_regime_when_deductions_are_large_relative_to_income(self):
        # At Rs 15,00,000 gross with the maximum available Chapter VI-A
        # deductions, the Old Regime's lower taxable base outweighs the
        # New Regime's flatter slabs.
        deductions = {
            "section_80c": 150_000,
            "section_80d": 50_000,
            "section_24b": 200_000,
            "hra_exemption": 300_000,
        }
        r = compute_comparison(1_500_000, deductions)
        assert r["recommended_regime"] == "old"
        assert r["old_regime"]["total_payable"] < r["new_regime"]["total_payable"]

    def test_zero_income_returns_either(self):
        r = compute_comparison(0, {})
        assert r["recommended_regime"] == "either"
        assert r["savings_amount"] == 0
