import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import { Download, FileJson, FileSpreadsheet, FileText, ShieldCheck } from "lucide-react";
import { api, apiUrl, getAuthToken } from "../lib/api";

const FALLBACK_REPORTS = [
  { report_id: "placement_pdf", kind: "pdf", title: "Placement board report", href: "/reports/placement.pdf", file: "placement-report.pdf", audience: "Board", cadence: "Weekly", decision: "Are offers, CTC, departments, and recruiters moving in the right direction?" },
  { report_id: "training_pdf", kind: "pdf", title: "Training intervention report", href: "/reports/training.pdf", file: "training-report.pdf", audience: "Faculty", cadence: "Twice weekly", decision: "Which cohorts need action before the next drive?" },
  { report_id: "department_pdf", kind: "pdf", title: "Department health report", href: "/reports/department.pdf", file: "department-report.pdf", audience: "HOD", cadence: "Weekly", decision: "Which department is underperforming and why?" },
  { report_id: "students_csv", kind: "csv", title: "Student intelligence export", href: "/reports/students.csv", file: "students.csv", audience: "Ops", cadence: "On demand", decision: "Which students should move into action lists?" },
  { report_id: "applications_csv", kind: "csv", title: "Application pipeline export", href: "/reports/applications.csv", file: "applications.csv", audience: "TPO", cadence: "Daily", decision: "Where are applications stuck?" },
  { report_id: "placements_csv", kind: "csv", title: "Placement ledger export", href: "/reports/placements.csv", file: "placements.csv", audience: "Audit", cadence: "Monthly", decision: "Which recruiter relationships compound over time?" },
];

const iconFor = (kind) => {
  if (kind === "csv") return FileSpreadsheet;
  if (kind === "json") return FileJson;
  return FileText;
};

export default function Reports() {
  const [manifest, setManifest] = useState(null);
  const reports = manifest?.items?.length ? manifest.items : FALLBACK_REPORTS;
  const board = manifest?.board_packet || {};

  useEffect(() => {
    api.get("/reports/manifest").then(({ data }) => setManifest(data)).catch(() => {});
  }, []);

  const download = async (href, filename) => {
    const token = getAuthToken();
    const res = await fetch(apiUrl(href), {
      credentials: "include",
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-10">
      <section className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-8 editorial p-10 lg:p-14 bg-ink-900 text-bone-100">
          <div className="font-mono text-[10px] tracking-[0.28em] text-bone-100/40">PHASE 8 / REPORTS ENGINE</div>
          <h1 className="font-display text-5xl md:text-7xl tracking-tightest leading-[0.94] mt-3" data-testid="reports-heading">
            Boardroom-ready intelligence packets.
          </h1>
          <p className="font-serif text-lg text-bone-100/70 mt-5 max-w-2xl">
            Every export answers a leadership question: risk, forecast, cohort action, recruiter movement, and audit trace.
          </p>
          <button
            onClick={async () => {
              try {
                await api.post("/digest/send", {});
                toast.success("Digest compiled and queued for delivery.");
              } catch (e) {
                toast.error("Digest failed: " + (e.response?.data?.detail || e.message));
              }
            }}
            className="mt-6 btn bg-bone-100 text-ink-900 border-bone-100 hover:bg-accent hover:border-accent hover:text-white"
          >
            Send Periodic Digest
          </button>
        </div>

        <div className="col-span-12 lg:col-span-4 editorial p-8 bg-bone-50" data-testid="board-packet">
          <div className="flex items-center gap-3 text-ink-400">
            <ShieldCheck size={18} />
            <div className="font-mono text-[10px] tracking-[0.24em] uppercase">Board Packet</div>
          </div>
          <div className="font-display text-4xl tracking-tight mt-5">{board.status || "ready"}</div>
          <div className="grid grid-cols-3 gap-3 mt-6">
            <div>
              <div className="font-mono text-[10px] text-ink-400">SCORE</div>
              <div className="font-display text-3xl tnum mt-1">{board.command_score || 0}</div>
            </div>
            <div>
              <div className="font-mono text-[10px] text-ink-400">FORECAST</div>
              <div className="font-display text-3xl tnum mt-1 text-accent">{board.forecasted_offers || 0}</div>
            </div>
            <div>
              <div className="font-mono text-[10px] text-ink-400">RISKS</div>
              <div className="font-display text-3xl tnum mt-1">{board.risk_count || 0}</div>
            </div>
          </div>
          <button
            onClick={() => download("/reports/board-packet.json", "careeros-board-packet.json")}
            className="mt-7 btn w-full justify-center"
            data-testid="download-board-packet"
          >
            <FileJson size={15} /> Download board packet
          </button>
        </div>
      </section>

      <section className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-4 editorial p-8">
          <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">EXPORT SEQUENCE</div>
          <h2 className="font-display text-2xl tracking-tight mt-1">Recommended packet order</h2>
          <div className="mt-6 space-y-3">
            {(board.recommended_sequence || ["placement_pdf", "department_pdf", "training_pdf", "applications_csv"]).map((id, i) => {
              const report = reports.find((item) => item.report_id === id);
              return (
                <div key={id} className="grid grid-cols-12 gap-3 border border-line bg-bone-50 p-4">
                  <div className="col-span-2 font-mono text-[10px] text-ink-400 tnum">{String(i + 1).padStart(2, "0")}</div>
                  <div className="col-span-10">
                    <div className="font-display text-lg tracking-tight">{report?.title || id}</div>
                    <div className="text-xs text-ink-500 mt-1">{report?.decision || "Leadership packet artifact"}</div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="col-span-12 lg:col-span-8 grid grid-cols-12 gap-3" data-testid="reports-grid">
          {reports.map((report) => {
            const Icon = iconFor(report.kind);
            return (
              <div key={report.report_id || report.title} className="col-span-12 md:col-span-6 editorial p-7 hover:border-ink-900 transition-colors flex flex-col" data-testid={`report-${report.file}`}>
                <div className="flex items-start justify-between gap-4">
                  <div className="w-11 h-11 grid place-items-center bg-ink-900 text-bone-100">
                    <Icon size={18} />
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 uppercase">{report.kind}</div>
                    <div className="text-xs text-ink-500 mt-1">{report.cadence}</div>
                  </div>
                </div>
                <h3 className="font-display text-2xl tracking-tight mt-5">{report.title}</h3>
                <p className="text-sm text-ink-500 mt-2 flex-1 leading-relaxed">{report.decision}</p>
                <div className="mt-5 flex items-center justify-between border-t border-line pt-4">
                  <span className="font-mono text-[10px] tracking-[0.2em] text-ink-400 uppercase">{report.audience}</span>
                  <button
                    onClick={() => download(report.href, report.file)}
                    data-testid={`download-${report.file}`}
                    className="inline-flex items-center justify-center gap-2 btn py-3 text-xs"
                  >
                    <Download size={14} /> Download
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
