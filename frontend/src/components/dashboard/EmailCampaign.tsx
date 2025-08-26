import { useEffect, useMemo, useState } from "react";
import Button from "../shared/Button";
import EmailCampaignHeader from "./EmailCamgainHeader";
import apiUtils from "../../utils/apiUtils";
import { usePersistentState } from "../../hooks/usePersistanceStorage";
import { ChevronDown, ChevronRight } from "lucide-react";

type MonthCounts = { total: number; generated: number; pending: number };

type CampaignStatsResponse = {
  years: Record<string, Record<string, MonthCounts>>;
  month_labels: Record<string, string>;
  campaigns: Record<string, Record<string, any[]>>;
};

export default function EmailCampaign({
  step,
  setStep,
}: {
  step: number;
  setStep: (n: number) => void;
}) {
  const [email] = usePersistentState<string>("email", "");

  const [mode, setMode] = useState<"Generate" | "Summary">("Generate");
  const [summary, setSummary] = useState<CampaignStatsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [previewHtml, setPreviewHtml] = useState<string | null>(null);

  // NEW: spinner while generating emails
  const [isGenerating, setIsGenerating] = useState(false);

  const { getEmailCampaign, generateEmailsAPI, getEmailPreview } = apiUtils();

  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState<number>(currentYear);
  const [months, setMonths] = useState<number[]>([]);

  // Track which months are expanded
  const [openMonths, setOpenMonths] = useState<Record<string, boolean>>({});

  // Initialize open months whenever year/summary changes
  useEffect(() => {
    if (!summary) return;
    const ym = summary.years?.[String(year)] || {};
    const next: Record<string, boolean> = {};
    Object.keys(ym).forEach((m) => {
      const counts = ym[m];
      next[m] = (counts?.total || 0) > 0;
    });
    setOpenMonths(next);
  }, [summary, year]);

  const counts = useMemo(() => {
    if (!summary) return { total: 0, generated: 0, pending: 0 };
    const ym = summary.years?.[String(year)];
    if (!ym) return { total: 0, generated: 0, pending: 0 };

    const monthsToUse = months.length > 0 ? months : Array.from({ length: 12 }, (_, i) => i + 1);

    return monthsToUse.reduce(
      (acc, mNum) => {
        const m = ym[String(mNum)];
        if (!m) return acc;
        acc.total += m.total || 0;
        acc.generated += m.generated || 0;
        acc.pending += m.pending || 0;
        return acc;
      },
      { total: 0, generated: 0, pending: 0 }
    );
  }, [summary, year, months]);

  const availableYears = useMemo(() => {
    if (!summary) return [];
    return Object.keys(summary.years).map(Number).sort((a, b) => a - b);
  }, [summary]);

  const disabledMonths = useMemo(() => {
    if (!summary) return [];
    const ym = summary.years[String(year)];
    if (!ym) return [];
    const disabled: number[] = [];
    for (let m = 1; m <= 12; m++) {
      const entry = ym[String(m)];
      if (!entry || entry.total === 0) disabled.push(m);
    }
    return disabled;
  }, [summary, year]);

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const data = await getEmailCampaign(email);
        setSummary(data);
        const years = Object.keys(data.years).map(Number).sort((a, b) => a - b);
        if (years.length && !years.includes(year)) setYear(years[0]);
      } catch (e) {
        console.error("Failed to load campaign summary", e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  async function handleGenerate() {
    try {
      setIsGenerating(true); // NEW: start spinner
      const data = await generateEmailsAPI(email, months, year);
      setSummary(data);
      setMode("Summary");
    } catch (e) {
      console.error(e);
    } finally {
      setIsGenerating(false); // NEW: stop spinner
    }
  }

  const monthLabels = summary?.month_labels || {
    "1": "January", "2": "February", "3": "March", "4": "April", "5": "May", "6": "June",
    "7": "July", "8": "August", "9": "September", "10": "October", "11": "November", "12": "December",
  };

  async function handlePreview(campaignId: string) {
    try {
      const result = await getEmailPreview(campaignId);
      if (result.success) setPreviewHtml(result.html);
      else console.error("Preview error:", result.message);
    } catch (e) {
      console.error("Preview failed:", e);
    }
  }

  const selectedLabel =
    months.length > 0
      ? months.map((m) => monthLabels[String(m)].slice(0, 3)).join(", ")
      : "All months";

  const toggleMonth = (m: string) =>
    setOpenMonths((prev) => ({ ...prev, [m]: !prev[m] }));

  return (
    <div className="flex overflow-y-auto flex-col items-center pt-32 pb-24 px-4">
      {/* Title */}
      <div className="relative w-full max-w-6xl mb-2 flex items-end">
        <div className="mx-auto text-center">
          <h1 className="text-[22px] font-semibold tracking-tight text-gray-900">
            {mode === "Summary" ? "Email Summary" : "Email Campaign"}
          </h1>
          <p className="text-gray-600 text-xs mt-1">
            {mode === "Summary"
              ? "Review generated campaigns and counts."
              : "Pick year and months, then generate missing campaigns."}
          </p>
        </div>
      </div>

      {/* Header */}
      <div className="w-full max-w-6xl">
        <EmailCampaignHeader
          mode={mode}
          setMode={setMode}
          year={year}
          setYear={setYear}
          months={months}
          setMonths={setMonths}
          availableYears={availableYears}
          monthLabels={monthLabels}
          disabledMonths={disabledMonths}
        />
      </div>

      {/* Generate */}
      {mode === "Generate" && (
        <div className="w-full max-w-6xl">
          <div className="p-5 border rounded-xl bg-white shadow-sm">
            {loading ? (
              <p className="text-sm text-gray-600">Loading…</p>
            ) : (
              <>
                <p className="text-sm text-gray-700 mb-3">
                  {selectedLabel} <b>{year}</b>:{" "}
                  <b>{counts.total}</b> offers •{" "}
                  <span className="text-green-700"><b>{counts.generated}</b> generated</span> •{" "}
                  <span className="text-amber-700"><b>{counts.pending}</b> pending</span>
                </p>

                <div className="flex gap-2">
                  <Button
                    type="normal"
                    label={
                      isGenerating
                        ? "Generating…"
                        : counts.pending > 0
                          ? `Generate ${counts.pending} Pending`
                          : "Nothing to Generate"
                    }
                    onClick={handleGenerate}
                    disabled={loading || isGenerating || counts.pending === 0}
                    aria-busy={isGenerating}
                  />
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Summary */}
      {mode === "Summary" && (
        <div className="w-full max-w-6xl">
          {loading || !summary ? (
            <div className="text-sm text-gray-600">Loading…</div>
          ) : (
            <div className="space-y-4">
              {Object.entries(summary?.campaigns[String(year)] || {})
                .filter(([m]) => months.length === 0 || months.includes(Number(m)))
                .map(([m, cards]) => {
                  const counts = summary.years[String(year)]?.[m] || { total: 0, generated: 0, pending: 0 };
                  const isOpen = !!openMonths[m];
                  return (
                    <MonthSection
                      key={m}
                      monthKey={m}
                      title={`${summary.month_labels[m]} ${year}`}
                      counts={counts}
                      isOpen={isOpen}
                      onToggle={() => toggleMonth(m)}
                      cards={cards as any[]}
                      onPreview={handlePreview}
                      onGoGenerate={() => setMode("Generate")}
                    />
                  );
                })}
            </div>
          )}
        </div>
      )}

      {previewHtml && (
        <EmailPreviewModal html={previewHtml} onClose={() => setPreviewHtml(null)} />
      )}

      {/* NEW: simple overlay spinner while generating */}
      {isGenerating && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-white/60 backdrop-blur-sm">
          <div className="flex items-center gap-3 rounded-xl border bg-white px-4 py-3 shadow">
            <svg className="h-5 w-5 animate-spin" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
            </svg>
            <span className="text-sm text-gray-700">Generating campaigns…</span>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="fixed inset-x-0 bottom-0 z-40 border-t border-gray-200 bg-white/90 py-3">
        <div className="max-w-6xl mx-auto px-4 flex items-center justify-between">
          <div className="flex flex-col">
            <span className="text-sm font-medium text-gray-800">
              Step 5: Email Campaign — {mode}
            </span>
            <span className="text-xs text-gray-500">
              {year} • {selectedLabel}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Button type="normal" label="Back" onClick={() => setStep(step - 1)} disabled={isGenerating} />
            <Button type="normal" label="Next" onClick={() => setStep(step + 1)} disabled={isGenerating} />
          </div>
        </div>
      </div>
    </div>
  );
}

function MonthSection({
  monthKey,
  title,
  counts,
  isOpen,
  onToggle,
  cards,
  onPreview,
  onGoGenerate,
}: {
  monthKey: string;
  title: string;
  counts: MonthCounts;
  isOpen: boolean;
  onToggle: () => void;
  cards: any[];
  onPreview: (id: string) => void;
  onGoGenerate: () => void;
}) {
  const hasOffers = (counts?.total || 0) > 0;
  return (
    <div className="border rounded-lg bg-white shadow-sm">
      <button
        type="button"
        onClick={onToggle}
        className="w-full px-4 py-2 border-b flex items-center justify-between hover:bg-gray-50"
        aria-expanded={isOpen}
        aria-controls={`month-${monthKey}`}
      >
        <div className="flex items-center gap-2">
          {isOpen ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
          <div className="font-medium">{title}</div>
        </div>
        <div className="text-xs text-gray-500">
          Total {counts.total} •
          <span className="text-green-700 ml-1">Generated {counts.generated}</span> •
          <span className="text-amber-700 ml-1">Pending {counts.pending}</span>
        </div>
      </button>

      {isOpen && (
        <div id={`month-${monthKey}`} className="p-4">
          {!hasOffers ? (
            <div className="rounded-md border border-dashed p-4 bg-gray-50 text-sm text-gray-600 flex items-center justify-between">
              <span>No offers this month.</span>
              <Button type="normal" label="Generate Offers" onClick={onGoGenerate} />
            </div>
          ) : cards.length === 0 || !cards[0].subject ? (
            <div className="rounded-md border border-dashed p-4 bg-gray-50 text-sm text-gray-600">
              No campaigns found for this month yet.
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-3">
              {cards.map((c) => (
                <div key={c.offer_id} className="p-3 border rounded-lg bg-gray-50 flex flex-col gap-2">
                  <div className="text-sm font-semibold">{c.subject || "No Subject Yet"}</div>
                  <div className="text-xs text-gray-500">
                    {c.hotel} • {c.business_label} • {c.discount_pct || 0}% off
                  </div>
                  <div className="flex gap-2 mt-2">
                    {c.campaign_id ? (
                      <Button type="normal" label="Preview" onClick={() => onPreview(c.campaign_id)} />
                    ) : (
                      <span className="text-xs text-gray-400">Not generated yet</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function EmailPreviewModal({ html, onClose }: { html: string; onClose: () => void }) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-lg shadow-lg relative">
        <button
          onClick={onClose}
          className="absolute top-2 right-2 text-gray-500 hover:text-gray-700"
          aria-label="Close preview"
        >
          ✕
        </button>
        <iframe srcDoc={html} className="w-full h-[80vh] border-0 rounded-b-lg" title="Email Preview" />
      </div>
    </div>
  );
}
