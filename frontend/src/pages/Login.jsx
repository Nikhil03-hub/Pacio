import React, { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowLeft, ArrowUpRight, ChevronDown, Lock } from "lucide-react";
import { toast } from "sonner";
import { api, setAuthToken } from "../lib/api";
import { useAuth } from "../App";

const GoogleMark = () => (
  <svg width="16" height="16" viewBox="0 0 48 48" aria-hidden="true">
    <path fill="#FFC107" d="M43.6 20.5H42V20H24v8h11.3c-1.6 4.5-5.9 8-11.3 8-6.6 0-12-5.4-12-12s5.4-12 12-12c3 0 5.8 1.1 7.9 3l5.7-5.7C33.9 6.1 29.2 4 24 4 12.9 4 4 12.9 4 24s8.9 20 20 20 20-8.9 20-20c0-1.3-.1-2.3-.4-3.5z"/>
    <path fill="#FF3D00" d="M6.3 14.7l6.6 4.8C14.7 16 19 13 24 13c3 0 5.8 1.1 7.9 3l5.7-5.7C33.9 6.1 29.2 4 24 4 16.3 4 9.7 8.3 6.3 14.7z"/>
    <path fill="#4CAF50" d="M24 44c5.1 0 9.8-2 13.3-5.2l-6.1-5.2c-2 1.4-4.5 2.4-7.2 2.4-5.3 0-9.7-3.5-11.3-8.3l-6.6 5.1C9.5 39.6 16.2 44 24 44z"/>
    <path fill="#1976D2" d="M43.6 20.5H42V20H24v8h11.3c-.8 2.3-2.3 4.2-4.2 5.6l6.1 5.2c-.4.4 6.8-5 6.8-14.8 0-1.3-.1-2.3-.4-3.5z"/>
  </svg>
);

export default function Login() {
  const navigate = useNavigate();
  const { setUser } = useAuth();
  const [config, setConfig] = useState(null);
  const [showPassword, setShowPassword] = useState(false);
  const [form, setForm] = useState({ email: "", password: "" });
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/auth/config")
      .then(({ data }) => setConfig(data))
      .catch(() => setConfig({ google_enabled: true, password_enabled: false }));
  }, []);

  const handleGoogle = () => {
    window.location.href = "/api/auth/google/start";
  };

  const handlePassword = async (e) => {
    e.preventDefault();
    if (!form.email || !form.password) {
      toast.error("Enter your email and password.");
      return;
    }
    setBusy(true);
    try {
      const { data } = await api.post("/auth/login", { email: form.email, password: form.password });
      setAuthToken(data.access_token);
      setUser(data.user);
      navigate("/app", { replace: true });
    } catch (err) {
      toast.error(err.response?.data?.detail || "Sign in failed.");
    } finally {
      setBusy(false);
    }
  };

  const nothingConfigured = config && !config.google_enabled && !config.password_enabled;

  return (
    <main className="min-h-screen bg-bone-100 grid md:grid-cols-12 grain">
      {/* LEFT — editorial */}
      <div className="hidden md:flex md:col-span-7 relative bg-ink text-bone p-12 lg:p-16 flex-col justify-between overflow-hidden">
        <div className="absolute inset-0 opacity-[0.07] pointer-events-none" style={{ backgroundImage: "linear-gradient(135deg, transparent 49.5%, #FF3B00 49.5%, #FF3B00 50.5%, transparent 50.5%)", backgroundSize: "70px 70px" }} />
        <div className="relative">
          <Link to="/" className="inline-flex items-center gap-3" data-testid="login-brand">
            <div className="w-7 h-7 bg-bone grid place-items-center"><div className="w-2 h-2 bg-accent" /></div>
            <span className="font-display font-bold tracking-tight">CareerOS</span>
          </Link>
        </div>
        <div className="relative max-w-2xl">
          <div className="font-mono text-[11px] tracking-[0.28em] text-bone/40 mb-5">&sect; MISSION CONTROL</div>
          <h1 className="font-display text-6xl lg:text-7xl tracking-tightest leading-[0.92]">
            One platform. <br /><span className="text-accent">Every career decision.</span>
          </h1>
          <p className="font-serif text-lg text-bone/70 mt-8 max-w-md">
            CareerOS connects institutions, students, faculty, placement teams and recruiters
            in one intelligence layer. Sign in and it takes you straight to your workspace.
          </p>
        </div>
        <div className="relative font-mono text-[10px] tracking-[0.24em] text-bone/40">
          AUTH · SIGNED SESSIONS · TLS 1.3 · HTTP-ONLY COOKIE
        </div>
      </div>

      {/* RIGHT — sign in */}
      <div className="md:col-span-5 flex items-center justify-center p-8 md:p-12">
        <div className="w-full max-w-md">
          <Link to="/" className="ink-link text-sm text-ink-500 inline-flex items-center gap-2 mb-10">
            <ArrowLeft size={14} /> Back
          </Link>
          <div className="font-mono text-[11px] tracking-[0.28em] text-ink-400">SIGN IN</div>
          <h2 className="font-display text-4xl md:text-5xl tracking-tightest mt-3">Welcome to CareerOS.</h2>
          <p className="font-serif text-lg text-ink-500 mt-3">
            {config === null
              ? "Loading sign-in options…"
              : "Use the account your institution registered for you."}
          </p>

          {nothingConfigured && (
            <div className="mt-10 border border-rust bg-bone-50 p-5" data-testid="auth-unconfigured">
              <div className="font-mono text-[10px] tracking-[0.24em] text-rust uppercase">Sign-in unavailable</div>
              <p className="font-serif text-sm text-ink-600 mt-2">
                No authentication provider is configured on this deployment. Set GOOGLE_CLIENT_ID
                and GOOGLE_CLIENT_SECRET, or enable PASSWORD_AUTH_ENABLED.
              </p>
            </div>
          )}

          {config?.google_enabled && (
            <button onClick={handleGoogle} data-testid="google-signin-btn"
              className="w-full flex items-center justify-center gap-3 bg-accent text-bone px-6 py-4 mt-10 text-sm font-medium hover:bg-accent-hover transition-colors">
              <GoogleMark />
              Continue with Google
            </button>
          )}

          {config?.password_enabled && (
            <div className="mt-6">
              {!showPassword ? (
                <button
                  onClick={() => setShowPassword(true)}
                  data-testid="show-password-form"
                  className="w-full flex items-center justify-center gap-2 border border-line-strong text-ink py-3 text-xs font-mono tracking-[0.18em] uppercase hover:border-ink hover:bg-bone-200 transition-colors"
                >
                  <Lock size={13} /> Sign in with email <ChevronDown size={13} />
                </button>
              ) : (
                <form onSubmit={handlePassword} className="border border-line bg-bone-50 p-6 space-y-4" data-testid="password-form">
                  <div>
                    <label htmlFor="login-email" className="font-mono text-[10px] tracking-[0.24em] text-ink-400 uppercase">Email</label>
                    <input
                      id="login-email"
                      type="email"
                      autoComplete="username"
                      value={form.email}
                      onChange={(e) => setForm({ ...form, email: e.target.value })}
                      className="mt-2 w-full px-3 py-2.5 border border-line bg-white text-sm focus:outline-none focus:border-ink"
                      data-testid="login-email-input"
                    />
                  </div>
                  <div>
                    <label htmlFor="login-password" className="font-mono text-[10px] tracking-[0.24em] text-ink-400 uppercase">Password</label>
                    <input
                      id="login-password"
                      type="password"
                      autoComplete="current-password"
                      value={form.password}
                      onChange={(e) => setForm({ ...form, password: e.target.value })}
                      className="mt-2 w-full px-3 py-2.5 border border-line bg-white text-sm focus:outline-none focus:border-ink"
                      data-testid="login-password-input"
                    />
                  </div>
                  <button type="submit" disabled={busy} data-testid="login-submit-btn"
                    className="btn w-full justify-center py-3 text-xs">
                    {busy ? "Signing in…" : "Sign in"}
                  </button>
                  <p className="text-[11px] text-ink-400 leading-relaxed">
                    Accounts created by an invitation activate on first Google sign-in. Email and
                    password is for administrators and for institutions that do not use Google.
                  </p>
                </form>
              )}
            </div>
          )}

          <p className="text-xs text-ink-400 mt-6 text-center leading-relaxed">
            Your workspace and permissions are determined automatically based on your account.
          </p>

          <div className="my-8 hairline" />

          <div className="text-center text-xs text-ink-500">
            Don't have access yet? Contact your institution's placement office.
          </div>
          <div className="mt-3 text-center text-xs text-ink-400">
            Onboarding a new institution?{" "}
            <Link to="/register" className="text-accent font-medium hover:underline" data-testid="register-link">
              Register here <ArrowUpRight size={10} className="inline" />
            </Link>
          </div>
        </div>
      </div>
    </main>
  );
}
