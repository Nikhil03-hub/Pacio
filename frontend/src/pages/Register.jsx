import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { toast } from "sonner";
import { Building, User } from "lucide-react";

export default function Register() {
  const navigate = useNavigate();

  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [collegeName, setCollegeName] = useState("");
  const [department, setDepartment] = useState("");
  const [university, setUniversity] = useState("");
  const [partnershipType, setPartnershipType] = useState("CRT");
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !email || !collegeName || !university || !department) {
      toast.error("Please fill in all fields.");
      return;
    }

    setBusy(true);
    try {
      await api.post("/auth/register", {
        name,
        email,
        college_name: collegeName,
        affiliated_university: university,
        partnership_type: partnershipType,
        department,
      });
      setDone(true);
    } catch (err) {
      toast.error(err.response?.data?.detail || "Registration failed.");
    } finally {
      setBusy(false);
    }
  };

  if (done) {
    return (
      <div className="min-h-screen bg-bone-100 flex flex-col items-center justify-center p-6">
        <div className="w-full max-w-[460px] editorial p-8 md:p-10 space-y-5 bg-white text-center">
          <div className="font-mono text-[10px] tracking-[0.28em] text-ink-400">§ REGISTRATION RECEIVED</div>
          <h1 className="font-display text-3xl tracking-tightest leading-tight">
            {collegeName} is <span className="text-accent">pending review.</span>
          </h1>
          <p className="font-serif text-sm text-ink-500">
            A CareerOS admin will review and approve your institution shortly. Once approved,
            sign in with Google using <span className="font-mono text-ink-900">{email}</span> to
            access your workspace — no password needed.
          </p>
          <button onClick={() => navigate("/login")} className="btn w-full py-3 justify-center font-mono text-[10px] tracking-[0.22em] uppercase mt-2">
            Back to sign in
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-bone-100 flex flex-col items-center justify-center p-6 select-none">
      <div className="w-full max-w-[500px] editorial p-8 md:p-10 space-y-8 bg-white">

        <div className="text-center space-y-2">
          <div className="font-mono text-[10px] tracking-[0.28em] text-ink-400">§ INSTITUTION ONBOARDING</div>
          <h1 className="font-display text-4xl tracking-tightest leading-none">
            Register your <span className="text-accent">institution</span>
          </h1>
          <p className="font-serif text-sm text-ink-500">
            New to CareerOS? Tell us about your institution. Once approved, you and your
            students sign in with Google — no separate password.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            <div>
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">YOUR NAME</div>
              <div className="mt-2 flex items-center gap-2 border border-line px-3 py-2 bg-bone-50">
                <User size={14} className="text-ink-400" />
                <input
                  type="text"
                  placeholder="Full Name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  disabled={busy}
                  className="bg-transparent text-sm w-full focus:outline-none"
                  data-testid="register-name-input"
                />
              </div>
            </div>

            <div>
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">GOOGLE EMAIL ADDRESS</div>
              <div className="mt-2 flex items-center gap-2 border border-line px-3 py-2 bg-bone-50">
                <User size={14} className="text-ink-400" />
                <input
                  type="email"
                  placeholder="you@institution.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={busy}
                  className="bg-transparent text-sm w-full focus:outline-none"
                  data-testid="register-email-input"
                />
              </div>
              <p className="text-[11px] text-ink-400 mt-1.5">Use the same Google account you'll sign in with later.</p>
            </div>

            <div>
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">COLLEGE NAME</div>
              <div className="mt-2 flex items-center gap-2 border border-line px-3 py-2 bg-bone-50">
                <Building size={14} className="text-ink-400" />
                <input
                  type="text"
                  placeholder="e.g. Vasavi College of Engineering"
                  value={collegeName}
                  onChange={(e) => setCollegeName(e.target.value)}
                  required
                  disabled={busy}
                  className="bg-transparent text-sm w-full focus:outline-none"
                  data-testid="register-tpo-college"
                />
              </div>
            </div>
            <div>
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">AFFILIATED UNIVERSITY</div>
              <input
                type="text"
                placeholder="e.g. JNTUH, Osmania"
                value={university}
                onChange={(e) => setUniversity(e.target.value)}
                required
                disabled={busy}
                className="mt-2 w-full px-3 py-2 border border-line bg-bone-50 text-sm focus:outline-none"
                data-testid="register-tpo-university"
              />
            </div>
            <div>
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">DEPARTMENT</div>
              <input
                type="text"
                placeholder="e.g. CSE"
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                required
                disabled={busy}
                className="mt-2 w-full px-3 py-2 border border-line bg-bone-50 text-sm focus:outline-none"
                data-testid="register-tpo-dept"
              />
            </div>
            <div>
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">PARTNERSHIP TYPE</div>
              <select
                value={partnershipType}
                onChange={(e) => setPartnershipType(e.target.value)}
                className="mt-2 w-full px-3 py-2 border border-line bg-bone-50 text-sm focus:outline-none"
                data-testid="register-tpo-partnership"
              >
                <option value="CRT">Campus Recruitment Training (CRT)</option>
                <option value="FDP">Faculty Development Program (FDP)</option>
                <option value="Multi-program">Multi-program</option>
              </select>
            </div>
          </div>

          <button
            type="submit"
            disabled={busy}
            className="btn w-full py-3 flex items-center justify-center gap-2 font-mono text-[10px] tracking-[0.22em] uppercase"
            data-testid="register-submit-btn"
          >
            <Building size={14} />
            {busy ? "SUBMITTING…" : "REGISTER INSTITUTION"}
          </button>
        </form>

        <div className="text-center pt-2">
          <button
            onClick={() => navigate("/login")}
            className="inline-flex items-center gap-1 text-xs text-ink-400 hover:text-ink-900 transition-colors font-mono tracking-wider"
          >
            ALREADY APPROVED? SIGN IN WITH GOOGLE
          </button>
        </div>
      </div>
    </div>
  );
}
