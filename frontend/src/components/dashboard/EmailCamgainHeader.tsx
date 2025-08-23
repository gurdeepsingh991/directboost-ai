// EmailCampaignHeader.tsx
import { useState } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";

type Props = {
  mode: "Generate" | "Summary";
  setMode: (m: "Generate" | "Summary") => void;
  year: number;
  setYear: (y: number) => void;
  months: number[];                              // MULTI
  setMonths: (ms: number[]) => void;            // MULTI
  availableYears: number[];
  monthLabels: Record<string, string>;
  disabledMonths?: number[];
};

export default function EmailCampaignHeader({
  mode, setMode,
  year, setYear,
  months, setMonths,
  availableYears,
  monthLabels,
  disabledMonths = [],
}: Props) {
  const [show, setShow] = useState(true);

  const allMonths = Array.from({ length: 12 }, (_, i) => i + 1);

  const toggleMonth = (m: number, disabled: boolean) => {
    if (disabled) return;
    if (months.includes(m)) {
      setMonths(months.filter((x) => x !== m));
    } else {
      setMonths([...months, m]);
    }
  };

  const clearMonths = () => setMonths([]);

  return (
    <div className="w-full mb-6">
      {/* Top bar */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex rounded-lg border bg-gray-100 p-1">
          {(["Generate", "Summary"] as const).map((opt) => (
            <button
              key={opt}
              onClick={() => setMode(opt)}
              className={`px-4 py-1.5 rounded-md text-sm font-medium transition ${
                mode === opt ? "bg-blue-600 text-white" : "text-gray-700 hover:bg-gray-200"
              }`}
            >
              {opt}
            </button>
          ))}
        </div>

        <button
          onClick={() => setShow(!show)}
          className="flex items-center text-sm text-gray-600 hover:text-gray-800"
        >
          Filters {show ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
        </button>
      </div>

      {/* Filters */}
      {show && (
        <div className="mt-4 border rounded-lg p-4 bg-white shadow-sm">
          <div className="flex flex-wrap items-center gap-4">
            {/* Year */}
            <label className="text-sm text-gray-700">
              <span className="mr-2">Year</span>
              <select
                className="border rounded px-3 py-1.5 text-sm"
                value={year}
                onChange={(e) => {
                  setYear(Number(e.target.value));
                  // keep selected months; or clear if you prefer:
                  setMonths([]);
                }}
              >
                {availableYears.map((y) => (
                  <option key={y} value={y}>
                    {y}
                  </option>
                ))}
              </select>
            </label>

            {/* Months (multi) */}
            <div className="flex flex-wrap gap-2">
              {allMonths.map((m) => {
                const label = monthLabels[String(m)] ?? `M${m}`;
                const disabled = disabledMonths.includes(m);
                const active = months.includes(m);

                return (
                  <button
                    key={m}
                    type="button"
                    disabled={disabled}
                    onClick={() => toggleMonth(m, disabled)}
                    className={`px-2.5 py-1 rounded-md text-sm border transition ${
                      disabled
                        ? "bg-gray-100 text-gray-300 cursor-not-allowed"
                        : active
                        ? "bg-blue-600 text-white border-blue-600"
                        : "bg-gray-50 text-gray-700 hover:bg-gray-100"
                    }`}
                    title={disabled ? "No offers" : label}
                  >
                    {label.slice(0, 3)}
                  </button>
                );
              })}
              <button
                onClick={clearMonths}
                className="ml-2 text-xs text-gray-500 hover:text-gray-700 underline"
              >
                Clear months
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
