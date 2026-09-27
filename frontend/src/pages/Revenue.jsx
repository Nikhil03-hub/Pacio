import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useAuth } from "../App";
import { toast } from "sonner";
import { DollarSign, TrendingUp, Award, CreditCard, FileText, Plus, X } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const emptyForm = { amount_inr: "", period: "", type: "platform_share" };

export default function Revenue() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);

  const load = () => {
    api.get("/revenue/me")
      .then(({ data }) => setData(data))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const handleCreateEntry = async (e) => {
    e.preventDefault();
    if (!form.amount_inr || !form.period) {
      toast.error("Amount and period are required");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/revenue/share", {
        institution_id: user?.institution_id || "inst_kmit",
        amount_inr: Number(form.amount_inr),
        period: form.period,
        type: form.type
      });
      toast.success("Revenue record created");
      setForm(emptyForm);
      setOpen(false);
      load();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Failed to create revenue record");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) return <div className="font-mono text-xs text-ink-400 p-8">LOADING…</div>;

  const records = data?.records || [];
  const terms = data?.mou_terms || {};
  const totalAccrued = data?.total_accrued_inr || 0;
  const expected = data?.expected_inr || 0;
  const revenueScore = data?.revenue_score || 0;
  const payoutStatus = data?.payout_status || "—";

  const formatINR = (val) => `₹${(val / 100000).toFixed(2)}L`;

  // Build cumulative chart data
  const chronological = [...records].reverse();
  let totalCumulative = 0;
  const chartData = chronological.map(r => {
    totalCumulative += r.amount_inr || 0;
    return {
      period: r.period,
      amount: r.amount_inr,
      accrued: totalCumulative / 100000, // Show in Lakhs for chart scaling
    };
  });

  const isAdmin = user?.role === "super_admin" || user?.role === "institution_admin";

  return (
    <div className="space-y-10">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-6">
        <div>
          <div className="font-mono text-[10px] tracking-[0.28em] text-ink-400">§ REVENUE</div>
          <h1 className="font-display text-5xl md:text-6xl tracking-tightest mt-3" data-testid="revenue-heading">
            Partnership <span className="text-accent">Revenue</span>
          </h1>
          <p className="font-serif text-lg text-ink-500 mt-2 max-w-xl">Revenue share tracking and payout schedules across partnership terms.</p>
        </div>
        {isAdmin && (
          <button 
            onClick={() => setOpen((prev) => !prev)}
            className="btn"
          >
            {open ? <X size={14} /> : <Plus size={14} />} {open ? "Close" : "Log Transaction"}
          </button>
        )}
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-12 gap-3" data-testid="revenue-kpi">
        {[
          { label: "TOTAL ACCRUED", value: formatINR(totalAccrued), accent: true, icon: DollarSign },
          { label: "EXPECTED REVENUE", value: formatINR(expected), accent: false, icon: TrendingUp },
          { label: "PARTNERSHIP SCORE", value: revenueScore, accent: false, icon: Award },
          { label: "PAYOUT STATUS", value: payoutStatus, accent: false, icon: CreditCard },
        ].map((card) => (
          <div key={card.label} className="col-span-12 md:col-span-3 editorial p-6">
            <div className="flex items-start justify-between">
              <div>
                <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">{card.label}</div>
                <div className={`font-display text-4xl tracking-tightest mt-3 tnum ${card.accent ? "text-accent" : ""}`}>
                  {card.value}
                </div>
              </div>
              <card.icon size={20} className="text-ink-300" />
            </div>
          </div>
        ))}
      </div>

      {/* Add Entry Form Modal */}
      {open && (
        <form onSubmit={handleCreateEntry} className="editorial p-6 grid grid-cols-12 gap-3" data-testid="revenue-form">
          <div className="col-span-12">
            <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 mb-3">LOG PARTNERSHIP TRANSACTION</div>
          </div>
          <input
            type="number"
            value={form.amount_inr}
            onChange={(e) => setForm({ ...form, amount_inr: e.target.value })}
            placeholder="Amount in INR"
            required
            className="col-span-12 md:col-span-4 px-3 py-2.5 border border-line bg-bone-50 focus:outline-none focus:border-accent text-sm"
          />
          <input
            type="text"
            value={form.period}
            onChange={(e) => setForm({ ...form, period: e.target.value })}
            placeholder="Period (e.g. Q3 2026)"
            required
            className="col-span-12 md:col-span-4 px-3 py-2.5 border border-line bg-bone-50 focus:outline-none focus:border-accent text-sm"
          />
          <select
            value={form.type}
            onChange={(e) => setForm({ ...form, type: e.target.value })}
            className="col-span-12 md:col-span-2 px-3 py-2.5 border border-line bg-bone-50 text-sm focus:outline-none"
          >
            <option value="platform_share">Platform Share</option>
            <option value="direct_payment">Direct Payment</option>
            <option value="bonus">Bonus Share</option>
          </select>
          <button 
            type="submit" 
            disabled={submitting} 
            className="col-span-12 md:col-span-2 btn justify-center"
          >
            {submitting ? "Saving…" : "Save Record"}
          </button>
        </form>
      )}

      {/* Revenue growth chart */}
      {records.length > 0 && (
        <div className="border border-line bg-bone-50 p-6 space-y-6">
          <div>
            <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">FINANCIAL ACCRUAL TIMELINE</div>
            <h3 className="font-display text-2xl tracking-tight mt-1">Cumulative Accrued Revenue Growth</h3>
          </div>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={chartData}>
                <defs>
                  <linearGradient id="colorAccrued" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#c1440e" stopOpacity={0.2}/>
                    <stop offset="95%" stopColor="#c1440e" stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <XAxis dataKey="period" stroke="#0a0a0a" fontSize={10} tickLine={false} />
                <YAxis stroke="#0a0a0a" fontSize={10} tickLine={false} tickFormatter={(v) => `₹${v}L`} />
                <Tooltip 
                  contentStyle={{ background: "#F4F0E8", border: "1px solid #0a0a0a" }} 
                  formatter={(val) => [`₹${Number(val).toFixed(2)} Lakhs`, "Cumulative Accrued"]}
                />
                <Area type="monotone" dataKey="accrued" stroke="#c1440e" strokeWidth={2} fillOpacity={1} fill="url(#colorAccrued)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="grid grid-cols-12 gap-3">
        {/* Revenue records table */}
        <div className="col-span-12 lg:col-span-8 border border-line bg-bone-50" data-testid="revenue-table">
          <div className="p-6 border-b border-line">
            <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">REVENUE RECORDS / {records.length}</div>
            <h3 className="font-display text-2xl tracking-tight mt-1">Transaction history</h3>
          </div>
          <div className="grid grid-cols-12 px-6 py-3 border-b border-line font-mono text-[10px] tracking-[0.2em] text-ink-400">
            <div className="col-span-3">PERIOD</div>
            <div className="col-span-3">AMOUNT</div>
            <div className="col-span-3">TYPE</div>
            <div className="col-span-3 text-right">DATE</div>
          </div>
          <div className="max-h-[420px] overflow-y-auto divide-y divide-line">
            {records.map((r, i) => (
              <div key={r.record_id || i} className="grid grid-cols-12 px-6 py-3 items-center text-sm hover:bg-bone-100 transition-colors" data-testid={`revenue-row-${i}`}>
                <div className="col-span-3 font-medium">{r.period || "—"}</div>
                <div className="col-span-3 font-display text-xl text-accent tnum">{formatINR(r.amount_inr || 0)}</div>
                <div className="col-span-3">
                  <span className="font-mono text-[10px] tracking-[0.2em] px-2 py-0.5 border border-line">
                    {(r.type || "—").toUpperCase()}
                  </span>
                </div>
                <div className="col-span-3 text-right font-mono text-xs">{r.date?.slice(0, 10) || "—"}</div>
              </div>
            ))}
            {records.length === 0 && <div className="p-12 text-center text-ink-400">No revenue records found.</div>}
          </div>
        </div>

        {/* MOU revenue terms */}
        <div className="col-span-12 lg:col-span-4 editorial bg-ink-900 text-bone-100 p-8" data-testid="revenue-terms">
          <div className="flex items-center gap-3">
            <FileText size={20} className="text-accent" />
            <div className="font-mono text-[10px] tracking-[0.24em] text-bone-100/60">MOU REVENUE TERMS</div>
          </div>
          <div className="hairline my-6 border-bone-100/30" />
          <div className="space-y-5">
            {[
              { label: "PARTNERSHIP TYPE", value: terms.partnership_type || "—" },
              { label: "REVENUE SHARE %", value: terms.share_percentage != null ? `${terms.share_percentage}%` : "—" },
              { label: "BILLING CYCLE", value: terms.billing_cycle || "—" },
              { label: "CONTRACT PERIOD", value: terms.contract_period || "—" },
              { label: "MIN GUARANTEE", value: terms.min_guarantee_inr ? formatINR(terms.min_guarantee_inr) : "—" },
            ].map((item) => (
              <div key={item.label}>
                <div className="font-mono text-[10px] tracking-[0.24em] text-bone-100/60">{item.label}</div>
                <div className="font-display text-xl mt-1">{item.value}</div>
              </div>
            ))}
          </div>
          <div className="hairline my-6 border-bone-100/30" />
          <div className="font-serif text-sm text-bone-100/70">
            Revenue terms are governed by the active MOU. Contact your partnership manager for amendments.
          </div>
        </div>
      </div>
    </div>
  );
}
