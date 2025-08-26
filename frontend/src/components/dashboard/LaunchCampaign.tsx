import { useEffect, useMemo, useState } from "react";
import Button from "../shared/Button";
import apiUtils from "../../utils/apiUtils";
import { usePersistentState } from "../../hooks/usePersistanceStorage";
import clsx from "clsx";

type MonthCounts = { total: number; generated: number; pending: number };
type CampaignStatsResponse = {
    years: Record<string, Record<string, MonthCounts>>;
    month_labels: Record<string, string>;
    campaigns: Record<string, Record<string, any[]>>;
};
type ScheduleMode = "now" | "later" | "smart";

function Spinner({ label = "Loading…" }: { label?: string }) {
    return (
        <div className="flex items-center gap-2 text-sm text-gray-600">
            <div className="h-4 w-4 border-2 border-gray-300 border-t-gray-600 rounded-full animate-spin" />
            {label}
        </div>
    );
}

function EmailPreviewModal({ html, onClose }: { html: string; onClose: () => void }) {
    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
            <div className="bg-white w-full max-w-4xl max-h-[90vh] overflow-y-auto rounded-lg shadow-lg relative">
                <button onClick={onClose} className="absolute top-2 right-2 text-gray-500 hover:text-gray-700" aria-label="Close preview">✕</button>
                <iframe srcDoc={html} className="w-full h-[80vh] border-0 rounded-b-lg" title="Email Preview" />
            </div>
        </div>
    );
}

export default function LaunchCampaign({
    step,
    setStep,
}: {
    step: number;
    setStep: (n: number) => void;
}) {
    const [email] = usePersistentState<string>("email", "");
    const { getEmailCampaign, getEmailPreview, launchEmailCampaign } = apiUtils();

    // ---------- UI State ----------
    const [ui, setUi] = useState<"compose" | "receipt">("compose");
    const [loading, setLoading] = useState(true);
    const [launching, setLaunching] = useState(false);
    const [error, setError] = useState<string | null>(null);

    // Data (from Step 5 API)
    const [summary, setSummary] = useState<CampaignStatsResponse | null>(null);

    // Campaign meta (manager input)
    const [campaignName, setCampaignName] = useState("");
    const [campaignDesc, setCampaignDesc] = useState("");

    // Scope selection
    const [year, setYear] = useState<number | null>(null);
    const [months, setMonths] = useState<number[]>([]);

    // Email selection
    const [selected, setSelected] = useState<Record<string, boolean>>({});
    const [selectAll, setSelectAll] = useState(true);

    // Scheduling + Compliance
    const [scheduleMode, setScheduleMode] = useState<ScheduleMode>("now");
    const [scheduleAt, setScheduleAt] = useState<string>("");
    const [compliance, setCompliance] = useState([
        { id: "gdpr", label: "GDPR: Only opted‑in recipients included", checked: false },
        { id: "unsub", label: "Unsubscribe link present and tested", checked: false },
        { id: "brand", label: "Branding (logo, colors, footer) verified", checked: false },
    ]);

    const FixedActionBar = ({ children }: { children: React.ReactNode }) => (
        <>
            {/* spacer to avoid overlap */}
            <div className="h-24" />
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
                            <span className="text-sm font-medium text-gray-800">
                                Step 6: Launch Campaign
                            </span>
                            <span className="text-xs text-gray-500">
                                Your progress is saved locally. Continue when ready.
                            </span>
                        </div>
                        <div className="flex items-center gap-2 sm:gap-3">{children}</div>
                    </div>
                </div>
            </div>
        </>
    );

    // Preview
    const [previewHtml, setPreviewHtml] = useState<string | null>(null);

    // ---------- Load summary ----------
    useEffect(() => {
        (async () => {
            setLoading(true);
            setError(null);
            try {
                const data = await getEmailCampaign(email);
                setSummary(data);

                // pick most recent year with generated>0
                const years = Object.keys(data.years || {}).map(Number).sort((a, b) => a - b);
                const chosenYear =
                    [...years].reverse().find((y) => {
                        const ym = data.years[String(y)] || {};
                        return Object.values(ym).some((m) => (m?.generated || 0) > 0);
                    }) ?? years[years.length - 1];
                setYear(chosenYear);

                const ym = data.campaigns[String(chosenYear)] || {};
                const defaultMonths = Object.keys(ym)
                    .map(Number)
                    .filter((m) => monthHasValidEmails(data, chosenYear, m));
                setMonths(defaultMonths);


                // preselect emails in chosen scope
                const rows = collectRows(data, chosenYear, defaultMonths);
                const initialSel: Record<string, boolean> = {};
                rows.forEach((r: any) => r?.campaign_id && (initialSel[r.campaign_id] = true));
                setSelected(initialSel);
                setSelectAll(true);
            } catch (e: any) {
                setError("Failed to load campaign emails for launch.");
            } finally {
                setLoading(false);
            }
        })();
    }, [email]);

    // ---------- Helpers ----------
    const monthLabels = useMemo(
        () =>
            summary?.month_labels || {
                "1": "January", "2": "February", "3": "March", "4": "April", "5": "May", "6": "June",
                "7": "July", "8": "August", "9": "September", "10": "October", "11": "November", "12": "December",
            },
        [summary]
    );

    const availableMonths = useMemo(() => {
        if (!summary || !year) return [];
        return Array.from({ length: 12 }, (_, i) => i + 1).map((m) => ({
            month: m,
            valid: monthHasValidEmails(summary, year, m),
        }));
    }, [summary, year]);

    // filter out already launched emails in collectRows
    function collectRows(data: CampaignStatsResponse, y: number | null, ms: number[]) {
        if (!data || !y) return [];
        const ym = data.campaigns[String(y)] || {};
        const rows: any[] = [];

        (ms.length ? ms : Object.keys(ym).map(Number)).forEach((m) => {
            (ym[String(m)] || [])
                // only include valid emails
                .filter((r: any) => r?.subject?.trim().length > 0 && r?.status !== "launched")
                .forEach((r: any) => rows.push({ ...r, _month: m }));
        });
        return rows;
    }

    // adjust month validity check to also exclude launched
    function monthHasValidEmails(data: CampaignStatsResponse, year: number, m: number) {
        const ym = data.campaigns[String(year)] || {};
        const rows = ym[String(m)] || [];
        return rows.some((r: any) => r?.subject?.trim().length > 0 && r?.status !== "launched");
    }

    const rows = useMemo(() => (summary ? collectRows(summary, year, months) : []), [summary, year, months]);
    const selectedIds = useMemo(() => Object.entries(selected).filter(([, v]) => v).map(([k]) => k), [selected]);
    const counts = useMemo(() => ({ total: rows.length, selected: selectedIds.length }), [rows.length, selectedIds.length]);

    const availableYears = useMemo(() => (summary ? Object.keys(summary.years || {}).map(Number).sort((a, b) => a - b) : []), [summary]);


    

    function toggleMonth(m: number) {
        setMonths((curr) => (curr.includes(m) ? curr.filter((x) => x !== m) : [...curr, m].sort((a, b) => a - b)));
    }
    function toggleAll(val: boolean) {
        setSelectAll(val);
        const next: Record<string, boolean> = {};
        rows.forEach((r: any) => r?.campaign_id && (next[r.campaign_id] = val));
        setSelected(next);
    }
    function toggleOne(id: string) {
        setSelected((curr) => ({ ...curr, [id]: !curr[id] }));
    }

    async function handlePreview(id: string) {
        try {
            const res = await getEmailPreview(id);
            if (res.success) setPreviewHtml(res.html);
            else setError(res.message || "Preview failed.");
        } catch {
            setError("Preview failed.");
        }
    }

    function validate() {
        if (!campaignName.trim()) return setError("Please enter a campaign name."), false;
        if (selectedIds.length === 0) return setError("Please select at least one email."), false;
        if (scheduleMode === "later" && !scheduleAt) return setError("Please choose a schedule date & time."), false;
        if (!compliance.every((c) => c.checked)) return setError("Please confirm all compliance checks."), false;
        return true;
    }

    async function handleLaunch() {
        setError(null);
        if (!validate()) return;

        setLaunching(true);
        try {
            const payload = {
                user_email: email,
                campaign: { name: campaignName.trim(), description: campaignDesc.trim() || null },
                scope: { year: year!, months },
                email_campaign_ids: selectedIds,
                schedule: { mode: scheduleMode, schedule_at: scheduleAt || null, timezone: "Europe/London" },
                compliance: Object.fromEntries(compliance.map((c) => [c.id, c.checked])),
            };

            const res = await launchEmailCampaign(payload); // single call
            if (!res?.success) throw new Error(res?.message || "Launch failed.");

            setUi("receipt"); // show success receipt
        } catch (e: any) {
            setError(e?.message || "Launch failed.");
        } finally {
            setLaunching(false);
        }
    }

    // ---------- UI ----------
    if (ui === "receipt") {
        return (
            <div className="max-w-3xl mx-auto pt-40 px-4 py-10 space-y-6">
                <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-green-100 flex items-center justify-center">✓</div>
                    <div>
                        <h1 className="text-xl font-semibold">Campaign scheduled</h1>
                        <p className="text-sm text-gray-600">Your emails have been queued. You can monitor delivery and engagement from your dashboard.</p>
                    </div>
                </div>

                <div className="bg-white border rounded-2xl shadow-sm p-4">
                    <div className="text-sm text-gray-500">Campaign</div>
                    <div className="text-sm">{campaignName || "—"}</div>

                    <div className="mt-3 text-sm text-gray-500">Scope</div>
                    <div className="text-sm">
                        {year} • {months.map((m) => monthLabels[String(m)]).join(", ")}
                    </div>

                    <div className="mt-3 text-sm text-gray-500">Selection</div>
                    <div className="text-sm">{counts.selected} email(s) queued</div>

                    <div className="mt-3 text-sm text-gray-500">Send</div>
                    <div className="text-sm">
                        {scheduleMode === "now" && "Immediately"}
                        {scheduleMode === "later" && (scheduleAt ? new Date(scheduleAt).toLocaleString() : "Scheduled (time not set)")}
                        {scheduleMode === "smart" && "Smart Send (optimised)"} • Europe/London
                    </div>
                </div>

                <div className="flex gap-2">
                    <Button type="normal" label="Go to Dashboard" onClick={() => { if (typeof window !== "undefined") window.location.href = "/dashboard"; }} />
                </div>
            </div>
        );
    }

    // compose view
    return (
        <div className="max-w-6xl mx-auto pt-48 px-4 py-8 space-y-6">
            <div className="flex flex-col items-center">
                <h1 className="text-2xl font-semibold">Launch Campaign</h1>
                <p className="text-sm text-gray-600">Name your campaign, choose scope, review emails, schedule, and launch.</p>
            </div>

            {error && <div className="border border-red-200 bg-red-50 text-red-700 p-3 rounded-xl">{error}</div>}

            {/* Campaign meta */}
            <div className="bg-white border rounded-2xl shadow-sm p-4 space-y-3">
                <div className="font-medium">Campaign details</div>
                <div className="grid sm:grid-cols-2 gap-3">
                    <div className="flex flex-col">
                        <label className="text-sm text-gray-600 mb-1">Campaign name</label>
                        <input className="border rounded-lg px-3 py-2 text-sm" placeholder="e.g., Late Summer Offers" value={campaignName} onChange={(e) => setCampaignName(e.target.value)} />
                    </div>
                    <div className="flex flex-col">
                        <label className="text-sm text-gray-600 mb-1">Description (optional)</label>
                        <input className="border rounded-lg px-3 py-2 text-sm" placeholder="Internal note visible to your team" value={campaignDesc} onChange={(e) => setCampaignDesc(e.target.value)} />
                    </div>
                </div>
            </div>

            {/* Scope */}
            <div className="bg-white border rounded-2xl shadow-sm p-4 space-y-3">
                <div className="font-medium">Scope</div>
                {loading || !summary ? (
                    <Spinner />
                ) : (
                    <>
                        <div className="flex gap-3 flex-wrap items-center">
                            <div className="flex items-center gap-2">
                                <label className="text-sm text-gray-600">Year</label>
                                <select
                                    className="border rounded-lg px-3 py-2 text-sm"
                                    value={year ?? ""}
                                    onChange={(e) => {
                                        const y = Number(e.target.value);
                                        setYear(y);
                                        const ym = summary.years[String(y)] || {};
                                        const nextMonths = Object.entries(ym).filter(([, v]) => (v?.generated || 0) > 0).map(([m]) => Number(m));
                                        setMonths(nextMonths);
                                        const nextRows = collectRows(summary, y, nextMonths);
                                        const nextSel: Record<string, boolean> = {};
                                        nextRows.forEach((r: any) => r?.campaign_id && (nextSel[r.campaign_id] = true));
                                        setSelected(nextSel);
                                        setSelectAll(true);
                                    }}
                                >
                                    {availableYears.map((y) => (<option key={y} value={y}>{y}</option>))}
                                </select>
                            </div>

                            <div className="flex items-center gap-2 flex-wrap">
                                <span className="text-sm text-gray-600">Months</span>
                                {availableMonths.map(({ month: m, valid }) => {
                                    const label = monthLabels[String(m)];
                                    return (
                                        <label
                                            key={m}
                                            className={clsx(
                                                "text-xs px-2 py-1 rounded-full border cursor-pointer",
                                                months.includes(m) ? "bg-blue-50 border-blue-200" : "bg-white border-gray-200",
                                                !valid && "opacity-50 cursor-not-allowed"
                                            )}
                                        >
                                            <input
                                                type="checkbox"
                                                className="mr-1"
                                                disabled={!valid}
                                                checked={months.includes(m)}
                                                onChange={() => toggleMonth(m)}
                                            />
                                            {label}
                                        </label>
                                    );
                                })}
                            </div>
                        </div>
                        <div className="text-xs text-gray-500">Tip: Months with no data are disabled. Defaults to months with generated emails.</div>
                    </>
                )}
            </div>

            {/* Emails list */}
            <div className="bg-white border rounded-2xl shadow-sm">
                <div className="border-b p-4 flex items-center justify-between">
                    <div>
                        <div className="font-medium">Emails to include</div>
                        <div className="text-xs text-gray-500">Defaults to all generated emails in the selected scope.</div>
                    </div>
                    <div className="text-sm">
                        {counts.selected}/{counts.total} selected
                        <button className="ml-3 text-blue-700 underline underline-offset-4" onClick={() => toggleAll(!selectAll)}>
                            {selectAll ? "Deselect all" : "Select all"}
                        </button>
                    </div>
                </div>

                {loading ? (
                    <div className="p-4"><Spinner /></div>
                ) : rows.length === 0 ? (
                    <div className="p-4 text-sm text-gray-600">No generated emails found for this scope.</div>
                ) : (
                    <ul className="divide-y">
                        {rows.map((c: any) => {
                            const id = c?.campaign_id;
                            const checked = !!selected[id];
                            return (
                                <li key={id} className="p-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                                    <label className="flex items-start gap-3">
                                        <input type="checkbox" className="mt-1 h-4 w-4" checked={checked} onChange={() => toggleOne(id)} />
                                        <div>
                                            <div className="text-sm font-medium">
                                                {c?.subject || "No Subject"}{" "}
                                                <span className="text-xs text-gray-500">({monthLabels[String(c._month ?? c.month)]} {year})</span>
                                            </div>
                                            <div className="text-xs text-gray-500">
                                                {c?.hotel || "Hotel"} • {c?.business_label || "Segment"} • {c?.discount_pct ?? 0}% off
                                            </div>
                                        </div>
                                    </label>
                                    <div className="flex items-center gap-2">
                                        {id ? <Button type="normal" label="Preview" onClick={() => handlePreview(id)} /> : <span className="text-xs text-gray-400">Not generated</span>}
                                    </div>
                                </li>
                            );
                        })}
                    </ul>
                )}
            </div>

            {/* Scheduling */}
            <div className="bg-white border rounded-2xl shadow-sm p-4 space-y-3">
                <div className="font-medium">Scheduling</div>
                <div className="flex gap-2 flex-wrap">
                    <button className={clsx("px-3 py-2 rounded-lg border text-sm", scheduleMode === "now" ? "border-blue-500 ring-2 ring-blue-100" : "border-gray-200")} onClick={() => setScheduleMode("now")}>Send Now</button>
                    <button className={clsx("px-3 py-2 rounded-lg border text-sm", scheduleMode === "later" ? "border-blue-500 ring-2 ring-blue-100" : "border-gray-200")} onClick={() => setScheduleMode("later")}>Schedule</button>
                    {/* <button className={clsx("px-3 py-2 rounded-lg border text-sm", scheduleMode === "smart" ? "border-blue-500 ring-2 ring-blue-100" : "border-gray-200")} onClick={() => setScheduleMode("smart")} title="Optimise by historical open rates">Smart Send</button> */}
                </div>
                {scheduleMode === "later" && (
                    <div className="flex items-center gap-3">
                        <label className="text-sm text-gray-600" htmlFor="scheduleAt">Date & time (Europe/London)</label>
                        <input id="scheduleAt" type="datetime-local" className="border rounded-lg px-3 py-2 text-sm" value={scheduleAt} onChange={(e) => setScheduleAt(e.target.value)} />
                    </div>
                )}
                {/* {scheduleMode === "smart" && <div className="text-sm text-gray-600">Will optimise send time based on past engagement.</div>} */}
            </div>

            {/* Compliance */}
            <div className="bg-white border rounded-2xl shadow-sm p-4">
                <div className="font-medium mb-2">Compliance & Safety Checks</div>
                <ul className="space-y-3">
                    {compliance.map((it) => (
                        <li key={it.id} className="flex items-start gap-3">
                            <input id={it.id} type="checkbox" className="mt-1 h-4 w-4" checked={it.checked} onChange={() => setCompliance((cs) => cs.map((c) => (c.id === it.id ? { ...c, checked: !c.checked } : c)))} />
                            <label htmlFor={it.id} className="text-sm text-gray-700">{it.label}</label>
                        </li>
                    ))}
                </ul>
            </div>

            {/* CTA */}
            <FixedActionBar>
                <Button type="normal" label="Back" onClick={() => setStep(step - 1)} />
                <Button
                    type="normal"
                    label={launching ? "Queuing…" : "Launch Campaign"}
                    onClick={handleLaunch}
                    disabled={launching || loading}
                />
            </FixedActionBar>
            {previewHtml && <EmailPreviewModal html={previewHtml} onClose={() => setPreviewHtml(null)} />}
        </div>
    );
}



