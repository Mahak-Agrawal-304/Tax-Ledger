import { formatINR } from "../utils/format";

function Row({ label, value, muted = false, subtract = false }) {
  return (
    <div className="flex items-baseline justify-between py-2 border-b border-paper-line/70">
      <span className={muted ? "text-sm text-ink-muted" : "text-sm text-ink"}>
        {label}
      </span>
      <span className="figure font-mono text-ink">
        {subtract && value > 0 ? "−" : ""}
        {formatINR(Math.abs(value), { precise: true })}
      </span>
    </div>
  );
}

/**
 * Full computation breakdown for a single regime's TaxResponse.
 */
export default function ResultCard({ result, regimeLabel }) {
  if (!result) return null;

  const {
    gross_income,
    total_deductions,
    taxable_income,
    base_tax,
    rebate_87a,
    marginal_relief,
    cess,
    total_payable,
  } = result;

  return (
    <div>
      <div className="flex items-baseline justify-between border-b border-ink pb-3">
        <span className="font-display text-lg text-ink">{regimeLabel}</span>
        <span className="text-xs text-ink-muted">FY 2025-26</span>
      </div>

      <div className="mt-4">
        <Row label="Gross annual income" value={gross_income} />
        <Row label="Total deductions" value={total_deductions} subtract muted />
        <Row label="Taxable income" value={taxable_income} />
        <Row label="Tax on slabs" value={base_tax} muted />
        {rebate_87a > 0 && (
          <Row label="Rebate u/s 87A" value={rebate_87a} subtract muted />
        )}
        {marginal_relief > 0 && (
          <Row label="Marginal relief" value={marginal_relief} subtract muted />
        )}
        <Row label="Health & education cess (4%)" value={cess} muted />
      </div>

      <div className="mt-4 flex items-baseline justify-between bg-ledger px-4 py-4 text-paper">
        <span className="font-display text-base">Total tax payable</span>
        <span className="figure font-mono text-2xl">
          {formatINR(total_payable, { precise: true })}
        </span>
      </div>
    </div>
  );
}
