import { TrendingDown } from "lucide-react";
import ResultCard from "./ResultCard";
import { formatINR } from "../utils/format";

/**
 * Renders both regimes side by side and surfaces a clear "Recommended"
 * marker with the exact savings amount on whichever regime wins.
 */
export default function Comparison({ comparison }) {
  if (!comparison) return null;

  const { new_regime, old_regime, recommended_regime, savings_amount } = comparison;

  const panelClasses = (regime) =>
    `relative border p-5 ${
      recommended_regime === regime
        ? "border-marigold border-2"
        : "border-paper-line"
    }`;

  return (
    <div>
      {recommended_regime !== "either" ? (
        <div className="mb-5 flex items-center gap-2 bg-marigold/15 px-4 py-3 text-sm text-ink">
          <TrendingDown size={16} className="shrink-0 text-marigold" />
          <span>
            Recommended: the{" "}
            <strong className="font-semibold">
              {recommended_regime === "new" ? "New Regime" : "Old Regime"}
            </strong>{" "}
            saves you {formatINR(savings_amount, { precise: true })} this year.
          </span>
        </div>
      ) : (
        <div className="mb-5 bg-paper-line/40 px-4 py-3 text-sm text-ink-muted">
          Both regimes result in the same tax liability at this income level.
        </div>
      )}

      <div className="grid gap-6 sm:grid-cols-2">
        <div className={panelClasses("new")}>
          {recommended_regime === "new" && (
            <span className="absolute -top-3 left-4 bg-marigold px-2 py-0.5 text-xs text-paper">
              Recommended
            </span>
          )}
          <ResultCard result={new_regime} regimeLabel="New Regime" />
        </div>
        <div className={panelClasses("old")}>
          {recommended_regime === "old" && (
            <span className="absolute -top-3 left-4 bg-marigold px-2 py-0.5 text-xs text-paper">
              Recommended
            </span>
          )}
          <ResultCard result={old_regime} regimeLabel="Old Regime" />
        </div>
      </div>
    </div>
  );
}
