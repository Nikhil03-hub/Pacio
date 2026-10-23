import React, { useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../App";
import { api } from "../lib/api";
import { toast } from "sonner";
import { ArrowRight } from "lucide-react";

export default function OnboardingPending() {
  const { user, refresh } = useAuth();
  const [form, setForm] = useState({
    college_name: "",
    short_name: "",
    role: "tpo",
    affiliated_university: "",
    partnership_type: "CRT",
    department: "",
  });
  const [submitted, setSubmitted] = useState(user?.college_id ? true : false);

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center text-ink-500">
        <Link to="/login" className="ink-link">Please sign in</Link>
      </div>
    );
  }

  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/signup", form);
      toast.success("Request submitted. Awaiting Super Admin approval.");
      setSubmitted(true);
      await refresh();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "Submission failed");
    }
  };

  return (
    <main className="min-h-screen bg-bone-100 grain">
      <div className="max-w-[1100px] mx-auto px-6 md:px-12 py-20">
        <Link to="/" className="num-mono text-[11px] tracking-[0.24em] text-ink-400 ink-link">CAREEROS / ONBOARDING</Link>
        <h1 className="font-display text-5xl md:text-6xl tracking-tightest mt-6">Institutional verification.</h1>
        <p className="font-serif text-xl text-ink-500 mt-4 max-w-2xl">
          {submitted
            ? "Thanks — your request is in the queue. A Skill Tank super-admin will verify your institution shortly."
            : "Tell us about your institution. A super-admin will review and activate your placement command center."}
        </p>

        {submitted ? (
          <div className="mt-12 grid md:grid-cols-3 gap-6">
            <div className="border border-line p-8 bg-bone-50 md:col-span-2">
              <div className="num-mono text-[10px] tracking-[0.24em] text-ink-400">STATUS</div>
              <div className="font-display text-4xl mt-2">Pending approval</div>
              <p className="text-ink-500 mt-4">You will receive an Email + Telegram notification the moment your access is granted. Refresh this page periodically to check status.</p>
              <button onClick={refresh} className="mt-6 inline-flex items-center gap-2 bg-accent text-bone-100 px-5 py-3 text-sm hover:bg-accent-hover transition-colors" data-testid="refresh-status-btn">
                Re-check approval <ArrowRight size={14} />
              </button>
            </div>
            <div className="border border-line p-8">
              <div className="num-mono text-[10px] tracking-[0.24em] text-ink-400">YOU</div>
              <div className="font-display text-xl mt-2">{user.name}</div>
              <div className="text-sm text-ink-500">{user.email}</div>
              <div className="hairline my-6" />
              <div className="num-mono text-[10px] tracking-[0.24em] text-ink-400">ROLE</div>
              <div className="font-display text-xl mt-2 uppercase">{user.role}</div>
            </div>
          </div>
        ) : (
          <form onSubmit={submit} className="mt-12 grid md:grid-cols-2 gap-6 max-w-3xl" data-testid="signup-form">
            {[
              { k: "college_name", label: "Institution name", placeholder: "Keshav Memorial Institute of Technology" },
              { k: "short_name", label: "Short name", placeholder: "KMIT" },
              { k: "affiliated_university", label: "Affiliated university", placeholder: "JNTUH" },
            ].map((f) => (
              <label key={f.k} className="block">
                <span className="num-mono text-[10px] tracking-[0.24em] text-ink-400">{f.label.toUpperCase()}</span>
                <input
                  required={f.k === "college_name"}
                  value={form[f.k]}
                  onChange={(e) => setForm({ ...form, [f.k]: e.target.value })}
                  placeholder={f.placeholder}
                  data-testid={`signup-${f.k}`}
                  className="mt-2 w-full px-4 py-3 border border-line bg-bone-50 focus:outline-none focus:border-ink-900"
                />
              </label>
            ))}
            <label className="block">
              <span className="num-mono text-[10px] tracking-[0.24em] text-ink-400">YOUR ROLE</span>
              <select
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                data-testid="signup-role"
                className="mt-2 w-full px-4 py-3 border border-line bg-bone-50 focus:outline-none focus:border-ink-900"
              >
                <option value="tpo">TPO · Training & Placement Officer</option>
                <option value="hod">HOD · Department Head</option>
                <option value="coordinator">Coordinator</option>
              </select>
            </label>
            <label className="block">
              <span className="num-mono text-[10px] tracking-[0.24em] text-ink-400">PARTNERSHIP</span>
              <select
                value={form.partnership_type}
                onChange={(e) => setForm({ ...form, partnership_type: e.target.value })}
                data-testid="signup-partnership"
                className="mt-2 w-full px-4 py-3 border border-line bg-bone-50 focus:outline-none focus:border-ink-900"
              >
                <option>CRT</option><option>FDP</option><option>External Placement Partner</option><option>Multi-program</option>
              </select>
            </label>
            <div className="md:col-span-2 mt-4">
              <button type="submit" data-testid="signup-submit" className="inline-flex items-center gap-3 bg-accent text-bone-100 px-7 py-4 text-sm font-medium hover:bg-accent-hover transition-colors">
                Request approval <ArrowRight size={16} />
              </button>
            </div>
          </form>
        )}
      </div>
    </main>
  );
}
