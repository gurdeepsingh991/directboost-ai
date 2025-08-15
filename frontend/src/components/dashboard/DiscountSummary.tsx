import { useEffect, useState } from "react";
import apiUtils from "../../utils/apiUtils";

interface DiscountSummaryProps {
  email: string;
}

export default function DiscountSummary({ email }: DiscountSummaryProps) {
  const { getDiscountSummary } = apiUtils();
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [expandedRooms, setExpandedRooms] = useState<Record<string, boolean>>({});
  const [selectedMonthYear, setSelectedMonthYear] = useState<Record<string, string>>({});

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const data = await getDiscountSummary(email);
        setSummary(data);
      } catch (err) {
        console.error("Failed to fetch discount summary", err);
      } finally {
        setLoading(false);
      }
    };
    fetchSummary();
  }, [email]);

  const toggleRoom = (key: string) => {
    setExpandedRooms((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  const handleMonthChange = (key: string, value: string) => {
    setSelectedMonthYear((prev) => ({ ...prev, [key]: value }));
  };

  if (loading) {
    return <div className="text-center py-10">Fetching discount summary...</div>;
  }

  if (!summary?.success) {
    return <div className="text-center py-10 text-red-500">No summary found.</div>;
  }

  const overall = summary.overall || {};

  return (
    <div className="w-full max-w-6xl mt-6">
      <h2 className="text-xl font-semibold mb-4">Discount Summary</h2>

      {/* Overall stats */}
      <div className="bg-white shadow rounded-lg p-4 mb-6 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
        <Stat label="Total Offers" value={overall.total_offers} />
        <Stat label="Avg Discount %" value={`${overall.avg_discount_pct?.toFixed(2)}%`} />
        <Stat label="Avg Base ADR" value={overall.avg_base_adr ? `€${overall.avg_base_adr.toFixed(2)}` : "-"} />
        <Stat label="Avg Post-Discount ADR" value={overall.avg_post_discount_adr ? `€${overall.avg_post_discount_adr.toFixed(2)}` : "-"} />
      </div>

      {/* Segment-level summary */}
      <div className="space-y-6">
        {summary.segments?.map((seg: any) => (
          <div key={seg.segment_id} className="bg-gray-50 p-4 rounded-lg border">
            <h3 className="font-semibold text-lg">{seg.business_label}</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-2 text-sm">
              <Stat label="Offers" value={seg.offers_count} />
              <Stat label="Avg Discount" value={`${seg.avg_discount_pct?.toFixed(2)}%`} />
              <Stat label="Avg Base ADR" value={seg.avg_base_adr ? `€${seg.avg_base_adr.toFixed(2)}` : "-"} />
              <Stat label="Avg Post-Discount ADR" value={seg.avg_post_discount_adr ? `€${seg.avg_post_discount_adr.toFixed(2)}` : "-"} />
            </div>
            {seg.most_common_perks?.length > 0 && (
              <p className="mt-1 text-xs text-gray-500">
                Common Perks: {seg.most_common_perks.join(", ")}
              </p>
            )}

            {/* Room-level summary */}
            <div className="ml-2 mt-4 space-y-3">
              {seg.rooms?.map((room: any) => {
                const roomKey = `${seg.segment_id}-${room.room_type}`;
                const monthOptions = ["All", ...room.months.map((m: any) => `${m.month} ${m.year}`)];
                const selected = selectedMonthYear[roomKey] || "All";

                // Filtered months for display
                const monthsToShow =
                  selected === "All"
                    ? room.months
                    : room.months.filter((m: any) => `${m.month} ${m.year}` === selected);

                return (
                  <div key={room.room_type} className="bg-white p-3 rounded border shadow-sm">
                    <div className="flex justify-between items-center">
                      <div>
                        <p className="font-medium">Room {room.room_type}</p>
                        <p className="text-xs text-gray-500">
                          Offers: {room.offers_count}, Avg Discount: {room.avg_discount_pct?.toFixed(2)}%
                        </p>
                      </div>
                      <button
                        onClick={() => toggleRoom(roomKey)}
                        className="text-sm text-blue-500 hover:underline"
                      >
                        {expandedRooms[roomKey] ? "Hide" : "Show"} Monthly
                      </button>
                    </div>

                    {expandedRooms[roomKey] && (
                      <div className="mt-3">
                        {/* Month Selector */}
                        <select
                          value={selected}
                          onChange={(e) => handleMonthChange(roomKey, e.target.value)}
                          className="border px-2 py-1 rounded text-sm mb-3"
                        >
                          {monthOptions.map((opt) => (
                            <option key={opt} value={opt}>
                              {opt}
                            </option>
                          ))}
                        </select>

                        {/* Monthly breakdown table */}
                        <table className="w-full text-xs border">
                          <thead>
                            <tr className="bg-gray-100 text-left">
                              <th className="p-2">Month</th>
                              <th className="p-2">Year</th>
                              <th className="p-2">Offers</th>
                              <th className="p-2">Avg Discount</th>
                              <th className="p-2">Base ADR</th>
                              <th className="p-2">Post-Discount ADR</th>
                            </tr>
                          </thead>
                          <tbody>
                            {monthsToShow.map((m: any, idx: number) => (
                              <tr key={idx} className="border-t">
                                <td className="p-2">{m.month}</td>
                                <td className="p-2">{m.year}</td>
                                <td className="p-2">{m.offers_count}</td>
                                <td className="p-2">{m.avg_discount_pct?.toFixed(2)}%</td>
                                <td className="p-2">{m.avg_base_adr ? `€${m.avg_base_adr.toFixed(2)}` : "-"}</td>
                                <td className="p-2">{m.avg_post_discount_adr ? `€${m.avg_post_discount_adr.toFixed(2)}` : "-"}</td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: any }) {
  return (
    <div className="bg-gray-50 p-3 rounded text-center border">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="font-medium">{value}</p>
    </div>
  );
}
