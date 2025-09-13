import { useState, useMemo } from "react";
import Button from "../../components/shared/Button";
import { usePersistentState } from "../../hooks/usePersistanceStorage";
import SegmentDiscountCard, { ALL_PERKS } from "./SegmentDiscountCard";
import type { SegmentDiscountConfig } from "./SegmentDiscountCard";
import apiUtils from "../../utils/apiUtils";
import DiscountSummary from "./DiscountSummary";

type Strategy = "Balanced" | "Conservative" | "Aggressive";
type Props = { step: number; setStep: (n: number) => void };

export default function Discounts({ step, setStep }: Props) {
  const [email] = usePersistentState<string>("email", "");
  const [strategy, setStrategy] = useState<Strategy>("Balanced");

  // NEW: generation state flags
  const [isGenerating, setIsGenerating] = useState(false);
  const [showSummary, setShowSummary] = usePersistentState("discountSummary", false);

  const { generateDiscountsAPI } = apiUtils();

  const initialData: SegmentDiscountConfig[] = useMemo(
    () => [
      {
        cluster_id: 0,
        business_label: "Group Deal Seekers",
        baseline: { low: 0.12, shoulder: 0.10, high: 0.08 },
        boost_if_high_gap: 0.03,
        max_perk_cost: 35,
        perk_priority: ["bar_credit", "swimming_pool", "gym", "kids_club"],
      },
      {
        cluster_id: 1,
        business_label: "Family Vacationers",
        baseline: { low: 0.10, shoulder: 0.09, high: 0.07 },
        boost_if_high_gap: 0.02,
        max_perk_cost: 25,
        perk_priority: ["kids_club", "bar_credit", "swimming_pool", "spa"],
      },
      {
        cluster_id: 2,
        business_label: "Budget Online Travellers",
        baseline: { low: 0.08, shoulder: 0.06, high: 0.05 },
        boost_if_high_gap: 0.02,
        max_perk_cost: 15,
        perk_priority: ["gym", "swimming_pool", "bar_credit"],
      },
      {
        cluster_id: 3,
        business_label: "Frequent Work Travelers",
        baseline: { low: 0.08, shoulder: 0.06, high: 0.05 },
        boost_if_high_gap: 0.02,
        max_perk_cost: 20,
        perk_priority: ["work_desk", "meeting_room", "spa", "bar_credit", "gym"],
      },
      {
        cluster_id: 4,
        business_label: "Loyal Niche Guests",
        baseline: { low: 0.05, shoulder: 0.04, high: 0.03 },
        boost_if_high_gap: 0.02,
        max_perk_cost: 40,
        perk_priority: ["spa", "bar_credit", "swimming_pool", "gym", "work_desk", "meeting_room"],
      },
    ],
    []
  );

  const [config, setConfig] = usePersistentState<SegmentDiscountConfig[]>(
    "discountConfig",
    initialData
  );

  const onSegmentChange = (idx: number, next: SegmentDiscountConfig) => {
    const updated = [...config];
    updated[idx] = next;
    setConfig(updated);
  };

  const copyToAll = (source: SegmentDiscountConfig) => {
    const next = config.map((seg) => ({
      ...seg,
      baseline: { ...source.baseline },
      boost_if_high_gap: source.boost_if_high_gap,
      max_perk_cost: source.max_perk_cost,
      perk_priority: [...source.perk_priority],
    }));
    setConfig(next);
  };

  const applyStrategy = (mode: Strategy) => {
    const factor = mode === "Conservative" ? 0.8 : mode === "Aggressive" ? 1.25 : 1;
    const clamp01 = (n: number) => Math.max(0, Math.min(1, n));

    const next = config.map((seg) => ({
      ...seg,
      baseline: {
        low: clamp01(seg.baseline.low * factor),
        shoulder: clamp01(seg.baseline.shoulder * factor),
        high: clamp01(seg.baseline.high * factor),
      },
      boost_if_high_gap: clamp01(seg.boost_if_high_gap * factor),
    }));
    setConfig(next);
    setStrategy(mode);
  };

  const getPayload = () =>
    config.map((c) => ({
      cluster_id: c.cluster_id,
      business_label: c.business_label,
      baseline: c.baseline,
      boost_if_high_gap: c.boost_if_high_gap,
      max_perk_cost: c.max_perk_cost,
      perk_priority: c.perk_priority,
    }));

  const generateDiscounts = async () => {
    const issues: string[] = [];
    config.forEach((c) => {
      if (c.max_perk_cost < 0) issues.push(`${c.business_label}: Max perk cost cannot be negative`);
      (["low", "shoulder", "high"] as const).forEach((s) => {
        const v = c.baseline[s];
        if (v < 0 || v > 1) issues.push(`${c.business_label}: ${s} baseline should be 0–100%`);
      });
      if (c.boost_if_high_gap < 0 || c.boost_if_high_gap > 1)
        issues.push(`${c.business_label}: boost_if_high_gap should be 0–100%`);
      const invalid = c.perk_priority.filter((p) => !ALL_PERKS.includes(p));
      if (invalid.length) issues.push(`${c.business_label}: Invalid perks - ${invalid.join(", ")}`);
    });

    if (issues.length) {
      alert(`Please fix the following:\n\n- ${issues.join("\n- ")}`);
      return;
    }

    setIsGenerating(true); // NEW: disable button + show spinner
    try {
      const payload = getPayload();
      console.log("Segment Discount Array (ready to send):", payload);
      const response = await generateDiscountsAPI(email, payload);

      if (response?.success) {
        // Show summary view; Next will appear automatically
        setShowSummary(true);
      } else {
        alert("Failed to generate discounts.");
      }
    } catch (err) {
      console.error(err);
      alert("Something went wrong while generating discounts.");
    } finally {
      setIsGenerating(false); // NEW: stop spinner
    }
  };

  // Dynamic labels based on state
  const pageTitle = showSummary ? "Discount Summary" : "Step 4: Discount Generation";
  const pageSub =
    showSummary
      ? "Here’s your generated discount breakdown by segment, room, and month."
      : "Configure baselines (%), gap boost (%), max perk cost, and perk priority for each segment.";

  return (
    <div className="flex flex-col items-center pt-40 px-4">
      {/* Header */}
      <div className="relative w-full max-w-6xl mb-4 flex items-end">
        {/* Centered Title */}
        <div className="mx-auto text-center">
          <h1 className="text-2xl font-semibold text-gray-800">{pageTitle}</h1>
          <p className="text-gray-600 text-sm mt-1">{pageSub}</p>
        </div>

        {/* Right-aligned Strategy presets */}
        {!showSummary && (
          <div className="absolute right-0 flex items-center gap-2">
            <label className="text-sm text-gray-600">Strategy</label>
            <select
              className="border rounded px-2 py-1 text-sm"
              value={strategy}
              onChange={(e) => applyStrategy(e.target.value as Strategy)}
              disabled={isGenerating}
            >
              <option>Balanced</option>
              <option>Conservative</option>
              <option>Aggressive</option>
            </select>
          </div>
        )}
      </div>

      {/* Body */}
      {!showSummary ? (
        <div className="w-full max-w-6xl grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          {config.map((seg, idx) => (
            <SegmentDiscountCard
              key={seg.cluster_id}
              value={seg}
              onChange={(next) => onSegmentChange(idx, next)}
              onCopyToAll={() => copyToAll(seg)}
            />
          ))}
        </div>
      ) : (
        <DiscountSummary email={email} />
      )}

      {/* Spinner overlay while generating */}
      {isGenerating && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/60 backdrop-blur-sm">
          <div className="flex items-center gap-3 rounded-xl border bg-white px-4 py-3 shadow">
            <svg
              className="h-5 w-5 animate-spin"
              viewBox="0 0 24 24"
              fill="none"
              aria-hidden="true"
            >
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
              />
            </svg>
            <span className="text-sm text-gray-700">
              Generating discounts and pulling your summary…
            </span>
          </div>
        </div>
      )}

      {/* Spacer */}
      <div className="h-24" />

      {/* Sticky action bar */}
      <div
        className="
          fixed inset-x-0 bottom-0 z-40
          border-t border-gray-200
          bg-white/90 backdrop-blur supports-[backdrop-filter]:bg-white/70
          shadow-[0_-6px_12px_-8px_rgba(0,0,0,0.15)]
          py-3
          pb-[calc(0.75rem+env(safe-area-inset-bottom))]
        "
      >
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex flex-col">
              <span className="text-sm font-medium text-gray-800">{pageTitle}</span>
              <span className="text-xs text-gray-500">
                {showSummary
                  ? "Review your discount summary below."
                  : "Changes are saved locally. Use “Generate Discounts” to create your offers."}
              </span>
            </div>

            <div className="flex items-center gap-2 sm:gap-3">
              {/* Compact strategy on small screens (hide when in summary) */}
              {!showSummary && (
                <select
                  className="border rounded px-2 py-1 text-sm block sm:hidden"
                  value={strategy}
                  onChange={(e) => applyStrategy(e.target.value as Strategy)}
                  disabled={isGenerating}
                >
                  <option>Balanced</option>
                  <option>Conservative</option>
                  <option>Aggressive</option>
                </select>
              )}

              <Button
                type="normal"
                label="Back"
                onClick={() => setStep(step - 1)}
                disabled={isGenerating}
              />

              {/* Hide Generate button after summary is shown */}
              {!showSummary && (
                <Button
                  type="normal"
                  label={isGenerating ? "Generating…" : "Generate Discounts"}
                  onClick={generateDiscounts}
                  disabled={isGenerating}
                  aria-busy={isGenerating}
                />
              )}

              {/* Show Next only after summary is visible */}
              {showSummary && (
                <Button
                  type="normal"
                  label="Next"
                  onClick={() => setStep(step + 1)}
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
