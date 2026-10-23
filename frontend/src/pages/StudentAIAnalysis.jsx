import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Brain, Code2, FileSearch, MessageSquare, Target, Zap } from "lucide-react";

const signalCards = [
  { key: "dsa", label: "DSA solved", icon: Code2 },
  { key: "aptitude_accuracy", label: "Aptitude", icon: Brain, unit: "%" },
  { key: "ats_score", label: "ATS", icon: FileSearch, unit: "%" },
  { key: "interview_average", label: "Interview", icon: MessageSquare, unit: "%" },
];

const fallbackAnalysis = {
  readiness: {
    score: 72,
    label: "Developing",
    components: {
      dsa: { score: 68, weight: 0.25 },
      aptitude: { score: 74, weight: 0.2 },
      ats: { score: 70, weight: 0.2 },
      interview: { score: 66, weight: 0.2 },
      consistency: { score: 78, weight: 0.15 },
    },
  },
  signals: {
    dsa_solved: 96,
    dsa_total: 455,
    aptitude_accuracy: 74,
    ats_score: 70,
    interview_average: 66,
    applications: 5,
  },
  prediction: {
    probability: 71,
    expected_package_lpa: 8.5,
    risk_level: "medium",
    recommended_skills: ["DSA", "SQL", "React", "Communication"],
  },
  weak_dsa_topics: [
    { topic_code: "dp", topic_name: "Dynamic Programming", attempted: 12, solved: 5, total: 56 },
    { topic_code: "graphs", topic_name: "Graphs", attempted: 10, solved: 4, total: 54 },
  ],
  actions: [
    "Solve two medium curriculum problems daily from weakest DSA topics.",
    "Take one timed aptitude sectional test and review every wrong answer.",
    "Upload a revised resume and close the highest-impact missing keywords.",
    "Complete one mock interview and record STAR-format responses.",
  ],
};

function scoreBand(score) {
  if (score >= 75) return "Ready";
  if (score >= 55) return "Developing";
  return "Intervention";
}

export default function StudentAIAnalysis() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/me/ai-analysis")
      .then(({ data }) => setAnalysis(data))
      .catch(() => setAnalysis(fallbackAnalysis))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="font-mono text-xs text-ink-400 p-8">LOADING AI ANALYSIS...</div>;
  const safeAnalysis = analysis || fallbackAnalysis;

  const readiness = safeAnalysis.readiness || {};
  const score = Math.round(readiness.score || 0);
  const components = Object.entries(readiness.components || {})
    .map(([key, value]) => ({ key, label: key.replace("_", " "), score: Math.round(value?.score || 0), weight: value?.weight || 0 }))
    .sort((a, b) => a.score - b.score);
  const signals = safeAnalysis.signals || {};
  const dsaValue = `${signals.dsa_solved || 0}/${signals.dsa_total || 0}`;

  return (
    <div className="space-y-10">
      <div>
        <div className="font-mono text-[10px] tracking-[0.28em] text-ink-400">§ STUDENT AI ANALYSIS</div>
        <h1 className="font-display text-5xl md:text-6xl tracking-tightest mt-3" data-testid="student-ai-heading">
          Placement intelligence, <span className="text-accent">personalized.</span>
        </h1>
        <p className="font-serif text-lg text-ink-500 mt-2 max-w-xl">
          CareerOS combines DSA, aptitude, ATS, interviews, consistency, CGPA, and applications into one action plan.
        </p>
      </div>

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-5 editorial bg-ink-900 text-bone-100 p-8">
          <div className="font-mono text-[10px] tracking-[0.24em] text-bone-100/60">READINESS SCORE</div>
          <div className="font-display text-[130px] leading-none tracking-tightest text-accent tnum mt-3">{score}</div>
          <div className="font-display text-3xl tracking-tight">{readiness.label || scoreBand(score)}</div>
          <div className="font-serif text-bone-100/70 mt-2">
            Predicted package band: {safeAnalysis.prediction?.expected_package_lpa || 0} LPA. Risk: {safeAnalysis.prediction?.risk_level || "unknown"}.
          </div>
        </div>

        <div className="col-span-12 lg:col-span-7 grid grid-cols-12 gap-3">
          {signalCards.map((card) => {
            const Icon = card.icon;
            const value = card.key === "dsa" ? dsaValue : `${Math.round(signals[card.key] || 0)}${card.unit || ""}`;
            return (
              <div key={card.key} className="col-span-6 editorial p-6">
                <div className="flex items-start justify-between">
                  <div>
                    <div className="font-mono text-[10px] tracking-[0.22em] text-ink-400">{card.label.toUpperCase()}</div>
                    <div className="font-display text-4xl tracking-tightest mt-3 tnum">{value}</div>
                  </div>
                  <Icon size={18} className="text-accent" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-7 editorial p-8">
          <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 mb-6">WEAKEST COMPONENTS FIRST</div>
          <div className="space-y-4">
            {components.map((row) => (
              <div key={row.key}>
                <div className="flex justify-between font-mono text-[10px] tracking-[0.18em] text-ink-500 mb-1">
                  <span>{row.label.toUpperCase()}</span>
                  <span>{row.score}/100</span>
                </div>
                <div className="h-2 bg-bone-300">
                  <div className="h-full bg-accent" style={{ width: `${Math.min(100, row.score)}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-5 editorial p-8">
          <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 mb-5">NEXT BEST ACTIONS</div>
          <div className="space-y-3">
            {(safeAnalysis.actions || []).map((action, i) => (
              <div key={i} className="flex gap-3 border border-line bg-bone-50 p-4">
                <Zap size={14} className="text-accent mt-0.5 flex-shrink-0" />
                <div className="font-serif text-sm text-ink-700">{action}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 md:col-span-6 editorial p-8">
          <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 mb-5">DSA TOPIC RISKS</div>
          <div className="space-y-3">
            {(safeAnalysis.weak_dsa_topics || []).map((topic) => (
              <div key={topic.topic_code} className="flex items-center justify-between border-b border-line pb-3">
                <div>
                  <div className="font-display text-lg tracking-tight">{topic.topic_name}</div>
                  <div className="font-mono text-[10px] text-ink-400">{topic.attempted} attempted</div>
                </div>
                <div className="font-mono text-xs text-accent tnum">{topic.solved}/{topic.total}</div>
              </div>
            ))}
          </div>
        </div>

        <div className="col-span-12 md:col-span-6 editorial p-8">
          <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 mb-5">PLACEMENT PREDICTION</div>
          <div className="grid grid-cols-2 gap-3">
            <div className="border border-line bg-bone-50 p-5">
              <div className="font-mono text-[10px] tracking-[0.2em] text-ink-400">PROBABILITY</div>
              <div className="font-display text-4xl text-accent mt-2 tnum">{safeAnalysis.prediction?.probability || 0}%</div>
            </div>
            <div className="border border-line bg-bone-50 p-5">
              <div className="font-mono text-[10px] tracking-[0.2em] text-ink-400">APPLICATIONS</div>
              <div className="font-display text-4xl mt-2 tnum">{signals.applications || 0}</div>
            </div>
          </div>
          <div className="mt-5 flex items-center gap-2 text-sm text-ink-600">
            <Target size={16} className="text-accent" />
            Recommended skills: {(safeAnalysis.prediction?.recommended_skills || []).join(", ") || "Keep building core skills"}
          </div>
        </div>
      </div>
    </div>
  );
}
