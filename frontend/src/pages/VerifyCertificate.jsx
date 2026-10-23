import React, { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { BadgeCheck, BadgeX, ShieldQuestion } from "lucide-react";
import { api } from "../lib/api";

const Row = ({ label, value }) => (
  <div className="flex items-baseline justify-between gap-6 border-b border-line py-3 last:border-0">
    <span className="font-mono text-[10px] tracking-[0.24em] text-ink-400 uppercase">{label}</span>
    <span className="font-display text-base tracking-tight text-ink-900 text-right">{value || "—"}</span>
  </div>
);

export default function VerifyCertificate() {
  const { certId } = useParams();
  const [state, setState] = useState({ status: "loading", data: null });

  useEffect(() => {
    let alive = true;
    api.get(`/certificates/verify/${encodeURIComponent(certId)}`)
      .then(({ data }) => alive && setState({ status: "done", data }))
      .catch(() => alive && setState({ status: "error", data: null }));
    return () => { alive = false; };
  }, [certId]);

  const verdict = state.status === "error"
    ? { icon: ShieldQuestion, tone: "text-ink-400", title: "Verification unavailable", body: "The verification service could not be reached. Try again shortly." }
    : state.status === "loading"
      ? { icon: ShieldQuestion, tone: "text-ink-400", title: "Checking…", body: "" }
      : state.data?.valid
        ? { icon: BadgeCheck, tone: "text-moss", title: "Certificate is valid", body: "This record was issued through the placement platform." }
        : { icon: BadgeX, tone: "text-rust", title: "Not verified", body: "No certificate with this ID has been issued. Ask the institution's placement office." };

  const Icon = verdict.icon;

  return (
    <main className="min-h-screen bg-bone-100 grain flex items-center justify-center p-6">
      <div className="w-full max-w-[560px] editorial bg-bone-50 p-8 md:p-10">
        <div className="flex items-start gap-4">
          <Icon size={30} className={verdict.tone} aria-hidden="true" />
          <div>
            <div className="font-mono text-[10px] tracking-[0.28em] text-ink-400 uppercase">CERTIFICATE VERIFY</div>
            <h1 className="font-display text-3xl md:text-4xl tracking-tightest mt-2" data-testid="verify-heading">
              {verdict.title}
            </h1>
            {verdict.body && <p className="font-serif text-sm text-ink-500 mt-3">{verdict.body}</p>}
          </div>
        </div>

        <div className="mt-8">
          <Row label="Certificate ID" value={certId} />
          {state.data?.valid && (
            <>
              <Row label="Issued to" value={state.data.holder} />
              <Row label="Program" value={state.data.program} />
              <Row label="Department" value={state.data.department} />
              <Row label="Institution" value={state.data.institution} />
              <Row label="Issued on" value={state.data.issued_on} />
            </>
          )}
        </div>

        <div className="mt-8 flex items-center justify-between gap-4">
          <Link to="/" className="font-mono text-[10px] tracking-[0.24em] text-ink-400 ink-link uppercase">Home</Link>
          <span className="font-mono text-[9px] tracking-[0.2em] text-ink-400 uppercase">Checked {new Date().toLocaleDateString("en-IN")}</span>
        </div>
      </div>
    </main>
  );
}
