import React from "react";

// --- Shared Perks (accepted) ---
export const ALL_PERKS = [
  "spa",
  "gym",
  "kids_club",
  "bar_credit",
  "swimming_pool",
  "work_desk",
  "meeting_room",
] as const;

export type PerkKey = typeof ALL_PERKS[number];

export const PERK_LABELS: Record<PerkKey, string> = {
  spa: "Spa Access",
  gym: "Gym Access",
  kids_club: "Kids Club",
  bar_credit: "Bar Credit",
  swimming_pool: "Swimming Pool",
  work_desk: "Work Desk",
  meeting_room: "Meeting Room",
};

// --- Types ---
export interface SegmentDiscountConfig {
  cluster_id: number;
  business_label: string;
  baseline: { low: number; shoulder: number; high: number }; // decimals (0-1)
  boost_if_high_gap: number; // decimal (0-1)
  max_perk_cost: number; // currency
  perk_priority: PerkKey[]; // ordered list (priority)
}

interface Props {
  value: SegmentDiscountConfig;
  onChange: (next: SegmentDiscountConfig) => void;
  onCopyToAll?: () => void; // NEW: copy this card's values to all segments
}

// --- Helpers ---
const set = <T, K extends keyof T>(obj: T, key: K, v: T[K]): T => ({ ...obj, [key]: v });

// Percent helpers: UI shows %, state keeps decimals
const toPct = (dec: number) => (isNaN(dec) ? 0 : Math.round(dec * 1000) / 10); // 1 dp
const toDec = (pct: number) => (isNaN(pct) ? 0 : Math.max(0, Math.min(100, pct)) / 100);

export default function SegmentDiscountCard({ value, onChange, onCopyToAll }: Props) {
  const { business_label, baseline, boost_if_high_gap, max_perk_cost, perk_priority } = value;

  const updateBaselinePct = (k: keyof typeof baseline, pctVal: number) => {
    onChange({
      ...value,
      baseline: { ...baseline, [k]: toDec(pctVal) },
    });
  };

  const updateBoostPct = (pctVal: number) =>
    onChange(set(value, "boost_if_high_gap", toDec(pctVal)));

  const updateMaxPerkCost = (v: number) =>
    onChange(set(value, "max_perk_cost", isNaN(v) ? 0 : Math.max(0, v)));

  // --- Perk priority UI ---
  const isSelected = (perk: PerkKey) => perk_priority.includes(perk);

  const togglePerk = (perk: PerkKey) => {
    const selected = [...perk_priority];
    const idx = selected.indexOf(perk);
    if (idx >= 0) selected.splice(idx, 1);
    else selected.push(perk);
    onChange(set(value, "perk_priority", selected));
  };

  const movePerk = (perk: PerkKey, dir: "up" | "down") => {
    const selected = [...perk_priority];
    const idx = selected.indexOf(perk);
    if (idx === -1) return;
    const swapWith = dir === "up" ? idx - 1 : idx + 1;
    if (swapWith < 0 || swapWith >= selected.length) return;
    [selected[idx], selected[swapWith]] = [selected[swapWith], selected[idx]];
    onChange(set(value, "perk_priority", selected));
  };

  const PerkChip: React.FC<{ perk: PerkKey }> = ({ perk }) => {
    const selected = isSelected(perk);
    const order = selected ? perk_priority.indexOf(perk) + 1 : undefined;

    return (
      <button
        type="button"
        onClick={() => togglePerk(perk)}
        className={[
          "group relative select-none rounded-full border px-3 py-1.5 text-sm transition",
          selected
            ? "border-blue-500 bg-blue-50 hover:bg-blue-100"
            : "border-gray-300 hover:border-gray-400",
        ].join(" ")}
        title={selected ? `Selected • Priority ${order}` : "Click to select"}
      >
        {selected && (
          <span className="absolute -top-2 -right-2 inline-flex h-6 min-w-6 items-center justify-center rounded-full bg-blue-500 px-1 text-xs font-semibold text-white">
            {order}
          </span>
        )}
        <span className="whitespace-nowrap">{PERK_LABELS[perk]}</span>
        {selected && (
          <span className="ml-2 hidden items-center gap-1 align-middle text-gray-600 group-hover:inline-flex">
            <button
              type="button"
              aria-label="Move up"
              className="rounded px-1 hover:bg-blue-100"
              onClick={(e) => {
                e.stopPropagation();
                movePerk(perk, "up");
              }}
            >
              ↑
            </button>
            <button
              type="button"
              aria-label="Move down"
              className="rounded px-1 hover:bg-blue-100"
              onClick={(e) => {
                e.stopPropagation();
                movePerk(perk, "down");
              }}
            >
              ↓
            </button>
          </span>
        )}
      </button>
    );
  };

  return (
    <div className="border rounded-xl p-4 shadow-sm bg-white">
      <div className="flex items-center justify-between mb-3">
        <p className="text-lg font-semibold text-gray-800">{business_label}</p>
        {onCopyToAll && (
          <button
            type="button"
            onClick={onCopyToAll}
            className="text-xs px-2 py-1 rounded border border-gray-300 hover:bg-gray-50"
            title="Copy this configuration to all segments"
          >
            Copy to All
          </button>
        )}
      </div>

      {/* Baseline row (inputs in %) */}
      <div className="grid grid-cols-3 gap-3 mb-4">
        {(["low", "shoulder", "high"] as const).map((season) => (
          <div key={season}>
            <label className="block text-xs text-gray-600 mb-1">
              {season === "low" ? "Low Season (%)" : season === "shoulder" ? "Shoulder Season (%)" : "High Season (%)"}
            </label>
            <div className="relative">
              <input
                type="number"
                step="0.1"
                min={0}
                max={100}
                value={toPct(baseline[season])}
                onChange={(e) => updateBaselinePct(season, parseFloat(e.target.value))}
                className="w-full rounded border px-2 py-2 pr-8 text-sm"
              />
              <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500">%</span>
            </div>
          </div>
        ))}
      </div>

      {/* Boost & Cap (boost in %) */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div>
          <label className="block text-xs text-gray-600 mb-1">Boost if High Gap (%)</label>
          <div className="relative">
            <input
              type="number"
              step="0.1"
              min={0}
              max={100}
              value={toPct(boost_if_high_gap)}
              onChange={(e) => updateBoostPct(parseFloat(e.target.value))}
              className="w-full rounded border px-2 py-2 pr-8 text-sm"
            />
            <span className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500">%</span>
          </div>
        </div>
        <div>
          <label className="block text-xs text-gray-600 mb-1">Max Perk Cost (£)</label>
          <input
            type="number"
            min={0}
            value={max_perk_cost}
            onChange={(e) => updateMaxPerkCost(parseFloat(e.target.value))}
            className="w-full rounded border px-2 py-2 text-sm"
          />
        </div>
      </div>

      {/* Perk Priority */}
      <div>
        <label className="block text-xs text-gray-600 mb-2">Perk Priority</label>
        <div className="flex flex-wrap gap-2">
          {perk_priority.map((perk) => (
            <PerkChip key={perk} perk={perk} />
          ))}
          {ALL_PERKS.filter((p) => !perk_priority.includes(p)).map((perk) => (
            <PerkChip key={perk} perk={perk} />
          ))}
        </div>
        <p className="text-[11px] text-gray-500 mt-2">
          Click a perk to select/deselect. Use ↑/↓ on selected perks (hover) to adjust priority.
        </p>
      </div>
    </div>
  );
}
