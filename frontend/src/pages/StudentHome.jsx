import React, { useEffect, useState, useRef } from "react";
import { api } from "../lib/api";
import { useAuth } from "../App";
import { Code2, TrendingUp, Award, Briefcase, ChevronRight, Eye, ShieldCheck, Copy } from "lucide-react";
import { Link } from "react-router-dom";
import { Badge, Progress, EmptyState } from "../components/Primitives";
import { PageTransition, DashboardReveal, CounterAnimation } from "../components/Motion";
import { toast } from "sonner";
import { renderCertificateToCanvas, CERTIFICATE_TYPES } from "../lib/certificateRenderer";
import { pdf } from "@react-pdf/renderer";
import { BulkCertificatesDocument } from "../components/BulkCertificates";

export default function StudentHome() {
  useAuth();
  const [d, setD] = useState(null);
  const [workspace, setWorkspace] = useState(null);
  const [showCertificate, setShowCertificate] = useState(false);
  const [selectedCertType, setSelectedCertType] = useState("CRT");
  const [isGenerating, setIsGenerating] = useState(false);
  const canvasRef = useRef(null);

  useEffect(() => {
    if (showCertificate && canvasRef.current && d?.student) {
      const student = d.student;
      const canvas = canvasRef.current;
      const collegeName = student.institution_id === "inst_kmit" ? "Keshav Memorial Institute of Technology" : (student.institution_id?.replace("inst_", "").toUpperCase() + " Engineering College");
      const certTypeData = CERTIFICATE_TYPES[selectedCertType];
      const certId = `ST-${selectedCertType}-${student.student_id?.slice(4, 10).toUpperCase() || "XXXX"}`;
      const dateStr = new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" });
      
      const certData = {
        title: certTypeData.title,
        description: certTypeData.description,
        studentName: student.name,
        rollNumber: student.roll_number,
        branch: student.department || "CSE",
        collegeName: collegeName,
        certId: certId,
        date: dateStr,
        signatureTpo: "Dr. Neil Gogte",
        signatureSkillTank: "Skill Tank Director"
      };
      
      renderCertificateToCanvas(canvas, certData);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showCertificate, selectedCertType, d]);

  const downloadPNG = () => {
    if (!canvasRef.current) return;
    const link = document.createElement("a");
    link.download = `${s.name.replace(/\s+/g, "_")}_${selectedCertType}_certificate.png`;
    link.href = canvasRef.current.toDataURL("image/png");
    link.click();
  };

  const downloadPDF = async () => {
    if (!canvasRef.current) return;
    setIsGenerating(true);
    try {
      const imgData = canvasRef.current.toDataURL("image/png");
      const docInstance = <BulkCertificatesDocument images={[imgData]} />;
      const blob = await pdf(docInstance).toBlob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${s.name.replace(/\s+/g, "_")}_${selectedCertType}_certificate.pdf`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      toast.error("Error generating PDF certificate");
      console.error(err);
    } finally {
      setIsGenerating(false);
    }
  };

  useEffect(() => {
    api.get("/me/dashboard").then(({ data }) => setD(data)).catch(() => {});
    api.get("/workspace/me").then(({ data }) => setWorkspace(data)).catch(() => {});
  }, []);

  if (!d) return <div className="font-mono text-xs text-ink-400 p-8">LOADING…</div>;

  const s = d.student;
  const solved = d.dsa.reduce((a, t) => a + t.solved, 0);
  const dsaPct = Math.round((solved / d.dsa_total) * 100);
  const aptAvg = d.aptitude.length ? Math.round(d.aptitude.reduce((a, x) => a + x.score_pct, 0) / d.aptitude.length) : 0;
  const intAvg = d.interviews.length ? Math.round(d.interviews.reduce((a, x) => a + x.overall_score, 0) / d.interviews.length) : 0;
  const engine = d.readiness_engine;
  const readiness = Math.round(engine?.score ?? s.readiness_score);
  const atsScore = Math.round(engine?.components?.ats?.score ?? d.ats?.score ?? s.ats_score);
  const interviewScore = Math.round(engine?.components?.interview?.score ?? intAvg);

  // Discoverability calculations
  const hasLinkedin = s.linkedin_url || workspace?.linkedin || false;
  const hasGithub = s.github_url || workspace?.github || false;
  const skillsList = s.skills || [];
  const discoverabilityScore = Math.min(
    100,
    Math.round(
      (atsScore * 0.4) + 
      (hasLinkedin ? 25 : 0) + 
      (hasGithub ? 20 : 0) + 
      (skillsList.length > 5 ? 15 : skillsList.length * 3)
    )
  );

  const missingKeywords = ["System Design", "REST API", "Docker", "CI/CD", "AWS", "Unit Testing"].filter(
    (k) => !skillsList.some((sk) => (typeof sk === "string" ? sk : sk.name || "").toLowerCase() === k.toLowerCase())
  );

  const templateHeadline = `${s.department || "Software"} Engineer | JavaScript | React | Python | Deployed Products`;

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success("Copied to clipboard!");
  };

  return (
    <PageTransition className="space-y-10">
      {/* Editorial hero */}
      <DashboardReveal className="grid grid-cols-12 gap-4">
        <div className="col-span-12 md:col-span-7 editorial p-10 lg:p-14 relative overflow-hidden dash-reveal">
          <div className="absolute -right-10 -top-10 font-display text-[20vw] leading-none text-bone-200 select-none pointer-events-none">
            {s.name[0]}
          </div>
          <div className="relative font-mono text-[10px] tracking-[0.28em] text-ink-400">§ YOUR WORKSPACE</div>
          <h1 className="relative font-display text-5xl md:text-6xl tracking-tightest mt-3 leading-[0.95]" data-testid="student-heading">
            Hi <span className="text-accent">{s.name.split(" ")[0]}</span>.<br />Let's get you placed.
          </h1>
          <p className="relative font-serif text-lg text-ink-500 mt-3 max-w-xl">
            {s.placement?.placed
              ? `Placed at ${s.placement.company} (₹${s.placement.ctc_lpa}L). Now help your peers.`
              : `${dsaPct}% DSA done · ATS ${atsScore} · ${engine?.label || "readiness"} ${readiness}/100. Keep going.`}
          </p>
          <div className="relative mt-6 flex flex-wrap gap-2">
            <Badge variant="solid">{s.roll_number}</Badge>
            <Badge variant="accent">{s.department}</Badge>
            <Badge>CGPA {s.cgpa}</Badge>
            <Badge>{s.batch}</Badge>
          </div>
        </div>

        <div className="col-span-12 md:col-span-5 editorial bg-ink text-bone p-10 lg:p-12 flex flex-col justify-between dash-reveal">
          <div>
            <div className="font-mono text-[10px] tracking-[0.28em] text-bone/45">READINESS SCORE</div>
            <div className="font-display text-[14vw] md:text-[10vw] tracking-tightest leading-[0.9] tnum text-accent">
              <CounterAnimation value={readiness} />
            </div>
            <div className="text-bone/60 text-sm font-sans mt-2">{engine?.label || "composite"} (CGPA · DSA · ATS · Interview)</div>
          </div>
          <div className="grid grid-cols-3 gap-4 mt-8 pt-4 border-t border-bone/10">
            {[
              { l: "DSA PROGRESS", v: `${dsaPct}%` },
              { l: "ATS SCORE", v: atsScore },
              { l: "INT SCORE", v: `${interviewScore}` },
            ].map((x) => (
              <div key={x.l}>
                <div className="font-mono text-[9px] text-bone/45 tracking-[0.18em]">{x.l}</div>
                <div className="font-display text-2xl mt-1.5 tnum">{x.v}</div>
              </div>
            ))}
          </div>
        </div>
      </DashboardReveal>

      {/* 4 module rings */}
      <DashboardReveal className="grid grid-cols-12 gap-4" data-testid="student-modules">
        {[
          { to: "/student/dsa", icon: Code2, label: "DSA tracker", primary: `${dsaPct}%`, sub: `${solved}/${d.dsa_total} solved`, key: "dsa" },
          { to: "/student/jobs", icon: Briefcase, label: "Open drives", primary: d.recommended_jobs.length, sub: "matching your profile", key: "jobs" },
          { to: "/student/applications", icon: TrendingUp, label: "Applications", primary: d.applications.length, sub: `${d.applications.filter(a => a.stage === "Interview").length} interviews`, key: "apps" },
          { to: "/student/aptitude", icon: Award, label: "Aptitude practice", primary: `${aptAvg}%`, sub: `${d.aptitude.length} sections`, key: "apt" },
        ].map((m) => (
          <Link key={m.key} to={m.to} className="col-span-12 md:col-span-3 editorial p-8 hover:border-ink transition-colors group dash-reveal" data-testid={`stmod-${m.key}`}>
            <div className="flex items-center justify-between text-ink-400">
              <div className="font-mono text-[10px] tracking-[0.24em] flex items-center gap-2">
                <m.icon size={14} /> {m.label.toUpperCase()}
              </div>
            </div>
            <div className="font-display text-5xl tracking-tightest mt-5 tnum group-hover:text-accent transition-colors">
              {m.primary}
            </div>
            <div className="text-sm text-ink-500 mt-2 font-serif">{m.sub}</div>
          </Link>
        ))}
      </DashboardReveal>

      {/* Discoverability Insights Bento Row */}
      <div className="grid grid-cols-12 gap-4">
        {/* Discoverability Card */}
        <div className="col-span-12 md:col-span-4 border border-line bg-paper p-8 flex flex-col justify-between">
          <div>
            <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 mb-2">RECRUITER VISIBILITY</div>
            <h3 className="font-display text-2xl tracking-tight mb-4 flex items-center gap-2">
              Discoverability Intel <Eye size={18} className="text-accent" />
            </h3>
            
            <div className="flex items-center gap-4">
              <div className="font-display text-5xl text-accent tnum">{discoverabilityScore}%</div>
              <div>
                <div className="text-xs font-mono tracking-widest text-ink-400">VISIBILITY STATUS</div>
                <div className="text-sm font-serif text-ink-700 mt-0.5">
                  {discoverabilityScore >= 80 ? "Highly Discoverable" : discoverabilityScore >= 50 ? "Visible with Gaps" : "Hidden Profile"}
                </div>
              </div>
            </div>
            <div className="h-1.5 bg-bone-200 mt-4 relative">
              <div className="absolute inset-y-0 left-0 bg-accent transition-all" style={{ width: `${discoverabilityScore}%` }} />
            </div>
          </div>
          
          <ul className="space-y-2 mt-6 text-xs font-mono text-ink-500">
            <li className="flex items-center gap-1.5">
              <span className={hasLinkedin ? "text-accent" : "text-ink-300"}>{hasLinkedin ? "✓" : "✗"}</span> LinkedIn URL configured
            </li>
            <li className="flex items-center gap-1.5">
              <span className={hasGithub ? "text-accent" : "text-ink-300"}>{hasGithub ? "✓" : "✗"}</span> GitHub Link configured
            </li>
            <li className="flex items-center gap-1.5">
              <span className={atsScore >= 75 ? "text-accent" : "text-ink-300"}>{atsScore >= 75 ? "✓" : "✗"}</span> ATS Score &gt;= 75
            </li>
          </ul>
        </div>

        {/* Missing Keywords & Headline Templates */}
        <div className="col-span-12 md:col-span-8 border border-line bg-bone-50 p-8 flex flex-col justify-between">
          <div>
            <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 mb-2">KEYWORD DELTA & HEADLINE TEMPLATE</div>
            <h3 className="font-display text-2xl tracking-tight mb-4 flex items-center gap-2">
              Optimize Search Signals <ShieldCheck size={18} className="text-accent" />
            </h3>
            
            {/* Template Headline */}
            <div className="p-4 border border-line bg-paper flex items-center justify-between gap-4">
              <div>
                <div className="font-mono text-[9px] text-ink-400 tracking-widest">RECOMMENDED PROFILE HEADLINE</div>
                <div className="font-mono text-xs text-ink-800 font-bold mt-1 leading-relaxed">
                  {templateHeadline}
                </div>
              </div>
              <button 
                onClick={() => copyToClipboard(templateHeadline)}
                className="p-2 border border-line hover:border-accent text-ink-500 hover:text-accent bg-bone-50"
                title="Copy Headline Template"
              >
                <Copy size={12} />
              </button>
            </div>

            {/* Missing Keywords */}
            <div className="mt-6">
              <div className="font-mono text-[9px] text-ink-400 tracking-widest mb-3">HIGH-DEMAND KEYWORD GAPS</div>
              <div className="flex flex-wrap gap-1.5">
                {missingKeywords.map((kw, idx) => (
                  <span key={idx} className="font-mono text-[9px] tracking-wider px-2 py-1 border border-line bg-paper text-ink-600">
                    + {kw.toUpperCase()}
                  </span>
                ))}
                {missingKeywords.length === 0 && (
                  <span className="font-serif text-xs text-ink-500">No missing high-demand keywords! Perfect matching.</span>
                )}
              </div>
            </div>
          </div>
          
          <p className="font-serif text-xs text-ink-400 leading-relaxed mt-6">
            Adding these keywords to your resume summary, project descriptions, and LinkedIn profile significantly increases your matching rate in recruiter searches.
          </p>
        </div>
      </div>

      {/* Decision queue */}
      {workspace?.actions?.length > 0 && (
        <DashboardReveal className="grid grid-cols-12 gap-4" data-testid="student-decision-queue">
          {workspace.actions.slice(0, 3).map((action, i) => (
            <Link key={action.label} to={action.to} className="col-span-12 md:col-span-4 editorial p-6 hover:border-ink transition-colors dash-reveal">
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">NEXT MOVE {String(i + 1).padStart(2, "0")}</div>
              <div className="font-display text-xl tracking-tight mt-3">{action.label}</div>
              <div className="text-sm text-ink-500 mt-2 font-serif">{action.reason}</div>
            </Link>
          ))}
        </DashboardReveal>
      )}

      {/* Certifications Widget */}
      <div className="editorial p-8 bg-paper border border-line">
        <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 mb-2">PARTNERSHIP CREDENTIALS</div>
        <h3 className="font-display text-2xl tracking-tight mb-3 flex items-center gap-2">
          Co-branded Certificates <Award size={18} className="text-accent" />
        </h3>
        <p className="font-serif text-sm text-ink-500 max-w-2xl leading-relaxed">
          Upon satisfying the baseline readiness parameters (DSA solve rate, Aptitude accuracy, and ATS benchmarks), you are eligible to generate your Placement Partner co-branded certificate.
        </p>
        <button
          onClick={() => setShowCertificate(true)}
          className="mt-5 btn bg-ink text-bone-100 hover:bg-ink-800 text-xs py-2 px-4"
        >
          View Certificate
        </button>
      </div>

      {/* DSA breakdown + Recommended jobs */}
      <div className="grid grid-cols-12 gap-4">
        <div className="col-span-12 md:col-span-7 editorial p-8" data-testid="student-dsa-panel">
          <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">YOUR DSA CURRICULUM · TOPIC PROGRESS</div>
          <h3 className="font-display text-2xl tracking-tight mt-1">Where you stand</h3>
          
          <div className="mt-6 grid grid-cols-2 md:grid-cols-3 gap-3">
            {d.dsa.slice(0, 9).map((t) => {
              const pct = Math.round((t.solved / t.total) * 100);
              return (
                <div key={t.topic_code} className="border border-line p-4 bg-bone-100/50">
                  <div className="font-mono text-[9px] tracking-[0.2] text-ink-400">{t.topic_code}</div>
                  <div className="font-display text-sm tracking-tight mt-1 truncate">{t.topic_name}</div>
                  <div className="font-display text-2xl mt-3 tnum">{t.solved}<span className="text-ink-400 text-sm font-light">/{t.total}</span></div>
                  <div className="mt-3">
                    <Progress value={pct} />
                  </div>
                </div>
              );
            })}
          </div>
          <Link to="/student/dsa" className="mt-6 inline-flex items-center gap-1.5 ink-link text-xs font-mono uppercase tracking-wider">
            Open full tracker <ChevronRight size={14} />
          </Link>
        </div>

        <div className="col-span-12 md:col-span-5 editorial p-8 bg-bone-100/40 flex flex-col">
          <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">RECOMMENDED FOR YOU</div>
          <h3 className="font-display text-2xl tracking-tight mt-1">Open drives</h3>
          <div className="mt-6 space-y-3 flex-1">
            {d.recommended_jobs.map((j, i) => (
              <div key={j.job_id} className="border border-line-strong p-4 bg-paper hover:border-ink transition-colors" data-testid={`rec-job-${i}`}>
                <div className="flex items-baseline justify-between gap-2">
                  <div className="font-display text-lg tracking-tight uppercase">{j.company}</div>
                  <div className="font-mono text-accent tnum text-sm">₹{j.ctc_lpa}LPA</div>
                </div>
                <div className="text-xs text-ink-500 font-serif mt-1">{j.title} · {j.location} · {j.openings} openings</div>
              </div>
            ))}
            {d.recommended_jobs.length === 0 && (
              <EmptyState title="No active drives matching" description="We will notify you as soon as a new recruitment drive is posted by partners." />
            )}
          </div>
        </div>
      </div>
      {showCertificate && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-ink/75 backdrop-blur-sm overflow-y-auto">
          <div className="relative max-w-4xl w-full border border-line bg-bone-50 p-6 md:p-8 shadow-2xl my-8">
            <button
              onClick={() => setShowCertificate(false)}
              className="absolute top-4 right-4 text-xs font-mono tracking-widest text-ink-400 hover:text-accent uppercase cursor-pointer"
            >
              [ Close ]
            </button>
            <div className="flex flex-col md:flex-row justify-between items-stretch gap-6 mt-4">
              <div className="w-full md:w-3/4 flex flex-col items-center">
                {/* Live Canvas Preview */}
                <div className="w-full border border-line bg-white p-2 shadow-sm">
                  <canvas ref={canvasRef} className="w-full h-auto max-h-[500px] object-contain" />
                </div>
              </div>
              <div className="w-full md:w-1/4 flex flex-col justify-between">
                <div className="space-y-5">
                  <div>
                    <div className="font-mono text-[9px] tracking-[0.2em] text-ink-400 uppercase">Credentialing</div>
                    <h4 className="font-display text-lg tracking-tight mt-1">Configure Certificate</h4>
                  </div>
                  <div className="space-y-2">
                    <label className="block text-xs font-mono text-ink-500 uppercase">Certificate Type</label>
                    <select
                      value={selectedCertType}
                      onChange={(e) => setSelectedCertType(e.target.value)}
                      className="w-full border border-line bg-bone-100 p-2 text-sm focus:outline-none"
                    >
                      <option value="CRT">CRT Certificate</option>
                      <option value="WORKSHOP">Workshop Certificate</option>
                      <option value="HACKATHON">Hackathon Certificate</option>
                      <option value="INTERNSHIP">Internship Certificate</option>
                      <option value="PLACEMENT">Placement Achievement</option>
                    </select>
                  </div>
                </div>
                <div className="pt-6 border-t border-line space-y-2 mt-6 md:mt-0">
                  <button
                    onClick={downloadPNG}
                    className="w-full btn bg-bone-100 border-line hover:bg-paper text-ink-900 text-xs py-2.5"
                  >
                    Download PNG
                  </button>
                  <button
                    onClick={downloadPDF}
                    disabled={isGenerating}
                    className="w-full btn bg-ink text-bone-100 hover:bg-ink-800 text-xs py-2.5 flex items-center justify-center gap-2"
                  >
                    {isGenerating ? "Generating..." : "Download PDF"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </PageTransition>
  );
}
