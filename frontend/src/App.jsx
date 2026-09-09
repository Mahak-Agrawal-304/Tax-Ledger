import { useState } from "react";
import { AlertCircle, Landmark } from "lucide-react";
import TaxForm from "./components/TaxForm";
import ResultCard from "./components/ResultCard";
import Comparison from "./components/Comparison";
import { calculateTax, compareRegimes } from "./api/client";

const TABS = [
  { id: "new", label: "New Regime" },
  { id: "old", label: "Old Regime" },
  { id: "compare", label: "Compare Both" },
];

const INITIAL_VALUES = {
  gross_income: 1_200_000,
  deductions: {
    section_80c: 0,
    section_80d: 0,
    section_24b: 0,
    hra_exemption: 0,
  },
};

export default function App() {
  const [regime, setRegime] = useState("new");
  const [values, setValues] = useState(INITIAL_VALUES);
  const [result, setResult] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const switchTab = (tab) => {
    setRegime(tab);
    setResult(null);
    setComparison(null);
    setError(null);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      if (regime === "compare") {
        const data = await compareRegimes({
          gross_income: values.gross_income,
          deductions: values.deductions,
        });
        setComparison(data);
        setResult(null);
      } else if (regime === "old") {
        const data = await calculateTax({
          regime_type: "old",
          gross_income: values.gross_income,
          deductions: values.deductions,
        });
        setResult(data);
        setComparison(null);
      } else {
        const data = await calculateTax({
          regime_type: "new",
          gross_income: values.gross_income,
        });
        setResult(data);
        setComparison(null);
      }
    } catch (err) {
      setError(err.message || "Something went wrong while calculating tax.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen">
      <div className="mx-auto max-w-4xl px-6 py-12">
        <header className="mb-10">
          <div className="flex items-center gap-2 text-ledger">
            <Landmark size={20} strokeWidth={1.75} />
            <span className="text-xs tracking-wide text-ink-muted">
              Union Budget FY 2025-26
            </span>
          </div>
          <h1 className="mt-2 font-display text-4xl text-ink">Tax Ledger</h1>
          <p className="mt-2 max-w-md text-sm text-ink-muted">
            Work out what you owe under India&apos;s New and Old income tax
            regimes, and see exactly which one leaves more in your pocket.
          </p>
        </header>

        <nav className="mb-8 flex gap-1 border-b border-paper-line">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => switchTab(tab.id)}
              className={`px-4 py-2.5 text-sm transition-colors ${
                regime === tab.id
                  ? "border-b-2 border-ledger text-ink font-medium"
                  : "text-ink-muted hover:text-ink"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>

        <div className={regime === "compare" ? "" : "grid gap-10 sm:grid-cols-2"}>
          <div className={regime === "compare" ? "mb-8 max-w-md" : ""}>
            <TaxForm
              regime={regime}
              values={values}
              onChange={setValues}
              onSubmit={handleSubmit}
              loading={loading}
            />

            {error && (
              <div className="mt-4 flex items-start gap-2 bg-brick/10 px-4 py-3 text-sm text-brick">
                <AlertCircle size={16} className="mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}
          </div>

          <div>
            {regime !== "compare" && result && (
              <ResultCard
                result={result}
                regimeLabel={regime === "new" ? "New Regime" : "Old Regime"}
              />
            )}
            {regime !== "compare" && !result && !error && (
              <p className="text-sm text-ink-muted">
                Enter your income and hit calculate to see the breakdown.
              </p>
            )}
          </div>
        </div>

        {regime === "compare" && comparison && (
          <Comparison comparison={comparison} />
        )}
      </div>
    </div>
  );
}
