import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowUpRight, ArrowLeft, Lock, Mail } from "lucide-react";
import { api, setAuthToken } from "../lib/api";
import { useAuth } from "../App";
import { toast } from "sonner";

const ROLE_HOME = {
  super_admin: "/platform",
  institution_admin: "/institution",
  tpo: "/tpo",
  faculty: "/faculty",
  student: "/student",
  recruiter: "/recruiter",
};

const DEMO_USERS = [
  { email: "admin@careeros.app", label: "Super Admin · Platform", password: "careeros2026" },
  { email: "institution@kmit.in", label: "Institution Admin · KMIT", password: "careeros2026" },
  { email: "tpo@kmit.in", label: "TPO · Dr. Neil Gogte", password: "careeros2026" },
  { email: "faculty@kmit.in", label: "Faculty · Prof. Lavanya Iyer", password: "careeros2026" },
  { email: "student@kmit.in", label: "Student · Aarav Reddy", password: "careeros2026" },
  { email: "recruiter@amazon.com", label: "Recruiter · Amazon", password: "careeros2026" },
];

function fmtErr(d) {
  if (!d) return "Something went wrong.";
  if (typeof d === "string") return d;
  if (Array.isArray(d)) return d.map((e) => e?.msg || JSON.stringify(e)).join(" ");
  return d?.msg || String(d);
}

export default function Login() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [email, setEmail] = useState("tpo@kmit.in");
  const [password, setPassword] = useState("careeros2026");
  const [busy, setBusy] = useState(false);
  const [showForgot, setShowForgot] = useState(false);
  const [forgotEmail, setForgotEmail] = useState("");

  const handleGoogle = () => {
    window.location.href = "/api/auth/google/start";
  };

  const handleForgot = async (e) => {
    e.preventDefault();
    if (!forgotEmail) return;
    setBusy(true);
    try {
      await api.post("/auth/forgot-password", { email: forgotEmail });
      toast.success("Password reset email sent!");
      setShowForgot(false);
      setForgotEmail("");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to send reset email.");
    } finally {
      setBusy(false);
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setBusy(true);
    try {
      const { data } = await api.post("/auth/login", { email, password });
      setAuthToken(data.access_token);
      setUser(data.user);
      const home = ROLE_HOME[data.user.role] || "/";
      const target = data.user.approved || data.user.role === "super_admin" ? home : "/pending";
      // Wait one tick so AuthProvider state commits before Protected re-reads it
      await new Promise((r) => setTimeout(r, 30));
      navigate(target, { replace: true });
    } catch (err) {
      toast.error(fmtErr(err?.response?.data?.detail) || "Login failed");
    } finally { setBusy(false); }
  };

  const fillDemo = (u) => { setEmail(u.email); setPassword(u.password); };

  return (
    <main className="min-h-screen bg-bone-100 grid md:grid-cols-12 grain">
      {/* LEFT — editorial */}
      <div className="hidden md:flex md:col-span-7 relative bg-ink-900 text-bone-100 p-12 lg:p-16 flex-col justify-between overflow-hidden">
        <div className="absolute inset-0 opacity-[0.07] pointer-events-none" style={{ backgroundImage: "linear-gradient(135deg, transparent 49.5%, #FF3B00 49.5%, #FF3B00 50.5%, transparent 50.5%)", backgroundSize: "70px 70px" }} />
        <div className="relative">
          <Link to="/" className="inline-flex items-center gap-3" data-testid="login-brand">
            <div className="w-7 h-7 bg-bone-100 grid place-items-center"><div className="w-2 h-2 bg-accent" /></div>
            <span className="font-display font-bold tracking-tight">CareerOS</span>
          </Link>
        </div>
        <div className="relative max-w-2xl">
          <div className="font-mono text-[11px] tracking-[0.28em] text-bone-100/40 mb-5">§ MISSION CONTROL</div>
          <h1 className="font-display text-6xl lg:text-7xl tracking-tightest leading-[0.92]">
            Six roles. <br /><span className="text-accent">One canvas.</span>
          </h1>
          <p className="font-serif text-lg text-bone-100/70 mt-8 max-w-md">
            Super admins approve institutions. TPOs run command centers.
            Faculty teach batches. Students track readiness. Recruiters scout talent.
            Every login lands in a different workspace — by design.
          </p>
          <div className="mt-10 grid grid-cols-2 gap-3 max-w-xl">
            {DEMO_USERS.map((u) => (
              <button key={u.email} onClick={() => fillDemo(u)}
                className="text-left border border-bone-100/15 hover:border-accent transition-colors p-3"
                data-testid={`demo-${u.email.split("@")[0]}`}>
                <div className="font-mono text-[10px] tracking-[0.2em] text-bone-100/40 uppercase">{u.label.split("·")[0].trim()}</div>
                <div className="text-sm mt-1 truncate">{u.email}</div>
              </button>
            ))}
          </div>
        </div>
        <div className="relative font-mono text-[10px] tracking-[0.24em] text-bone-100/40">
          AUTH · GOOGLE OAUTH · BCRYPT · TLS 1.3 · SESSION COOKIE
        </div>
      </div>

      {/* RIGHT — form */}
      <div className="md:col-span-5 flex items-center justify-center p-8 md:p-12">
        <div className="w-full max-w-md">
          <Link to="/" className="ink-link text-sm text-ink-500 inline-flex items-center gap-2 mb-10">
            <ArrowLeft size={14} /> Back
          </Link>
          <div className="font-mono text-[11px] tracking-[0.28em] text-ink-400">SIGN IN · STEP 01</div>
          <h2 className="font-display text-4xl md:text-5xl tracking-tightest mt-3">Welcome back.</h2>
          <p className="font-serif text-lg text-ink-500 mt-3">Enter with your institutional email & password — or use a demo role from the left.</p>

          <form onSubmit={handleLogin} className="mt-10 space-y-4">
            <label className="block">
              <span className="font-mono text-[10px] tracking-[0.24em] text-ink-400">EMAIL</span>
              <div className="mt-2 flex items-center gap-2 border border-line bg-bone-50 px-3">
                <Mail size={14} className="text-ink-400" />
                <input value={email} onChange={(e) => setEmail(e.target.value)} type="email" data-testid="login-email"
                  className="bg-transparent w-full py-3 text-sm focus:outline-none" required />
              </div>
            </label>
            <label className="block">
              <div className="flex justify-between items-center">
                <span className="font-mono text-[10px] tracking-[0.24em] text-ink-400">PASSWORD</span>
                <button type="button" onClick={() => setShowForgot(true)} className="font-mono text-[10px] text-accent tracking-wider hover:underline" data-testid="forgot-password-link">
                  FORGOT?
                </button>
              </div>
              <div className="mt-2 flex items-center gap-2 border border-line bg-bone-50 px-3">
                <Lock size={14} className="text-ink-400" />
                <input value={password} onChange={(e) => setPassword(e.target.value)} type="password" data-testid="login-password"
                  className="bg-transparent w-full py-3 text-sm focus:outline-none" required />
              </div>
            </label>
            <button type="submit" disabled={busy} data-testid="login-submit" className="w-full btn justify-center disabled:opacity-50">
              {busy ? "Signing in…" : "Sign in"} <ArrowUpRight size={14} />
            </button>
          </form>

          <div className="my-8 hairline" />

          <button onClick={handleGoogle} data-testid="google-signin-btn"
            className="w-full flex items-center justify-center gap-3 border border-line px-6 py-4 text-sm font-medium hover:bg-ink-900 hover:text-bone-100 hover:border-ink-900 transition-colors group">
            <svg width="16" height="16" viewBox="0 0 48 48"><path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3c-1.6 4.5-5.9 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.8 1.1 7.9 3l5.7-5.7C33.9 6.1 29.2 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.3-.4-3.5z"/><path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 13 24 13c3 0 5.8 1.1 7.9 3l5.7-5.7C33.9 6.1 29.2 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/><path fill="#4CAF50" d="M24 44c5.1 0 9.8-2 13.3-5.2l-6.1-5.2c-2 1.4-4.5 2.4-7.2 2.4-5.3 0-9.7-3.5-11.3-8.3l-6.6 5.1C9.5 39.6 16.2 44 24 44z"/><path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.3 4.2-4.2 5.6l6.1 5.2c-.4.4 6.8-5 6.8-14.8 0-1.3-.1-2.3-.4-3.5z"/></svg>
            Continue with Google
          </button>

          <div className="mt-6 text-center text-xs text-ink-500">
            Don't have an account? <Link to="/register" className="text-accent font-medium hover:underline" data-testid="register-link">Register here</Link>
          </div>

          <p className="text-xs text-ink-400 mt-8 leading-relaxed">
            All demo accounts use password <span className="font-mono">careeros2026</span>. Institutional data is encrypted in transit and at rest.
          </p>
        </div>
      </div>

      {showForgot && (
        <div className="fixed inset-0 bg-ink-900/30 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white border border-line p-6 max-w-sm w-full space-y-4">
            <div>
              <h3 className="font-display text-xl tracking-tight">Forgot Password?</h3>
              <p className="font-serif text-xs text-ink-500 mt-1">We will email you a password reset link.</p>
            </div>
            <form onSubmit={handleForgot} className="space-y-4">
              <div className="flex items-center gap-2 border border-line bg-bone-50 px-3 py-2">
                <Mail size={14} className="text-ink-400" />
                <input
                  type="email"
                  placeholder="Your registered email"
                  value={forgotEmail}
                  onChange={(e) => setForgotEmail(e.target.value)}
                  required
                  className="bg-transparent text-xs w-full focus:outline-none"
                  data-testid="forgot-email-input"
                />
              </div>
              <div className="flex gap-2">
                <button type="submit" disabled={busy} className="btn text-xs py-2 px-4 flex-1">
                  {busy ? "Sending…" : "Send Link"}
                </button>
                <button type="button" onClick={() => setShowForgot(false)} className="btn btn-ghost text-xs py-2 px-4 border border-line">
                  Cancel
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </main>
  );
}
