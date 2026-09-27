import React, { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { toast } from "sonner";
import { Check, X, Bell, Building2, Clock, GraduationCap, ShieldCheck, Users } from "lucide-react";

export default function AdminPanel() {
  const [pending, setPending] = useState([]);
  const [colleges, setColleges] = useState([]);
  const [selections, setSelections] = useState({});

  const load = async () => {
    const [p, c] = await Promise.all([
      api.get("/admin/pending-signups"),
      api.get("/admin/colleges"),
    ]);
    setPending(p.data.items || []);
    setColleges(c.data.items || []);
  };

  useEffect(() => { load().catch(() => toast.error("Admin only")); }, []);

  const approve = async (u) => {
    const sel = selections[u.user_id] || {};
    const role = sel.role ?? u.role ?? "";
    if (!role) { toast.error("Select a role before approving."); return; }
    const institution_id = sel.institution_id ?? u.institution_id ?? "";
    await api.post(`/admin/approve/${u.user_id}`, { role, institution_id: institution_id || null });
    toast.success("Approved");
    load();
  };
  const reject = async (id) => { await api.post(`/admin/reject/${id}`); toast.success("Rejected"); load(); };
  const testNotif = async () => { await api.post("/admin/test-notification"); toast.success("Fan-out triggered"); };

  const collegeTypes = useMemo(() => {
    const grouped = colleges.reduce((acc, college) => {
      const type = college.type || "Institution";
      acc[type] = (acc[type] || 0) + 1;
      return acc;
    }, {});
    return Object.entries(grouped);
  }, [colleges]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="font-mono text-[10px] tracking-[0.28em] text-accent">INSTITUTIONS / CONTROL</div>
          <h1 className="font-display text-5xl md:text-6xl tracking-tightest mt-3" data-testid="institutions-heading">
            Approve. Manage. Override.
          </h1>
          <p className="font-serif text-lg text-ink-500 mt-2">Every partner institution and every pending signup, in one place.</p>
        </div>
        <button onClick={testNotif} data-testid="test-notif-btn" className="btn btn-ghost"><Bell size={14} /> Trigger test fan-out</button>
      </div>

      <section className="grid grid-cols-12 gap-3">
        {[
          { label: "Pending approvals", value: pending.length, icon: Clock, sub: "Needs admin review" },
          { label: "Institutions", value: colleges.length, icon: Building2, sub: "Partner ledger" },
          { label: "Approved", value: colleges.filter((c) => c.approved).length, icon: ShieldCheck, sub: "Active workspaces" },
          { label: "Departments", value: colleges.reduce((sum, c) => sum + (c.departments || []).length, 0), icon: GraduationCap, sub: "Mapped teams" },
        ].map((card) => (
          <div key={card.label} className="col-span-12 md:col-span-3 editorial p-5">
            <div className="flex items-center justify-between">
              <div className="font-mono text-[10px] tracking-[0.22em] text-ink-400 uppercase">{card.label}</div>
              <card.icon size={16} className="text-accent" />
            </div>
            <div className="font-display text-4xl tracking-tightest mt-4 tnum">{card.value}</div>
            <div className="text-sm text-ink-500 mt-1">{card.sub}</div>
          </div>
        ))}
      </section>

      <section className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-7 editorial" data-testid="pending-table">
          <div className="p-6 border-b border-line flex items-center justify-between">
            <div>
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">PENDING APPROVALS / {pending.length}</div>
              <h3 className="font-display text-2xl tracking-tight mt-1">Awaiting verification</h3>
            </div>
            <span className="pill pill-accent">{pending.length} queued</span>
          </div>
          {pending.length === 0 ? (
            <div className="px-6 py-12 text-center text-ink-400">All caught up.</div>
          ) : (
            <div className="divide-y divide-line">
              {pending.map((u) => (
                <div key={u.user_id} className="p-5" data-testid={`pending-${u.user_id}`}>
                  <div className="flex items-start gap-4">
                    <div className="w-11 h-11 border border-line bg-bone-100 grid place-items-center font-display text-accent">
                      {(u.name || "?").charAt(0)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <div className="font-display text-xl tracking-tight">{u.name}</div>
                          <div className="text-xs text-ink-500">{u.email}</div>
                        </div>
                        {u.role ? <span className="pill">{u.role}</span> : <span className="pill bg-bone-200 text-ink-400">unassigned</span>}
                      </div>
                      {u.institution?.name && (
                        <div className="mt-3 text-xs text-ink-400">
                          Requested institution: <span className="text-ink-700">{u.institution.name}</span>
                          {u.institution.affiliated_university ? ` · ${u.institution.affiliated_university}` : ""}
                        </div>
                      )}
                      <div className="mt-4 grid grid-cols-12 gap-3">
                        <div className="col-span-12 md:col-span-4">
                          <div className="font-mono text-[10px] text-ink-400 tracking-[0.18em]">ROLE</div>
                          <select
                            value={selections[u.user_id]?.role ?? u.role ?? ""}
                            onChange={(e) => setSelections((s) => ({ ...s, [u.user_id]: { ...s[u.user_id], role: e.target.value } }))}
                            data-testid={`role-select-${u.user_id}`}
                            className="mt-1 w-full px-2 py-2 border border-line bg-bone-50 text-xs focus:outline-none"
                          >
                            <option value="">Select role…</option>
                            <option value="institution_admin">Institution Admin</option>
                            <option value="tpo">TPO</option>
                            <option value="faculty">Faculty</option>
                            <option value="student">Student</option>
                            <option value="recruiter">Recruiter</option>
                          </select>
                        </div>
                        <div className="col-span-12 md:col-span-4">
                          <div className="font-mono text-[10px] text-ink-400 tracking-[0.18em]">INSTITUTION</div>
                          <select
                            value={selections[u.user_id]?.institution_id ?? u.institution_id ?? ""}
                            onChange={(e) => setSelections((s) => ({ ...s, [u.user_id]: { ...s[u.user_id], institution_id: e.target.value } }))}
                            data-testid={`institution-select-${u.user_id}`}
                            className="mt-1 w-full px-2 py-2 border border-line bg-bone-50 text-xs focus:outline-none"
                          >
                            <option value="">No institution</option>
                            {colleges.map((c) => (
                              <option key={c.institution_id} value={c.institution_id}>{c.name}</option>
                            ))}
                          </select>
                        </div>
                        <div className="col-span-12 md:col-span-4 flex items-end gap-2 justify-end">
                          <button onClick={() => approve(u)} data-testid={`approve-${u.user_id}`} className="btn py-2 px-3 text-xs">
                            <Check size={12} /> Approve
                          </button>
                          <button onClick={() => reject(u.user_id)} data-testid={`reject-${u.user_id}`} className="btn btn-ghost py-2 px-3 text-xs">
                            <X size={12} /> Reject
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="col-span-12 lg:col-span-5 space-y-3">
          <div className="editorial p-6">
            <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">INSTITUTION MIX</div>
            <h3 className="font-display text-2xl tracking-tight mt-1">Partner categories</h3>
            <div className="mt-5 space-y-4">
              {collegeTypes.map(([type, count]) => {
                const pct = colleges.length ? Math.round((count / colleges.length) * 100) : 0;
                return (
                  <div key={type}>
                    <div className="flex items-center justify-between font-mono text-[10px] uppercase">
                      <span>{type}</span>
                      <span className="text-accent">{count}</span>
                    </div>
                    <div className="h-2 bg-bone-200 mt-1"><div className="h-full bg-accent" style={{ width: `${pct}%` }} /></div>
                  </div>
                );
              })}
              {collegeTypes.length === 0 && <div className="text-sm text-ink-400">No institutions returned.</div>}
            </div>
          </div>

          <div className="editorial p-6 bg-bone-50">
            <div className="flex items-center gap-3">
              <Users size={18} className="text-accent" />
              <div>
                <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">APPROVAL FLOW</div>
                <div className="font-display text-xl tracking-tight">Review identity, institution, and role before activation.</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <div className="editorial" data-testid="colleges-table">
        <div className="p-6 border-b border-line">
          <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">PARTNER INSTITUTIONS / {colleges.length}</div>
          <h3 className="font-display text-2xl tracking-tight mt-1 flex items-center gap-2"><Building2 size={20} /> The platform map</h3>
        </div>
        <div className="grid grid-cols-12 px-6 py-3 border-b border-line font-mono text-[10px] tracking-[0.24em] text-ink-400">
          <div className="col-span-4">INSTITUTION</div>
          <div className="col-span-2">STREAM</div>
          <div className="col-span-3">UNIVERSITY</div>
          <div className="col-span-2">DEPARTMENTS</div>
          <div className="col-span-1 text-right">STATUS</div>
        </div>
        {colleges.map((c) => (
          <div key={c.institution_id} className="grid grid-cols-12 px-6 py-4 border-b border-line items-center text-sm hover:bg-bone-50">
            <div className="col-span-4">
              <div className="font-medium">{c.name}</div>
              <div className="text-xs text-ink-400">{c.city || ""} {c.state || ""}</div>
            </div>
            <div className="col-span-2"><span className="pill bg-bone-100">{c.type}</span></div>
            <div className="col-span-3 text-ink-500">{c.affiliated_university || "-"}</div>
            <div className="col-span-2 flex flex-wrap gap-1">
              {(c.departments || []).slice(0, 2).map((d) => <span key={d} className="pill bg-bone-100 text-[9px]">{d}</span>)}
            </div>
            <div className="col-span-1 text-right font-mono text-[10px]">
              {c.approved ? <span className="text-accent">ACTIVE</span> : <span className="text-ink-400">PENDING</span>}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
