import React, { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../App";
import {
  Activity,
  ArrowUpRight,
  Award,
  Bell,
  Briefcase,
  Building2,
  Download,
  MoreHorizontal,
  Search,
  Send,
  Users,
} from "lucide-react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import PlatformSummary from "../components/PlatformSummary";

const fmt = (value) => {
  if (value === null || value === undefined || value === "-") return "-";
  return Number(value).toLocaleString();
};

export default function PlatformControl() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [insts, setInsts] = useState([]);
  const [notifs, setNotifs] = useState([]);
  const [workspace, setWorkspace] = useState(null);

  useEffect(() => {
    api.get("/workspace/me").then(({ data }) => {
      setWorkspace(data);
      if (data.sections?.stats) setStats(data.sections.stats);
    }).catch(() => {});
    api.get("/admin/platform-stats").then(({ data }) => setStats(data)).catch(() => {});
    api.get("/admin/colleges").then(({ data }) => setInsts(data.items || [])).catch(() => setInsts([]));
    api.get("/admin/notifications").then(({ data }) => setNotifs(data.items || [])).catch(() => setNotifs([]));
  }, []);

  const overviewStats = [
    { key: "kpi-institutions", label: "Active institutions", val: stats?.institutions ?? "-", sub: "Across partner streams", icon: Building2 },
    { key: "kpi-pending", label: "Pending signups", val: stats?.pending_signups ?? "-", sub: "Awaiting review", icon: Activity },
    { key: "kpi-students", label: "Total students", val: stats?.students ?? "-", sub: "On platform", icon: Users },
    { key: "kpi-jobs", label: "Open drives", val: stats?.jobs_open ?? "-", sub: "Across recruiters", icon: Briefcase },
  ];

  const compactStats = [
    { label: "Applications", val: stats?.applications ?? "-", icon: Send },
    { label: "Estimated MRR", val: stats?.estimated_mrr_inr ?? "-", icon: Award },
    { label: "Notifications", val: notifs.length, icon: Bell },
  ];

  const institutionMix = useMemo(() => {
    const rows = stats?.by_type || [];
    if (rows.length) return rows.map((row) => ({ name: row.type || "Other", count: row.count || 0 }));
    const grouped = insts.reduce((acc, inst) => {
      const type = inst.type || "Other";
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {});
    return Object.entries(grouped).map(([name, count]) => ({ name, count }));
  }, [insts, stats]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="font-mono text-[10px] tracking-[0.28em] text-ink-400">PLATFORM / COMMAND</div>
          <h1 className="font-display text-5xl md:text-6xl tracking-tightest mt-3" data-testid="platform-heading">
            {workspace?.headline || `Good morning, ${user?.name?.split(" ")[1] || "Admin"}.`}
          </h1>
          <p className="font-serif text-lg text-ink-500 mt-2 max-w-3xl">
            {workspace?.subtitle || "The full layer. Institutions, recruiters, revenue, signups, and audit activity."}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className="hidden xl:flex items-center gap-2 border border-line bg-bone-50 px-3 py-2 text-xs text-ink-400">
            <Search size={14} />
            <span>Search institutions, recruiters, audits...</span>
          </div>
          <button 
            onClick={async () => {
              if (window.confirm("Are you sure you want to reseed missing demo data? This will safely insert any missing colleges, students, and recruiters without deleting any existing records.")) {
                try {
                  await api.post("/admin/reseed-demo");
                  toast.success("Demo data reseeded. Reloading…");
                  setTimeout(() => window.location.reload(), 700);
                } catch (e) {
                  toast.error("Reseed failed: " + (e.response?.data?.detail || e.message));
                }
              }
            }}
            className="btn bg-rust border-rust hover:bg-accent hover:border-accent text-bone-100"
          >
            Reseed Missing Demo Data
          </button>
          <Link to="/platform/institutions" className="btn">
            Review queue <ArrowUpRight size={14} />
          </Link>
        </div>
      </div>

      <div className="editorial bg-ink-900 text-bone-100 p-5 flex flex-wrap items-center justify-between gap-4">
        <div>
          <div className="font-mono text-[10px] tracking-[0.24em] text-bone-100/45">LIVE OPERATING LAYER</div>
          <div className="font-display text-2xl tracking-tight mt-1">Platform health, partner movement, and fan-out status.</div>
        </div>
        <Link to="/platform/analytics" className="btn bg-bone-100 text-ink-900 border-bone-100 hover:bg-accent hover:border-accent">
          Open analytics
        </Link>
      </div>

      {/* AI EXECUTIVE SUMMARY + VOICE + RISK RADAR (ported from CareerOS intelligence layer) */}
      <PlatformSummary stats={stats} insts={insts} />

      <section className="grid grid-cols-12 gap-3" data-testid="platform-kpis">
        {overviewStats.map((k) => (
          <div key={k.label} data-testid={k.key} className="col-span-12 md:col-span-3 editorial p-6">
            <div className="flex items-center justify-between">
              <div className="font-mono text-[10px] tracking-[0.22em] text-ink-400 uppercase">{k.label}</div>
              <div className="w-9 h-9 border border-line bg-bone-50 grid place-items-center text-accent">
                <k.icon size={16} />
              </div>
            </div>
            <div className="font-display text-5xl tracking-tightest mt-5 tnum">{fmt(k.val)}</div>
            <div className="text-sm text-ink-500 mt-2">{k.sub}</div>
          </div>
        ))}
      </section>

      <section className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-3 space-y-3">
          {compactStats.map((stat) => (
            <div key={stat.label} className="editorial p-5 flex items-center justify-between">
              <div>
                <div className="font-mono text-[10px] tracking-[0.2em] text-ink-400 uppercase">{stat.label}</div>
                <div className="font-display text-3xl tracking-tight mt-2 tnum">
                  {stat.label === "Estimated MRR" && stat.val !== "-" ? "Rs " : ""}{fmt(stat.val)}
                </div>
              </div>
              <div className="w-10 h-10 bg-bone-100 border border-line grid place-items-center text-accent">
                <stat.icon size={17} />
              </div>
            </div>
          ))}

          <div className="editorial p-5">
            <div className="flex items-center justify-between">
              <div className="font-mono text-[10px] tracking-[0.2em] text-ink-400">PRIORITY ACTIONS</div>
              <MoreHorizontal size={15} className="text-ink-300" />
            </div>
            <div className="mt-4 space-y-3">
              {(workspace?.actions || []).slice(0, 4).map((action) => (
                <Link key={action.label} to={action.to || "#"} className="block border-b border-line pb-3 last:border-0 last:pb-0">
                  <div className="font-display text-base tracking-tight">{action.label}</div>
                  <div className="text-xs text-ink-500 mt-1 leading-relaxed">{action.reason}</div>
                </Link>
              ))}
              {(workspace?.actions || []).length === 0 && <div className="text-xs text-ink-400">No priority actions returned.</div>}
            </div>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-6 space-y-3">
          <div className="editorial p-6">
            <div className="flex items-center justify-between mb-5">
              <div>
                <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">INSTITUTION MIX</div>
                <h3 className="font-display text-2xl tracking-tight mt-1">Where CareerOS lives</h3>
              </div>
              <button className="btn btn-ghost py-2 px-3 text-xs"><Download size={13} /> Export</button>
            </div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={institutionMix} margin={{ top: 8, right: 4, left: -28, bottom: 0 }} barCategoryGap="35%">
                  <CartesianGrid vertical={false} stroke="rgba(10,10,10,0.08)" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: "#777", fontSize: 10, fontFamily: "JetBrains Mono" }} />
                  <YAxis axisLine={false} tickLine={false} allowDecimals={false} tick={{ fill: "#777", fontSize: 10, fontFamily: "JetBrains Mono" }} />
                  <Tooltip contentStyle={{ borderRadius: 0, border: "1px solid rgba(10,10,10,0.18)", fontSize: 11 }} />
                  <Bar dataKey="count" radius={[0, 0, 0, 0]}>
                    {institutionMix.map((_, i) => <Cell key={i} fill={i === 0 ? "#ff3b00" : "rgba(255,59,0,0.28)"} />)}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="editorial p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">RECENT INSTITUTIONS</div>
                <h3 className="font-display text-2xl tracking-tight mt-1">Partner ledger</h3>
              </div>
              <Link to="/platform/institutions" className="pill text-accent border-accent/40">View all</Link>
            </div>
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-line">
                  <th className="pb-3 font-mono text-[10px] tracking-[0.2em] text-ink-400">INSTITUTION</th>
                  <th className="pb-3 font-mono text-[10px] tracking-[0.2em] text-ink-400">STREAM</th>
                  <th className="pb-3 font-mono text-[10px] tracking-[0.2em] text-ink-400 text-right">STATUS</th>
                </tr>
              </thead>
              <tbody>
                {insts.slice(0, 6).map((inst) => (
                  <tr key={inst.institution_id || inst.name} className="border-b border-line hover:bg-bone-50">
                    <td className="py-3">
                      <div className="font-medium">{inst.name}</div>
                      <div className="font-mono text-[10px] text-ink-400">{inst.short_name}</div>
                    </td>
                    <td className="py-3 text-sm text-ink-500">{inst.type || "Institution"}</td>
                    <td className="py-3 text-right">
                      <span className={`font-mono text-[10px] uppercase ${inst.approved ? "text-accent" : "text-ink-400"}`}>
                        {inst.approved ? "Active" : "Pending"}
                      </span>
                    </td>
                  </tr>
                ))}
                {insts.length === 0 && <tr><td colSpan={3} className="py-8 text-center text-xs text-ink-400">No institutions returned by API.</td></tr>}
              </tbody>
            </table>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-3 space-y-3">
          <div className="editorial p-5">
            <div className="flex items-center justify-between mb-4">
              <div className="font-mono text-[10px] tracking-[0.2em] text-ink-400">RECENT ACTIVITY</div>
              <MoreHorizontal size={15} className="text-ink-300" />
            </div>
            <div className="space-y-4">
              {notifs.slice(0, 8).map((n, i) => (
                <div key={`${n.created_at}-${i}`} className="flex items-start gap-3">
                  <div className={`w-5 h-5 mt-0.5 border grid place-items-center ${n.status === "sent" ? "border-accent text-accent" : "border-line text-ink-400"}`}>
                    <Activity size={11} />
                  </div>
                  <div className="min-w-0 flex-1">
                    <div className="text-xs font-medium text-ink-700 truncate">{n.event || n.channel}</div>
                    <div className="text-[10px] text-ink-400 mt-0.5 truncate">{n.subject || n.status}</div>
                  </div>
                  <div className="font-mono text-[9px] text-ink-400">{n.created_at?.slice(11, 16)}</div>
                </div>
              ))}
              {notifs.length === 0 && <div className="text-xs text-ink-400">No notifications yet.</div>}
            </div>
          </div>

          <div className="editorial p-5">
            <div className="font-mono text-[10px] tracking-[0.2em] text-ink-400">CHANNEL MIX</div>
            <div className="mt-4 space-y-3">
              {["email", "telegram", "system"].map((channel) => {
                const count = notifs.filter((n) => (n.channel || "").toLowerCase() === channel).length;
                const pct = notifs.length ? Math.min(100, Math.round((count / notifs.length) * 100)) : 0;
                return (
                  <div key={channel}>
                    <div className="flex items-center justify-between font-mono text-[10px] uppercase">
                      <span>{channel}</span>
                      <span className="text-accent">{count}</span>
                    </div>
                    <div className="h-1.5 bg-bone-200 mt-1">
                      <div className="h-full bg-accent" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
