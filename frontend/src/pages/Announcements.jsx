import React, { useEffect, useMemo, useState } from "react";
import { api } from "../lib/api";
import { toast } from "sonner";
import { CalendarDays, ChevronLeft, ChevronRight, Megaphone, MoreHorizontal, Pin, Plus, Send } from "lucide-react";
import { useAuth } from "../App";

const KINDS = ["drive", "training", "report", "fdp", "general"];
const KIND_COLOR = { drive: "#ff3b00", training: "#0a0a0a", report: "#c1440e", fdp: "#4a5d3a", general: "#9a9a9a" };
const DAYS = ["M", "T", "W", "T", "F", "S", "S"];

export default function Announcements() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [form, setForm] = useState({ title: "", body: "", kind: "general", pinned: false });
  const [adding, setAdding] = useState(false);

  const load = () => api.get("/announcements").then(({ data }) => setItems(data.items || []));
  useEffect(() => { load().catch(() => setItems([])); }, []);

  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/announcements", form);
      toast.success("Broadcast sent - fan-out triggered");
      setForm({ title: "", body: "", kind: "general", pinned: false });
      setAdding(false);
      load();
    } catch { toast.error("Failed"); }
  };

  const canPost = ["tpo", "institution_admin", "faculty", "super_admin"].includes(user?.role);
  const pinned = items.filter((item) => item.pinned);
  const kindCounts = useMemo(() => KINDS.map((kind) => ({
    kind,
    count: items.filter((item) => item.kind === kind).length,
  })), [items]);

  const [monthOffset, setMonthOffset] = useState(0);
  const view = useMemo(() => {
    const cursor = new Date();
    cursor.setDate(1);
    cursor.setMonth(cursor.getMonth() + monthOffset);
    const year = cursor.getFullYear();
    const month = cursor.getMonth();
    return {
      year,
      month,
      label: cursor.toLocaleDateString("en-IN", { month: "long", year: "numeric" }),
      days: new Date(year, month + 1, 0).getDate(),
      isCurrentMonth: monthOffset === 0,
    };
  }, [monthOffset]);

  const monthKey = `${view.year}-${String(view.month + 1).padStart(2, "0")}`;
  const monthDays = useMemo(() => Array.from({ length: view.days }, (_, i) => i + 1), [view.days]);
  const activeDays = useMemo(() => new Set(
    items
      .filter((item) => (item.created_at || "").slice(0, 7) === monthKey)
      .map((item) => Number(item.created_at?.slice(8, 10)))
      .filter(Boolean),
  ), [items, monthKey]);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <div className="font-mono text-[10px] tracking-[0.28em] text-ink-400">BROADCASTS</div>
          <h1 className="font-display text-5xl md:text-6xl tracking-tightest mt-3" data-testid="ann-heading">
            What the campus <span className="text-accent">needs to know.</span>
          </h1>
        </div>
        {canPost && (
          <button onClick={() => setAdding(true)} data-testid="new-ann-btn" className="btn">
            <Plus size={14} /> New broadcast
          </button>
        )}
      </div>

      <section className="grid grid-cols-12 gap-3">
        <div className="col-span-12 lg:col-span-3 space-y-3">
          <div className="editorial p-5">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-display text-xl tracking-tight">Broadcast Calendar</div>
                <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 uppercase mt-0.5">{view.label}</div>
              </div>
              <div className="flex gap-1">
                <button
                  onClick={() => setMonthOffset((m) => m - 1)}
                  aria-label="Previous month"
                  className="w-7 h-7 border border-line grid place-items-center text-ink-400 hover:border-ink-900 hover:text-ink-900 transition-colors"
                ><ChevronLeft size={14} /></button>
                <button
                  onClick={() => setMonthOffset((m) => Math.min(0, m + 1))}
                  disabled={view.isCurrentMonth}
                  aria-label="Next month"
                  className="w-7 h-7 border border-line grid place-items-center text-ink-400 hover:border-ink-900 hover:text-ink-900 transition-colors disabled:opacity-40 disabled:pointer-events-none"
                ><ChevronRight size={14} /></button>
              </div>
            </div>
            <div className="grid grid-cols-7 gap-1 mt-5">
              {DAYS.map((day, i) => <div key={`${day}-${i}`} className="text-center font-mono text-[10px] text-ink-400">{day}</div>)}
              {monthDays.map((day) => (
                <div
                  key={day}
                  className={`h-9 border border-line grid place-items-center font-mono text-xs ${activeDays.has(day) ? "bg-accent text-bone-100 border-accent" : "bg-bone-50 text-ink-500"}`}
                >
                  {day}
                </div>
              ))}
            </div>
          </div>

          <div className="editorial p-5">
            <div className="font-mono text-[10px] tracking-[0.22em] text-ink-400">NOTIFICATION MIX</div>
            <div className="mt-4 space-y-3">
              {kindCounts.map(({ kind, count }) => {
                const pct = items.length ? Math.round((count / items.length) * 100) : 0;
                return (
                  <div key={kind}>
                    <div className="flex items-center justify-between font-mono text-[10px] uppercase">
                      <span style={{ color: KIND_COLOR[kind] }}>{kind}</span>
                      <span>{count}</span>
                    </div>
                    <div className="h-1.5 bg-bone-200 mt-1"><div className="h-full bg-accent" style={{ width: `${pct}%` }} /></div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-6 space-y-3">
          {adding && (
            <form onSubmit={submit} className="editorial p-6 grid grid-cols-12 gap-3" data-testid="ann-form">
              <input value={form.title} onChange={(e) => setForm({ ...form, title: e.target.value })} placeholder="Title"
                data-testid="ann-title" className="col-span-12 md:col-span-6 px-4 py-3 border border-line bg-bone-50 focus:outline-none focus:border-accent" required />
              <select value={form.kind} onChange={(e) => setForm({ ...form, kind: e.target.value })} data-testid="ann-kind"
                className="col-span-6 md:col-span-3 px-4 py-3 border border-line bg-bone-50">
                {KINDS.map((k) => <option key={k} value={k}>{k.toUpperCase()}</option>)}
              </select>
              <label className="col-span-6 md:col-span-3 flex items-center gap-2 px-4 py-3 border border-line bg-bone-50 text-sm">
                <input type="checkbox" checked={form.pinned} onChange={(e) => setForm({ ...form, pinned: e.target.checked })} />
                Pin to top
              </label>
              <textarea value={form.body} onChange={(e) => setForm({ ...form, body: e.target.value })} placeholder="Message"
                data-testid="ann-body" rows={4} className="col-span-12 px-4 py-3 border border-line bg-bone-50 focus:outline-none focus:border-accent font-serif" required />
              <button type="submit" data-testid="ann-submit" className="col-span-6 md:col-span-3 btn justify-center"><Send size={14} /> Broadcast</button>
              <button type="button" onClick={() => setAdding(false)} className="col-span-6 md:col-span-3 btn btn-ghost justify-center">Cancel</button>
            </form>
          )}

          <div className="editorial" data-testid="ann-list">
            <div className="p-6 border-b border-line flex items-center justify-between">
              <div>
                <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">LIVE ANNOUNCEMENTS / {items.length}</div>
                <h3 className="font-display text-2xl tracking-tight mt-1">Notification feed</h3>
              </div>
              <MoreHorizontal size={17} className="text-ink-300" />
            </div>
            <div className="divide-y divide-line">
              {items.map((a) => (
                <div key={a.announcement_id} className="p-6 grid grid-cols-12 gap-4 items-start" data-testid={`ann-${a.announcement_id}`}>
                  <div className="col-span-12 md:col-span-2">
                    <div className="w-10 h-10 border border-line bg-bone-100 grid place-items-center" style={{ color: KIND_COLOR[a.kind] || "#9a9a9a" }}>
                      <Megaphone size={17} />
                    </div>
                    <div className="font-mono text-[10px] text-ink-400 mt-3">{a.created_at?.slice(0, 10)}</div>
                  </div>
                  <div className="col-span-12 md:col-span-10">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="font-mono text-[10px] tracking-[0.22em] uppercase" style={{ color: KIND_COLOR[a.kind] || "#9a9a9a" }}>{a.kind}</div>
                        <h3 className="font-display text-2xl tracking-tight mt-1">{a.title}</h3>
                      </div>
                      {a.pinned && <span className="pill text-accent border-accent/40"><Pin size={10} /> PINNED</span>}
                    </div>
                    <p className="font-serif text-base text-ink-700 mt-2">{a.body}</p>
                    <div className="font-mono text-[10px] text-ink-400 tracking-[0.2em] mt-3 uppercase">by {a.by_role}</div>
                  </div>
                </div>
              ))}
              {items.length === 0 && <div className="p-12 text-center text-ink-400">No broadcasts yet.</div>}
            </div>
          </div>
        </div>

        <div className="col-span-12 lg:col-span-3 space-y-3">
          <div className="editorial bg-ink-900 text-bone-100 p-6">
            <div className="font-mono text-[10px] tracking-[0.24em] text-bone-100/45">PINNED</div>
            <div className="font-display text-5xl tracking-tightest mt-3 tnum text-accent">{pinned.length}</div>
            <div className="text-sm text-bone-100/60 mt-2">Critical campus messages currently pinned.</div>
          </div>

          <div className="editorial p-5 bg-bone-50">
            <div className="flex items-center gap-3">
              <CalendarDays size={18} className="text-accent" />
              <div>
                <div className="font-mono text-[10px] tracking-[0.22em] text-ink-400">EVENT MANAGEMENT</div>
                <div className="font-display text-xl tracking-tight">Calendar marks active broadcast days using CareerOS data.</div>
              </div>
            </div>
          </div>

          <div className="editorial p-5">
            <div className="font-mono text-[10px] tracking-[0.22em] text-ink-400">RECENT PINNED</div>
            <div className="mt-4 space-y-3">
              {pinned.slice(0, 4).map((item) => (
                <div key={item.announcement_id} className="border-b border-line pb-3 last:border-0 last:pb-0">
                  <div className="font-medium text-sm">{item.title}</div>
                  <div className="text-[10px] text-ink-400 mt-1">{item.created_at?.slice(0, 10)}</div>
                </div>
              ))}
              {pinned.length === 0 && <div className="text-xs text-ink-400">No pinned broadcasts.</div>}
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
