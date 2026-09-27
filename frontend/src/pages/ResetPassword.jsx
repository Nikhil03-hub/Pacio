import React, { useState } from "react";
import { useSearchParams, useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { toast } from "sonner";
import { KeyRound, Lock, ArrowLeft } from "lucide-react";

export default function ResetPassword() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get("token");
  const navigate = useNavigate();

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!token) {
      toast.error("Reset token is missing in the URL.");
      return;
    }
    if (password.length < 6) {
      toast.error("Password must be at least 6 characters.");
      return;
    }
    if (password !== confirmPassword) {
      toast.error("Passwords do not match.");
      return;
    }

    setBusy(true);
    try {
      await api.post("/auth/reset-password", { token, new_password: password });
      toast.success("Password reset successfully. Please log in.");
      navigate("/login");
    } catch (err) {
      toast.error(err.response?.data?.detail || "Failed to reset password.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-bone-100 flex flex-col items-center justify-center p-6 select-none">
      <div className="w-full max-w-[420px] editorial p-8 md:p-10 space-y-8 bg-white">
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="font-mono text-[10px] tracking-[0.28em] text-ink-400">§ SECURE RESET</div>
          <h1 className="font-display text-4xl tracking-tightest leading-none">
            Reset Your <span className="text-accent">Password</span>
          </h1>
          <p className="font-serif text-sm text-ink-500">
            Please enter your new password below.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            <div>
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">NEW PASSWORD</div>
              <div className="mt-2 flex items-center gap-2 border border-line px-3 py-2.5 bg-bone-50">
                <Lock size={14} className="text-ink-400" />
                <input
                  type="password"
                  placeholder="At least 6 characters"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={busy}
                  className="bg-transparent text-sm w-full focus:outline-none"
                  data-testid="reset-password-input"
                />
              </div>
            </div>

            <div>
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">CONFIRM PASSWORD</div>
              <div className="mt-2 flex items-center gap-2 border border-line px-3 py-2.5 bg-bone-50">
                <Lock size={14} className="text-ink-400" />
                <input
                  type="password"
                  placeholder="Repeat new password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                  disabled={busy}
                  className="bg-transparent text-sm w-full focus:outline-none"
                  data-testid="reset-confirm-input"
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={busy || !token}
            className="btn w-full py-3 flex items-center justify-center gap-2 font-mono text-[10px] tracking-[0.22em] uppercase"
            data-testid="reset-submit-btn"
          >
            <KeyRound size={14} />
            {busy ? "RESETTING…" : "RESET PASSWORD"}
          </button>
        </form>

        <div className="text-center pt-2">
          <button
            onClick={() => navigate("/login")}
            className="inline-flex items-center gap-1.5 text-xs text-ink-400 hover:text-ink-900 transition-colors font-mono tracking-wider"
          >
            <ArrowLeft size={12} /> BACK TO LOGIN
          </button>
        </div>
      </div>
    </div>
  );
}
