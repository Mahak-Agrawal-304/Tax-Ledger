import { Calculator } from "lucide-react";
import { formatINR } from "../utils/format";

const DEDUCTION_FIELDS = [
  { key: "section_80c", label: "Section 80C (PF, ELSS, life insurance)", cap: 150_000 },
  { key: "section_80d", label: "Section 80D (health insurance premium)", cap: 100_000 },
  { key: "section_24b", label: "Section 24(b) (home loan interest)", cap: 200_000 },
  { key: "hra_exemption", label: "HRA exemption", cap: null },
];

function LedgerField({ label, value, onChange, cap, autoFocus = false }) {
  const overCap = cap != null && value > cap;
  return (
    <div className="py-3">
      <div className="flex items-baseline justify-between gap-4">
        <label className="text-sm text-ink-muted">{label}</label>
        {cap != null && (
          <span className="text-xs text-ink-muted/70 font-mono">
            cap {formatINR(cap)}
          </span>
        )}
      </div>
      <div className="mt-1 flex items-baseline gap-2 border-b border-paper-line focus-within:border-ledger transition-colors">
        <span className="text-ink-muted font-mono">₹</span>
        <input
          type="number"
          min="0"
          step="1000"
          inputMode="decimal"
          autoFocus={autoFocus}
          value={value === 0 ? "" : value}
          onChange={(e) => onChange(e.target.value === "" ? 0 : Number(e.target.value))}
          placeholder="0"
          className="w-full bg-transparent py-1.5 font-mono text-lg text-ink outline-none placeholder:text-ink-muted/40"
        />
      </div>
      {overCap && (
        <p className="mt-1 text-xs text-brick">
          Only {formatINR(cap)} is deductible; the excess won&apos;t reduce your tax.
        </p>
      )}
    </div>
  );
}

/**
 * Controlled form for gross income + (for Old Regime / Compare) Chapter
 * VI-A deductions. Parent owns all state via `values` / `onChange`.
 */
export default function TaxForm({ regime, values, onChange, onSubmit, loading }) {
  const showDeductions = regime === "old" || regime === "compare";

  const handleField = (key) => (val) =>
    onChange({ ...values, [key]: val });

  const handleDeduction = (key) => (val) =>
    onChange({
      ...values,
      deductions: { ...values.deductions, [key]: val },
    });

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        onSubmit();
      }}
      className="divide-y divide-paper-line"
    >
      <LedgerField
        label="Gross annual income"
        value={values.gross_income}
        onChange={handleField("gross_income")}
        autoFocus
      />

      {showDeductions && (
        <div>
          <p className="pt-4 text-xs text-ink-muted">
            Chapter VI-A deductions — Old Regime only
          </p>
          {DEDUCTION_FIELDS.map((field) => (
            <LedgerField
              key={field.key}
              label={field.label}
              cap={field.cap}
              value={values.deductions[field.key]}
              onChange={handleDeduction(field.key)}
            />
          ))}
        </div>
      )}

      <div className="pt-5">
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center gap-2 bg-ledger px-5 py-2.5 text-paper transition-colors hover:bg-ledger-dark disabled:opacity-60"
        >
          <Calculator size={16} strokeWidth={2} />
          {loading ? "Calculating…" : "Calculate"}
        </button>
      </div>
    </form>
  );
}
