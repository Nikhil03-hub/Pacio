import React, { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { ArrowUpRight, BrainCircuit, Gauge, Route, ShieldCheck, Zap } from "lucide-react";
import AICopilot from "../components/AICopilot";

const fmt = (value, digits = 0) => {
  const n = Number(value || 0);
  return n.toLocaleString(undefined, { maximumFractionDigits: digits, minimumFractionDigits: digits });
};

const healthColor = (health) => ({
  strong: "#2f6b3f",
  healthy: "#2f6b3f",
  watch: "#c1440e",
  critical: "#9f1d1d",
  high: "#2f6b3f",
  medium: "#c1440e",
  low: "#9f1d1d",
}[health] || "#ff3b00");

function MetricCard({ metric, index }) {
  return (
    <div className={`${index === 0 ? "col-span-12 md:col-span-4" : "col-span-12 md:col-span-2"} editorial p-6`}>
      <div className="flex items-start justify-between gap-4">
        <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 uppercase">{metric.label}</div>
        <span className="w-2.5 h-2.5 mt-1" style={{ background: healthColor(metric.health) }} />
      </div>
      <div className={`${index === 0 ? "text-6xl" : "text-4xl"} font-display tracking-tightest mt-4 tnum`}>
        {fmt(metric.value, Number.isInteger(metric.value) ? 0 : 1)}{metric.unit}
      </div>
      <div className="text-sm text-ink-500 mt-3 leading-relaxed">{metric.question}</div>
    </div>
  );
}

export default function AnalyticsWorkbench() {
  const [data, setData] = useState(null);
  const [modules, setModules] = useState(null);
  const [bench, setBench] = useState(null);

  useEffect(() => {
    api.get("/analytics/engine").then(({ data }) => setData(data)).catch(() => setData(null));
    api.get("/intelligence/modules").then(({ data }) => setModules(data)).catch(() => setModules(null));
    api.get("/benchmarking/partner").then(({ data }) => setBench(data)).catch(() => setBench(null));
  }, []);

  // Previously this table was a hardcoded literal (84.2%, "91st percentile",
  // "Outperforming") rendered as live campus data. It now comes from
  // /api/benchmarking/partner, which ranks the institution against partner averages.
  const benchRows = useMemo(() => {
    const self = bench?.self;
    const avg = bench?.averages;
    if (!self || !avg) return [];
    const ordinal = (value) => {
      const n = Math.round(Number(value) || 0);
      const hundred = n % 100;
      const suffix = hundred > 10 && hundred < 14 ? 0 : Math.min(n % 10, 3);
      return `${n}${["th", "st", "nd", "rd"][suffix]}`;
    };
    const row = (name, key, unit, digits) => ({
      name,
      campus: `${fmt(self[key], digits)}${unit}`,
      peer: `${fmt(avg[key], digits)}${unit}`,
      pct: ordinal(self.percentile),
      status: Number(self[key]) >= Number(avg[key]) ? "Above partner average" : "Below partner average",
    });
    return [
      row("Placement Rate", "placement_rate", "%", 1),
      row("Avg Readiness", "avg_readiness", "", 1),
      row("Training Completion", "training_completion", "%", 1),
      row("Health Score", "health_score", "", 1),
    ];
  }, [bench]);

  const funnelData = useMemo(() => (data?.funnel || []).filter((row) => row.stage !== "Rejected"), [data]);
  const healthRows = data?.department_health || [];
  const summary = data?.summary || {};
  const scope = data?.scope || {};
  const riskPie = useMemo(() => {
    const rows = data?.risk_register || [];
    const grouped = rows.reduce((acc, row) => {
      const key = row.severity || "watch";
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});
    return Object.entries(grouped).map(([name, value]) => ({ name, value, color: healthColor(name) }));
  }, [data]);

  if (!data) {
    return <div className="font-mono text-xs tracking-[0.28em] text-ink-400">LOADING ANALYTICS ENGINE...</div>;
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="font-mono text-[10px] tracking-[0.28em] text-ink-400">PHASE 7 / ANALYTICS ENGINE</div>
          <h1 className="font-display text-5xl md:text-6xl tracking-tightest mt-3" data-testid="analytics-heading">
            Command intelligence, <span className="text-accent">not dashboards.</span>
          </h1>
          <p className="font-serif text-lg text-ink-500 mt-3 max-w-3xl">
            Forecasts, leakage, department health, and intervention load in one operating surface.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <span className="pill">Scope / {scope.institution || "Institution"}</span>
          <span className="pill">{scope.department || "All departments"}</span>
          <span className="pill pill-accent">Health / {summary.health || "watch"}</span>
        </div>
      </div>

      <AICopilot surface="analytics-workbench" />

      <section className="grid grid-cols-12 gap-3" data-testid="analytics-kpis">
        <div className="col-span-12 md:col-span-3 editorial bg-ink-900 text-bone-100 p-7">
          <div className="flex items-center gap-3 text-bone-100/50">
            <Gauge size={18} />
            <div className="font-mono text-[10px] tracking-[0.24em] uppercase">Operating Score</div>
          </div>
          <div className="font-display text-7xl tracking-tightest mt-5 tnum text-accent">
            {fmt(summary.command_score, 1)}
          </div>
          <div className="text-sm text-bone-100/60 mt-2">Composite of placement, readiness, training, and conversion.</div>
        </div>
        {(data.kpis || []).slice(0, 5).map((metric, index) => <MetricCard key={metric.label} metric={metric} index={index} />)}
      </section>

      <section className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-4 editorial p-6 bg-bone-50" data-testid="analytics-risk">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">RISK REGISTER</div>
              <h2 className="font-display text-2xl tracking-tight mt-1">Intervention load</h2>
            </div>
            <div className="w-10 h-10 border border-line grid place-items-center text-accent"><Zap size={17} /></div>
          </div>
          <div className="h-44 mt-4 relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie data={riskPie.length ? riskPie : [{ name: "clear", value: 1, color: "#ff3b00" }]} innerRadius={52} outerRadius={70} paddingAngle={4} dataKey="value">
                  {(riskPie.length ? riskPie : [{ color: "rgba(255,59,0,.28)" }]).map((entry, i) => <Cell key={i} fill={entry.color} stroke="none" />)}
                </Pie>
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
              <div className="font-display text-3xl tracking-tightest">{data.risk_register?.length || 0}</div>
              <div className="font-mono text-[10px] text-ink-400">RISKS</div>
            </div>
          </div>
          <div className="space-y-3">
            {(data.risk_register || []).slice(0, 4).map((risk) => (
              <div key={risk.risk} className="border-t border-line pt-3">
                <div className="flex items-center justify-between gap-3">
                  <div className="font-display text-lg tracking-tight">{risk.risk}</div>
                  <span className="font-mono text-[10px] uppercase text-accent">{risk.severity}</span>
                </div>
                <div className="text-xs text-ink-500 mt-1">{risk.signal}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-5 editorial p-6" data-testid="analytics-trend">
          <div className="flex items-start justify-between gap-4 mb-5">
            <div>
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">PLACEMENT TRAJECTORY</div>
              <h2 className="font-display text-2xl tracking-tight mt-1">Offer trend and recruiter liquidity</h2>
            </div>
            <span className="pill">{fmt(summary.offers_delta_pct, 1)}% YoY</span>
          </div>
          <div className="h-72">
            <ResponsiveContainer>
              <LineChart data={data.trend || []}>
                <CartesianGrid vertical={false} stroke="rgba(10,10,10,0.08)" />
                <XAxis dataKey="academic_year" tick={{ fontSize: 10, fill: "#777", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: "#777", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ borderRadius: 0, border: "1px solid rgba(10,10,10,0.18)" }} />
                <Line type="monotone" dataKey="offers" stroke="#ff3b00" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="companies" stroke="#0a0a0a" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-3 editorial p-6 bg-bone-50" data-testid="analytics-funnel">
          <div className="flex items-center gap-3 text-ink-400">
            <Route size={18} />
            <div className="font-mono text-[10px] tracking-[0.24em] uppercase">Funnel Leakage</div>
          </div>
          <div className="mt-5 h-52">
            <ResponsiveContainer>
              <BarChart data={funnelData}>
                <CartesianGrid vertical={false} stroke="rgba(10,10,10,0.08)" />
                <XAxis dataKey="stage" tick={{ fontSize: 9, fill: "#777", fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                <YAxis hide />
                <Tooltip contentStyle={{ borderRadius: 0, border: "1px solid rgba(10,10,10,0.18)" }} />
                <Bar dataKey="count" fill="rgba(10,10,10,.25)" />
                <Bar dataKey="leakage" fill="#ff3b00" />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 space-y-2">
            {funnelData.slice(0, 4).map((row) => (
              <div key={row.stage} className="flex items-center justify-between gap-3 text-xs border-t border-line pt-2">
                <span className="font-display">{row.stage}</span>
                <span className="font-mono text-accent tnum">{row.leakage}%</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-8 editorial p-6" data-testid="analytics-departments">
          <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">DEPARTMENT HEALTH</div>
          <h2 className="font-display text-2xl tracking-tight mt-1">Where leadership should look first</h2>
          <div className="mt-5 divide-y divide-line">
            {healthRows.map((row) => (
              <div key={row.department} className="grid grid-cols-12 gap-4 py-4 items-center">
                <div className="col-span-3">
                  <div className="font-display text-xl">{row.department}</div>
                  <div className="font-mono text-[10px] text-ink-400 uppercase">{row.health}</div>
                </div>
                <div className="col-span-2">
                  <div className="text-xs text-ink-400">Placement</div>
                  <div className="font-display text-3xl tnum">{fmt(row.placement_rate)}%</div>
                </div>
                <div className="col-span-2">
                  <div className="text-xs text-ink-400">Readiness</div>
                  <div className="font-display text-3xl tnum text-accent">{fmt(row.readiness_avg, 1)}</div>
                </div>
                <div className="col-span-5">
                  <div className="h-2 bg-bone-300">
                    <div className="h-full" style={{ width: `${Math.min(100, row.health_score)}%`, background: healthColor(row.health) }} />
                  </div>
                  <div className="text-xs text-ink-500 mt-2">{row.interventions} interventions</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-4 space-y-3">
          <div className="editorial p-6 bg-bone-50">
            <div className="flex items-center gap-3 text-ink-400">
              <BrainCircuit size={18} />
              <div className="font-mono text-[10px] tracking-[0.24em] uppercase">Recommendations</div>
            </div>
            <div className="mt-5 space-y-3">
              {(data.recommendations || []).map((rec) => (
                <Link key={rec.title} to={rec.to || "#"} className="block border border-line bg-bone-100 p-4 hover:border-accent transition-colors">
                  <div className="flex items-center justify-between gap-3">
                    <div className="font-display text-lg">{rec.title}</div>
                    <ArrowUpRight size={14} />
                  </div>
                  <div className="text-sm text-ink-500 mt-1">{rec.body}</div>
                </Link>
              ))}
            </div>
          </div>

          {modules?.cards?.length > 0 && (
            <div className="editorial p-6" data-testid="analytics-modules">
              <div className="flex items-center gap-3 text-ink-400">
                <ShieldCheck size={18} />
                <div className="font-mono text-[10px] tracking-[0.24em] uppercase">Module Health</div>
              </div>
              <div className="mt-5 space-y-3">
                {modules.cards.slice(0, 4).map((card) => (
                  <Link key={card.code} to={card.to || "#"} className="block border-b border-line pb-3 last:border-0 last:pb-0">
                    <div className="flex items-center justify-between">
                      <div className="font-display text-lg tracking-tight">{card.module}</div>
                      <span className="w-2.5 h-2.5" style={{ background: healthColor(card.health) }} />
                    </div>
                    <div className="text-sm text-ink-500 mt-1">{card.primary}</div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* PEER BENCHMARKING & COMPARISON */}
      <section className="border border-line bg-bone-50 p-6 space-y-6" data-testid="analytics-benchmarking">
        <div>
          <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">PEER BENCHMARKING</div>
          <h2 className="font-display text-2xl tracking-tight mt-1">Campus vs partner colleges</h2>
        </div>
        <div className="grid grid-cols-12 gap-6">
          <div className="col-span-12 md:col-span-7">
            <div className="editorial divide-y divide-line">
              <div className="grid grid-cols-12 gap-3 py-3 font-mono text-[10px] tracking-wider text-ink-400">
                <div className="col-span-4">METRIC</div>
                <div className="col-span-2 text-right">CAMPUS</div>
                <div className="col-span-3 text-right">PARTNER AVG</div>
                <div className="col-span-3 text-right">PERCENTILE</div>
              </div>
              {benchRows.map((bench) => (
                <div key={bench.name} className="grid grid-cols-12 gap-3 py-4 items-center text-sm">
                  <div className="col-span-4">
                    <div className="font-display font-bold">{bench.name}</div>
                    <div className="font-mono text-[9px] text-ink-600 uppercase tracking-wider mt-0.5">{bench.status}</div>
                  </div>
                  <div className="col-span-2 text-right font-display font-bold tnum">{bench.campus}</div>
                  <div className="col-span-3 text-right text-ink-500 tnum">{bench.peer}</div>
                  <div className="col-span-3 text-right font-mono font-bold text-accent tnum">{bench.pct}</div>
                </div>
              ))}
              {benchRows.length === 0 && (
                <div className="py-6 text-sm text-ink-500">
                  Benchmarking needs at least one partner college with student data. It appears here once that exists.
                </div>
              )}
            </div>
          </div>
          <div className="col-span-12 md:col-span-5 bg-bone-100/50 p-6 border border-line flex flex-col justify-between">
            <div>
              <div className="font-mono text-[9px] tracking-widest text-ink-400">BENCHMARK INSIGHT</div>
              <h4 className="font-display text-lg tracking-tight font-bold mt-1">
                {bench?.self ? `Rank ${bench.self.rank} within tracked partner colleges` : "Not enough data yet"}
              </h4>
              <p className="font-serif text-sm text-ink-600 mt-4 leading-relaxed">
                {bench?.insight || "Peer comparison is computed from the partner colleges on this platform. It cites no national statistics because none are collected."}
              </p>
            </div>
            <div className="font-mono text-[9px] text-ink-400 border-t border-line/30 pt-3 mt-6">
              Computed from partner college data · no external census
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
