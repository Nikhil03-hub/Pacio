import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Search, Filter, Plus } from "lucide-react";
import { toast } from "sonner";
import { renderCertificateToCanvas, CERTIFICATE_TYPES } from "../lib/certificateRenderer";
import { pdf } from "@react-pdf/renderer";
import { BulkCertificatesDocument } from "../components/BulkCertificates";

export default function StudentRoster() {
  const [items, setItems] = useState([]);
  const [q, setQ] = useState("");
  const [dept, setDept] = useState("");
  const [placed, setPlaced] = useState("");
  const [adding, setAdding] = useState(false);
  const [newStudent, setNewStudent] = useState({ name: "", roll_number: "", department: "CSE", email: "", phone: "", cgpa: 7.5 });
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [journeyData, setJourneyData] = useState(null);
  const [loadingJourney, setLoadingJourney] = useState(false);

  const downloadSingleStudentCert = async (student, type) => {
    try {
      const canvas = document.createElement("canvas");
      const collegeName = student.college_name || (student.institution_id === "inst_kmit" ? "Keshav Memorial Institute of Technology" : student.institution_id?.replace("inst_", "").toUpperCase() + " Engineering College" || "Partner Institution");
      const certTypeData = CERTIFICATE_TYPES[type];
      const certId = `ST-${type}-${student.student_id?.slice(4, 10).toUpperCase() || "XXXX"}`;
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
      
      const imgUrl = await renderCertificateToCanvas(canvas, certData);
      const docInstance = <BulkCertificatesDocument images={[imgUrl]} />;
      const blob = await pdf(docInstance).toBlob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${student.name.replace(/\s+/g, "_")}_${type}_certificate.pdf`;
      link.click();
      URL.revokeObjectURL(url);
      toast.success("Certificate generated successfully!");
    } catch (err) {
      toast.error("Error generating certificate");
      console.error(err);
    }
  };

  const selectStudent = async (student) => {
    setSelectedStudent(student);
    setLoadingJourney(true);
    try {
      const { data } = await api.get(`/students/${student.student_id}`);
      setJourneyData(data);
    } catch {
      toast.error("Could not load journey data");
      setJourneyData(null);
    } finally {
      setLoadingJourney(false);
    }
  };

  const load = async () => {
    const params = {};
    if (q) params.q = q;
    if (dept) params.department = dept;
    if (placed) params.placed = placed === "yes";
    const { data } = await api.get("/students", { params });
    setItems(data.items);
  };

  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { load(); }, [dept, placed]);

  const submit = async (e) => {
    e.preventDefault();
    try {
      await api.post("/students", newStudent);
      toast.success("Student added");
      setAdding(false);
      setNewStudent({ name: "", roll_number: "", department: "CSE", email: "", phone: "", cgpa: 7.5 });
      load();
    } catch {
      toast.error("Could not add student");
    }
  };

  return (
    <div className="space-y-8">
      <div className="flex items-end justify-between">
        <div>
          <div className="num-mono text-[11px] tracking-[0.28em] text-ink-400">FEATURE · 03</div>
          <h1 className="font-display text-5xl md:text-6xl tracking-tightest mt-3">Student roster</h1>
          <p className="font-serif text-lg text-ink-500 mt-2">Every enrolled student, every batch. Filter, sort, and act.</p>
        </div>
        <button onClick={() => setAdding(true)} data-testid="add-student-btn" className="inline-flex items-center gap-2 bg-accent text-bone-100 px-5 py-3 text-sm hover:bg-accent-hover transition-colors">
          <Plus size={14} /> Add student
        </button>
      </div>

      {/* Filter bar */}
      <div className="border border-line bg-bone-50 p-4 flex flex-wrap items-center gap-3">
        <div className="flex items-center gap-2 flex-1 min-w-[260px] border border-line px-3 bg-bone-100">
          <Search size={14} className="text-ink-400" />
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && load()}
            placeholder="Search name or roll number…"
            data-testid="roster-search"
            className="bg-transparent w-full py-2 text-sm focus:outline-none"
          />
        </div>
        <select value={dept} onChange={(e) => setDept(e.target.value)} data-testid="roster-dept-filter" className="border border-line bg-bone-100 px-3 py-2 text-sm">
          <option value="">All departments</option>
          {["CSE", "IT", "CSE-AIML", "CSE-DS"].map((d) => <option key={d}>{d}</option>)}
        </select>
        <select value={placed} onChange={(e) => setPlaced(e.target.value)} data-testid="roster-placed-filter" className="border border-line bg-bone-100 px-3 py-2 text-sm">
          <option value="">All status</option>
          <option value="yes">Placed</option>
          <option value="no">Unplaced</option>
        </select>
        <button onClick={load} data-testid="roster-apply-btn" className="inline-flex items-center gap-2 bg-accent text-bone-100 px-4 py-2 text-sm hover:bg-accent-hover transition-colors">
          <Filter size={14} /> Apply
        </button>
        <span className="num-mono text-[11px] text-ink-400 tracking-[0.18em] ml-auto" data-testid="roster-count">{items.length} STUDENTS</span>
      </div>

      {adding && (
        <form onSubmit={submit} className="border border-line bg-bone-50 p-6 grid md:grid-cols-3 gap-3" data-testid="add-student-form">
          {[
            { k: "name", label: "Name" },
            { k: "roll_number", label: "Roll number" },
            { k: "email", label: "Email" },
            { k: "phone", label: "Phone" },
          ].map((f) => (
            <input key={f.k} required={f.k === "name"} placeholder={f.label} value={newStudent[f.k]}
              onChange={(e) => setNewStudent({ ...newStudent, [f.k]: e.target.value })}
              data-testid={`new-${f.k}`}
              className="px-3 py-2 border border-line bg-bone-100 text-sm focus:outline-none focus:border-ink-900"
            />
          ))}
          <select value={newStudent.department} onChange={(e) => setNewStudent({ ...newStudent, department: e.target.value })} data-testid="new-department" className="px-3 py-2 border border-line bg-bone-100 text-sm">
            {["CSE", "IT", "CSE-AIML", "CSE-DS"].map((d) => <option key={d}>{d}</option>)}
          </select>
          <input type="number" step="0.01" placeholder="CGPA" value={newStudent.cgpa} onChange={(e) => setNewStudent({ ...newStudent, cgpa: parseFloat(e.target.value) })} className="px-3 py-2 border border-line bg-bone-100 text-sm" />
          <div className="md:col-span-3 flex gap-3">
            <button type="submit" data-testid="save-student-btn" className="bg-accent text-bone-100 px-5 py-2 text-sm hover:bg-accent-hover">Save</button>
            <button type="button" onClick={() => setAdding(false)} className="border border-line px-5 py-2 text-sm">Cancel</button>
          </div>
        </form>
      )}

      {/* Table */}
      <div className="border border-line bg-bone-50 overflow-hidden">
        <div className="grid grid-cols-12 px-6 py-4 border-b border-line num-mono text-[10px] tracking-[0.24em] text-ink-400">
          <div className="col-span-3">STUDENT</div>
          <div className="col-span-2">ROLL</div>
          <div className="col-span-2">DEPT</div>
          <div className="col-span-1 text-center">CGPA</div>
          <div className="col-span-2">PLACEMENT</div>
          <div className="col-span-2 text-right">CTC</div>
        </div>
        {items.map((s, i) => (
          <div key={s.student_id} onClick={() => selectStudent(s)} className="grid grid-cols-12 px-6 py-4 border-b border-line items-center hover:bg-bone-200 transition-colors cursor-pointer" data-testid={`student-row-${i}`}>
            <div className="col-span-3">
              <div className="font-medium">{s.name}</div>
              <div className="text-xs text-ink-400">{s.email}</div>
            </div>
            <div className="col-span-2 num-mono text-sm">{s.roll_number}</div>
            <div className="col-span-2"><span className="pill bg-bone-100">{s.department}</span></div>
            <div className="col-span-1 text-center num-mono">{s.cgpa}</div>
            <div className="col-span-2">
              {s.placement?.placed ? (
                <span className="num-mono text-xs text-accent">● {s.placement.company}</span>
              ) : (
                <span className="num-mono text-xs text-ink-400">○ Open</span>
              )}
            </div>
            <div className="col-span-2 text-right num-mono">{s.placement?.placed ? `₹${s.placement.ctc_lpa?.toFixed(1)}L` : "—"}</div>
          </div>
        ))}
        {items.length === 0 && <div className="px-6 py-16 text-center text-ink-400">No students match these filters.</div>}
      </div>
      {selectedStudent && (
        <div className="fixed inset-0 z-50 flex justify-end bg-ink/75 backdrop-blur-xs">
          <div className="w-full max-w-md border-l border-line bg-bone-50 p-8 shadow-2xl overflow-y-auto flex flex-col h-full">
            <div className="flex justify-between items-center mb-6">
              <div>
                <div className="font-mono text-[9px] tracking-widest text-ink-400 uppercase">Student Placement Journey</div>
                <h3 className="font-display text-2xl tracking-tight mt-1">{selectedStudent.name}</h3>
                <div className="text-xs text-ink-500 font-mono mt-0.5">{selectedStudent.roll_number} · {selectedStudent.department}</div>
              </div>
              <button
                onClick={() => { setSelectedStudent(null); setJourneyData(null); }}
                className="text-xs font-mono tracking-wider text-ink-400 hover:text-accent uppercase"
              >
                [ CLOSE ]
              </button>
            </div>

            <div className="hairline mb-6" />

            {/* Certificate Generation Action */}
            <div className="border border-line bg-bone-100 p-4 mb-6">
              <div className="font-mono text-[9px] tracking-[0.2em] text-ink-400 uppercase mb-2">Generate Student Certificate</div>
              <div className="flex gap-2">
                <select
                  id="roster-cert-select"
                  className="flex-1 border border-line bg-bone-50 px-2 py-1 text-xs focus:outline-none"
                  defaultValue="CRT"
                >
                  <option value="CRT">CRT Certificate</option>
                  <option value="FDP">FDP Certificate</option>
                  <option value="WORKSHOP">Workshop Certificate</option>
                  <option value="HACKATHON">Hackathon Certificate</option>
                  <option value="INTERNSHIP">Internship Certificate</option>
                  <option value="PLACEMENT">Placement Achievement</option>
                </select>
                <button
                  onClick={async () => {
                    const sel = document.getElementById("roster-cert-select");
                    const type = sel ? sel.value : "CRT";
                    await downloadSingleStudentCert(selectedStudent, type);
                  }}
                  className="btn bg-ink text-bone-100 hover:bg-ink-800 text-[10px] py-1 px-3"
                >
                  Download PDF
                </button>
              </div>
            </div>

            {loadingJourney ? (
              <div className="font-mono text-xs text-ink-400">Loading placement journey…</div>
            ) : (
              <div className="space-y-6 flex-1">
                {(!journeyData || (
                  (journeyData.enrollments?.length || 0) +
                  (journeyData.resume_versions?.length || 0) +
                  (journeyData.interview_reports?.length || 0) +
                  (journeyData.applications?.length || 0)
                ) === 0) ? (
                  <div className="text-ink-400 text-sm font-serif">No placement journey events logged.</div>
                ) : (
                  <div className="relative border-l border-line pl-6 ml-2 space-y-8">
                    {[
                      ...(journeyData.enrollments || []).map(e => ({
                        date: e.enrolled_at,
                        title: "Enrolled in Program",
                        desc: `${e.program_name} (${e.program_code}) - Progress: ${e.completion_pct}%`,
                        type: "enroll"
                      })),
                      ...(journeyData.resume_versions || []).map(r => ({
                        date: r.created_at || r.updated_at,
                        title: "Resume Uploaded / Scored",
                        desc: `Version: ${r.version_id} - ATS Score: ${r.score || r.ats_score || 0}/100`,
                        type: "resume"
                      })),
                      ...(journeyData.interview_reports || []).map(i => ({
                        date: i.conducted_at,
                        title: `Mock Interview: ${i.type}`,
                        desc: `Communication: ${i.communication_score} · Tech: ${i.technical_score} · Overall: ${i.overall_score}%`,
                        type: "interview"
                      })),
                      ...(journeyData.applications || []).map(a => ({
                        date: a.applied_at,
                        title: `Applied to ${a.company}`,
                        desc: `Role: ${a.job_title} - Stage: ${a.stage}`,
                        type: "application"
                      })),
                      ...(journeyData.student?.placement?.placed && journeyData.student.placement.offer_date ? [{
                        date: journeyData.student.placement.offer_date,
                        title: `Offer Confirmed: ${journeyData.student.placement.company}`,
                        desc: `CTC: ₹${journeyData.student.placement.ctc_lpa}LPA`,
                        type: "offer"
                      }] : [])
                    ]
                      .sort((a, b) => new Date(b.date) - new Date(a.date))
                      .map((evt, idx) => (
                        <div key={idx} className="relative">
                          {/* Dot */}
                          <div className={`absolute -left-[31px] top-1.5 w-3 h-3 rounded-full border border-bone-50 ${
                            evt.type === 'offer' ? 'bg-accent' :
                            evt.type === 'application' ? 'bg-indigo-500' :
                            evt.type === 'interview' ? 'bg-emerald-500' :
                            evt.type === 'resume' ? 'bg-orange-500' : 'bg-ink'
                          }`} />
                          <div>
                            <div className="font-mono text-[9px] text-ink-400">{evt.date?.slice(0, 10)}</div>
                            <div className="font-display text-base tracking-tight font-semibold mt-1">{evt.title}</div>
                            <div className="text-xs text-ink-600 font-serif mt-1 leading-relaxed">{evt.desc}</div>
                          </div>
                        </div>
                      ))
                    }
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
