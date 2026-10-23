import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../App";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { AlertTriangle, ArrowUpRight, CheckCircle2 } from "lucide-react";
import VoiceSummary from "../components/VoiceSummary";
import HealthBreakdown from "../components/HealthBreakdown";
import HighRiskStudents from "../components/HighRiskStudents";
import AnomalyDetective from "../components/AnomalyDetective";
import WhatIfSimulator from "../components/WhatIfSimulator";
import AICopilot from "../components/AICopilot";

const num = (value, decimals = 0) => {
  if (value === null || value === undefined || value === "") return "0";
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return value;
  return numeric.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
};

const firstName = (name) => (
  (name || "TPO")
    .split(/[\s.]+/)
    .find((w) => w && w.length > 1 && !/^(Dr|Mr|Mrs|Ms|Prof)$/i.test(w)) || "TPO"
);

export default function Overview() {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [training, setTraining] = useState(null);
  const [dsa, setDsa] = useState(null);
  const [workspace, setWorkspace] = useState(null);

  useEffect(() => {
    api.get("/workspace/me").then(({ data }) => setWorkspace(data)).catch(() => {});
    api.get("/placements/overview").then(({ data }) => setData(data));
    api.get("/training/completion").then(({ data }) => setTraining(data));
    api.get("/dsa/intelligence").then(({ data }) => setDsa(data));
  }, []);

  const overview = workspace?.sections || data || {};
  const latest = overview.latest_year || overview.year_summaries?.[0] || data?.year_summaries?.[0];
  const placed = overview.students_placed ?? data?.students_placed ?? 0;
  const total = overview.students_total ?? data?.students_total ?? 0;
  const rate = overview.placement_rate ?? (total ? Math.round((placed / total) * 100) : 0);
  const kpis = workspace?.kpis?.length
    ? workspace.kpis
    : [
      { label: "Offers this year", value: latest?.offers, sub: `${latest?.companies || 0} recruiters`, status: "neutral" },
      { label: "Avg CTC", value: latest?.avg_lpa, unit: " LPA", sub: `Top ${latest?.top_offer_lpa || 0} LPA` },
      {
        label: "Training avg",
        value: training ? Math.round(training.by_program.reduce((a, b) => a + b.avg_completion, 0) / Math.max(1, training.by_program.length)) : 0,
        unit: "%",
        sub: `${training?.by_program?.length || 0} programs`,
      },
      { label: "Readiness avg", value: data?.readiness?.avg_readiness, unit: "/100", sub: `${data?.readiness?.needs_intervention || 0} need intervention` },
    ];
  const dsaTotal = dsa?.total_problems || 0;
  const dsaAvg = workspace?.role === "faculty"
    ? Math.round(workspace?.sections?.readiness?.component_avgs?.dsa || 0)
    : dsa?.by_topic
      ? Math.round(
        dsa.by_topic.reduce((a, t) => {
          const denominator = Math.max(1, (t.students || 0) * (t.total || t.total_problems || 0));
          return a + ((t.solved || 0) / denominator);
        }, 0) / Math.max(1, dsa.by_topic.length) * 100
      )
      : 0;

  const sideMetric = workspace?.role === "faculty"
    ? {
      eyebrow: "INTERVENTION QUEUE",
      value: workspace.sections?.readiness?.needs_intervention || 0,
      suffix: "",
      sub: `${workspace.sections?.readiness?.count || 0} students in ${workspace.scope?.department || "department"}`,
      lowerLabel: "READINESS AVG",
      lowerValue: `${workspace.sections?.readiness?.avg_readiness || 0}/100`,
      lowerSub: "department scoped",
    }
    : {
      eyebrow: "TOP OFFER / CURRENT YEAR",
      value: latest?.top_offer_lpa || 0,
      suffix: "L",
      sub: `${latest?.top_company || "Top recruiter"} / SDE`,
      lowerLabel: "PLACEMENT RATE",
      lowerValue: `${rate}%`,
      lowerSub: `${placed} of ${total} placed`,
    };

  const readinessAvg = data?.readiness?.avg_readiness ?? overview?.readiness?.avg_readiness;
  const needsInt = data?.readiness?.needs_intervention ?? overview?.readiness?.needs_intervention ?? 0;
  const liveAlerts = workspace?.alerts || [];
  const topAlert = liveAlerts[0];
  const scopeWord = workspace?.role === "faculty" ? "department" : "placement";
  const execNarration = [
    `This is your live ${scopeWord} summary.`,
    total ? `Placement rate is ${rate} percent, with ${placed} of ${total} students placed.` : null,
    latest?.offers
      ? `This cycle delivered ${num(latest.offers)} offers across ${latest.companies || 0} recruiters, averaging ${num(latest.avg_lpa, 1)} LPA${latest.top_offer_lpa ? `, peaking at ${num(latest.top_offer_lpa, 1)} LPA` : ""}${latest.top_company ? ` from ${latest.top_company}` : ""}.`
      : null,
    (readinessAvg !== undefined && readinessAvg !== null)
      ? `Average readiness is ${num(readinessAvg)} out of 100${needsInt ? `, with ${needsInt} student${needsInt === 1 ? "" : "s"} needing intervention` : ""}.`
      : null,
    liveAlerts.length
      ? `${liveAlerts.length} live alert${liveAlerts.length === 1 ? "" : "s"} need attention${topAlert?.title ? `, led by ${topAlert.title}` : ""}.`
      : "No urgent alerts across the pipeline.",
    needsInt
      ? `Recommended focus: run a readiness booster for the ${needsInt} flagged student${needsInt === 1 ? "" : "s"}, then sustain recruiter momentum.`
      : "Recommended focus: sustain recruiter momentum and convert open roles.",
  ].filter(Boolean).join(" ");

  const institutionId = workspace?.scope?.institution_id || user?.institution_id;
  const rosterPath = { tpo: "/tpo/roster", faculty: "/faculty/roster" }[workspace?.role];

  return (
    <div className="space-y-10">
      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 md:col-span-8 editorial p-10 lg:p-14 relative overflow-hidden">
          <div className="font-mono text-[10px] tracking-[0.28em] text-ink-400">
            {workspace?.eyebrow?.toUpperCase() || "MISSION CONTROL / LIVE"}
          </div>
          <h1 className="font-display text-5xl md:text-7xl tracking-tightest mt-3 leading-[0.95]" data-testid="overview-heading">
            {workspace?.headline || <>Good morning, <span className="text-accent">{firstName(user?.name)}.</span></>}
          </h1>
          <p className="font-serif text-lg text-ink-500 mt-3 max-w-2xl">
            {workspace?.subtitle || "Here's what's happening across your placement pipeline this morning."}
          </p>
          <div className="mt-8 flex flex-wrap gap-3 items-center">
            <span className="pill">AY / {latest?.academic_year || "2025-26"}</span>
            <span className="pill pill-solid">{latest?.companies || overview.open_jobs?.length || 0} recruiters live</span>
            <span className="pill">{workspace?.title || "Placement intelligence"}</span>
          </div>
        </div>
        <div className="col-span-12 md:col-span-4 editorial bg-ink-900 text-bone-100 p-8 lg:p-10 flex flex-col justify-between" data-testid="kpi-top-right">
          <div>
            <div className="font-mono text-[10px] tracking-[0.28em] text-bone-100/40">{sideMetric.eyebrow}</div>
            <div className="font-display text-[8vw] md:text-[6vw] tracking-tightest mt-3 leading-[0.9] text-accent tnum">
              {sideMetric.value}<span className="text-bone-100">{sideMetric.suffix}</span>
            </div>
            <div className="text-bone-100/70 mt-2">{sideMetric.sub}</div>
          </div>
          <div className="hairline border-bone-100/20 my-5" />
          <div>
            <div className="font-mono text-[10px] tracking-[0.28em] text-bone-100/40">{sideMetric.lowerLabel}</div>
            <div className="font-display text-5xl mt-2 tnum">{sideMetric.lowerValue}</div>
            <div className="text-bone-100/60 text-sm">{sideMetric.lowerSub}</div>
          </div>
        </div>
      </div>

      {/* AI EXECUTIVE SUMMARY — live narrative + voice narration (ported from CareerOS) */}
      <div className="editorial p-8 lg:p-10 bg-bone-50" data-testid="ai-exec-summary">
        <div className="flex items-center justify-between gap-4 flex-wrap">
          <div className="font-mono text-[10px] tracking-[0.28em] text-ink-400">AI EXECUTIVE SUMMARY / LIVE</div>
          <VoiceSummary text={execNarration} label="Narrate summary" />
        </div>
        <p className="font-serif text-xl text-ink-600 mt-4 leading-relaxed max-w-4xl">{execNarration}</p>
      </div>

      <AICopilot surface="overview-dashboard" />

      <div className="grid grid-cols-12 gap-3" data-testid="kpi-grid">
        {kpis.map((k, i) => {
          const decimals = Number.isInteger(Number(k.value || 0)) ? 0 : 1;
          return (
            <Link
              key={`${k.label}-${i}`}
              to={k.to || "#"}
              className="col-span-12 md:col-span-3 editorial p-6 hover:border-ink-900 transition-colors"
            >
              <div className="flex items-center justify-between text-ink-400">
                <div className="font-mono text-[10px] tracking-[0.24em]">{k.label.toUpperCase()}</div>
                <ArrowUpRight size={14} />
              </div>
              <div className="font-display text-5xl tracking-tightest mt-4 tnum">
                {k.unit === "INR" ? "Rs " : ""}{num(k.value, decimals)}{k.unit && k.unit !== "INR" ? k.unit : ""}
              </div>
              <div className="text-sm text-ink-500 mt-2">{k.sub}</div>
            </Link>
          );
        })}
      </div>

      {workspace && (
        <div className="grid grid-cols-12 gap-3" data-testid="workspace-decision-queue">
          <div className="col-span-12 md:col-span-7 editorial p-8">
            <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">DECISION QUEUE</div>
            <h3 className="font-display text-2xl tracking-tight mt-1">Priority actions</h3>
            <div className="mt-5 space-y-3">
              {(workspace.actions || []).slice(0, 4).map((action, i) => (
                <Link key={`${action.label}-${i}`} to={action.to} className="grid grid-cols-12 gap-4 border border-line bg-bone-50 p-4 hover:border-ink-900 transition-colors">
                  <div className="col-span-1 font-mono text-[10px] text-ink-400 tnum">{String(i + 1).padStart(2, "0")}</div>
                  <div className="col-span-8">
                    <div className="font-display text-lg tracking-tight">{action.label}</div>
                    <div className="text-xs text-ink-500 mt-1">{action.reason}</div>
                  </div>
                  <div className="col-span-3 text-right font-mono text-[10px] tracking-[0.18em] text-accent uppercase">{action.priority}</div>
                </Link>
              ))}
            </div>
          </div>
          <div className="col-span-12 md:col-span-5 editorial p-8 bg-bone-50">
            <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">LIVE SIGNALS</div>
            <h3 className="font-display text-2xl tracking-tight mt-1">Alerts</h3>
            <div className="mt-5 space-y-3">
              {(workspace.alerts || []).slice(0, 4).map((alert, i) => (
                <Link key={`${alert.title}-${i}`} to={alert.to || "#"} className="block border border-line bg-bone-100 p-4 hover:border-ink-900 transition-colors">
                  <div className="flex items-center gap-2 font-mono text-[10px] tracking-[0.18em] uppercase text-ink-400">
                    {alert.severity === "high" ? <AlertTriangle size={13} className="text-accent" /> : <CheckCircle2 size={13} />}
                    {alert.severity}
                  </div>
                  <div className="font-display text-lg tracking-tight mt-2">{alert.title}</div>
                  <div className="text-xs text-ink-500 mt-1">{alert.body}</div>
                </Link>
              ))}
              {(workspace.alerts || []).length === 0 && <div className="text-sm text-ink-400">No urgent alerts in this workspace.</div>}
            </div>
          </div>
        </div>
      )}

      {/* COLLEGE HEALTH 6-FACTOR + AI HIGH-RISK STUDENTS (ported from CareerOS intelligence layer) */}
      {institutionId && (
        <div className="grid grid-cols-12 gap-3" data-testid="health-risk-row">
          <div className="col-span-12 md:col-span-7">
            <HealthBreakdown institutionId={institutionId} showVoice />
          </div>
          <div className="col-span-12 md:col-span-5">
            <HighRiskStudents rosterPath={rosterPath} />
          </div>
        </div>
      )}

      {/* Anomaly detection and intervention modelling were built during the hackathon
          but never mounted, so the product claimed two intelligence features it did not
          show. They render from the same live placement payload as the rest of this page. */}
      {institutionId && (
        <div className="grid grid-cols-12 gap-3" data-testid="signal-forecast-row">
          <div className="col-span-12 md:col-span-7">
            <AnomalyDetective />
          </div>
          <div className="col-span-12 md:col-span-5">
            <WhatIfSimulator />
          </div>
        </div>
      )}

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 md:col-span-8 editorial p-8" data-testid="yoy-card">
          <div className="flex items-baseline justify-between mb-5">
            <div>
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">YEAR OVER YEAR</div>
              <h3 className="font-display text-2xl tracking-tight mt-1">Offers trajectory / 2017 to 2026</h3>
            </div>
            <span className="font-mono text-[11px] text-ink-400">SOURCE / INSTITUTIONAL</span>
          </div>
          <div className="h-72">
            <ResponsiveContainer>
              <BarChart data={[...(overview.year_summaries || data?.year_summaries || [])].reverse()}>
                <CartesianGrid stroke="rgba(10,10,10,0.06)" vertical={false} />
                <XAxis dataKey="academic_year" tick={{ fill: "#888", fontSize: 10, fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fill: "#888", fontSize: 10, fontFamily: "JetBrains Mono" }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ border: "1px solid rgba(10,10,10,0.2)", borderRadius: 0, background: "#FFF", fontFamily: "Satoshi" }} />
                <Bar dataKey="offers" fill="#0a0a0a" />
                <Bar dataKey="companies" fill="#FF3B00" />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="col-span-12 md:col-span-4 editorial bg-ink-900 text-bone-100 p-8" data-testid="top-recruiters-card">
          <div className="font-mono text-[10px] tracking-[0.24em] text-bone-100/40">TOP RECRUITERS</div>
          <div className="space-y-px mt-5">
            {(overview.top_recruiters || data?.top_recruiters || []).slice(0, 7).map((r, i) => (
              <div key={r.company} className="flex items-center justify-between py-3 border-b border-bone-100/10">
                <div className="flex items-center gap-3">
                  <span className="font-mono text-[10px] text-bone-100/40 tnum w-6">{String(i + 1).padStart(2, "0")}</span>
                  <span className="font-display tracking-tight">{r.company}</span>
                </div>
                <div className="text-right">
                  <div className="font-mono text-sm tnum">{r.selects}</div>
                  <div className="font-mono text-[10px] text-accent tnum">{num(r.max_ctc, 1)}L</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 md:col-span-7 editorial p-8" data-testid="dept-card">
          <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">BY DEPARTMENT</div>
          <h3 className="font-display text-2xl tracking-tight mt-1">Placement breakdown</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
            {(overview.department_breakdown || data?.department_breakdown || []).slice(0, 4).map((d) => {
              const pct = d.placement_rate ?? (d.total ? Math.round((d.placed / d.total) * 100) : 0);
              return (
                <div key={d.department} className="border border-line p-5 bg-bone-50" data-testid={`dept-${d.department}`}>
                  <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">{d.department}</div>
                  <div className="font-display text-4xl mt-2 tnum">{pct}%</div>
                  <div className="text-xs text-ink-500 mt-1">{d.placed}/{d.total}</div>
                  <div className="mt-3 h-1 bg-bone-300 relative">
                    <div className="absolute inset-y-0 left-0 bg-accent" style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
        <div className="col-span-12 md:col-span-5 editorial p-8 bg-bone-50">
          <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">DSA INTELLIGENCE / GLANCE</div>
          <h3 className="font-display text-2xl tracking-tight mt-1">DSA curriculum / {dsaTotal} problems</h3>
          <div className="font-display text-7xl tracking-tightest mt-6 tnum">{dsaAvg}%</div>
          <div className="text-ink-500 text-sm">{workspace?.role === "faculty" ? "Department DSA readiness component" : "Average problems solved"}</div>
          <div className="mt-5 grid grid-cols-3 gap-3 text-xs">
            <div>
              <div className="font-mono text-[10px] text-ink-400 tracking-[0.2em]">TOPICS</div>
              <div className="font-display text-2xl mt-1">{dsa?.by_topic?.length || 0}</div>
            </div>
            <div>
              <div className="font-mono text-[10px] text-ink-400 tracking-[0.2em]">LEADERS</div>
              <div className="font-display text-2xl mt-1">{dsa?.leaderboard?.length || 0}</div>
            </div>
            <div>
              <div className="font-mono text-[10px] text-ink-400 tracking-[0.2em]">PROBLEMS</div>
              <div className="font-display text-2xl mt-1">{dsaTotal}</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
