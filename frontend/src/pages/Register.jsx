import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../lib/api";
import { toast } from "sonner";
import { User, Mail, Lock, Building, GraduationCap, Briefcase } from "lucide-react";

const ROLES = [
  { id: "student", label: "Student", icon: GraduationCap },
  { id: "faculty", label: "Faculty", icon: User },
  { id: "recruiter", label: "Recruiter", icon: Briefcase },
  { id: "tpo", label: "TPO / Institution", icon: Building },
];

export default function Register() {
  const navigate = useNavigate();
  const [role, setRole] = useState("student");
  const [institutions, setInstitutions] = useState([]);
  
  // Form fields
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rollNumber, setRollNumber] = useState("");
  const [department, setDepartment] = useState("");
  const [institutionId, setInstitutionId] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [collegeName, setCollegeName] = useState("");
  const [university, setUniversity] = useState("");
  const [partnershipType, setPartnershipType] = useState("CRT");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (["student", "faculty"].includes(role)) {
      api.get("/public/institutions")
        .then(({ data }) => {
          setInstitutions(data.items || []);
          if (data.items?.length > 0) {
            setInstitutionId(data.items[0].institution_id);
          }
        })
        .catch(() => setInstitutions([]));
    }
  }, [role]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!name || !email || !password) {
      toast.error("Please fill in all basic fields.");
      return;
    }

    const payload = {
      role,
      name,
      email,
      password,
    };

    if (role === "student") {
      payload.institution_id = institutionId;
      payload.department = department || "CSE";
      payload.roll_number = rollNumber;
    } else if (role === "faculty") {
      payload.institution_id = institutionId;
      payload.department = department;
    } else if (role === "recruiter") {
      payload.company_name = companyName;
    } else if (role === "tpo") {
      payload.college_name = collegeName;
      payload.affiliated_university = university;
      payload.partnership_type = partnershipType;
      payload.department = department;
    }

    setBusy(true);
    try {
      const { data } = await api.post("/auth/register", payload);
      if (data.status === "approved") {
        toast.success("Registration successful and approved!");
        // Store session token and redirect
        localStorage.setItem("user", JSON.stringify(data.user));
        // Force app reload or state update
        window.location.href = "/app";
      } else {
        toast.success("Registration successful. Pending administrator approval.");
        navigate("/pending");
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || "Registration failed.");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-bone-100 flex flex-col items-center justify-center p-6 select-none">
      <div className="w-full max-w-[500px] editorial p-8 md:p-10 space-y-8 bg-white">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="font-mono text-[10px] tracking-[0.28em] text-ink-400">§ REGISTRATION</div>
          <h1 className="font-display text-4xl tracking-tightest leading-none">
            Create <span className="text-accent">Account</span>
          </h1>
          <p className="font-serif text-sm text-ink-500">
            Join the CareerOS Campus Intelligence network.
          </p>
        </div>

        {/* Role Selector Tabs */}
        <div className="grid grid-cols-4 gap-1.5 border-b border-line pb-4" data-testid="register-tabs">
          {ROLES.map((r) => {
            const Icon = r.icon;
            const active = role === r.id;
            return (
              <button
                key={r.id}
                type="button"
                onClick={() => setRole(r.id)}
                className={`py-2 flex flex-col items-center gap-1.5 border transition-colors text-[9px] font-mono tracking-wider uppercase ${
                  active
                    ? "border-ink-900 bg-ink-900 text-bone-100"
                    : "border-line text-ink-500 hover:text-ink-900 bg-bone-50"
                }`}
              >
                <Icon size={14} />
                <span>{r.label}</span>
              </button>
            );
          })}
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-4">
            
            {/* Common Fields */}
            <div>
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">NAME</div>
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
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">EMAIL ADDRESS</div>
              <div className="mt-2 flex items-center gap-2 border border-line px-3 py-2 bg-bone-50">
                <Mail size={14} className="text-ink-400" />
                <input
                  type="email"
                  placeholder="name@institution.edu"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  disabled={busy}
                  className="bg-transparent text-sm w-full focus:outline-none"
                  data-testid="register-email-input"
                />
              </div>
            </div>

            <div>
              <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">PASSWORD</div>
              <div className="mt-2 flex items-center gap-2 border border-line px-3 py-2 bg-bone-50">
                <Lock size={14} className="text-ink-400" />
                <input
                  type="password"
                  placeholder="Choose secure password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={busy}
                  className="bg-transparent text-sm w-full focus:outline-none"
                  data-testid="register-password-input"
                />
              </div>
            </div>

            {/* Student Specific */}
            {role === "student" && (
              <>
                <div>
                  <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">SELECT INSTITUTION</div>
                  <select
                    value={institutionId}
                    onChange={(e) => setInstitutionId(e.target.value)}
                    className="mt-2 w-full px-3 py-2 border border-line bg-bone-50 text-sm focus:outline-none"
                    data-testid="register-student-inst"
                  >
                    {institutions.map((i) => (
                      <option key={i.institution_id} value={i.institution_id}>
                        {i.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">DEPARTMENT</div>
                  <input
                    type="text"
                    placeholder="e.g. CSE, ECE"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    required
                    disabled={busy}
                    className="mt-2 w-full px-3 py-2 border border-line bg-bone-50 text-sm focus:outline-none"
                    data-testid="register-student-dept"
                  />
                </div>
                <div>
                  <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">ROLL NUMBER</div>
                  <input
                    type="text"
                    placeholder="e.g. 21KMIT0501"
                    value={rollNumber}
                    onChange={(e) => setRollNumber(e.target.value)}
                    required
                    disabled={busy}
                    className="mt-2 w-full px-3 py-2 border border-line bg-bone-50 text-sm focus:outline-none"
                    data-testid="register-student-roll"
                  />
                </div>
              </>
            )}

            {/* Faculty Specific */}
            {role === "faculty" && (
              <>
                <div>
                  <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">SELECT INSTITUTION</div>
                  <select
                    value={institutionId}
                    onChange={(e) => setInstitutionId(e.target.value)}
                    className="mt-2 w-full px-3 py-2 border border-line bg-bone-50 text-sm focus:outline-none"
                    data-testid="register-faculty-inst"
                  >
                    {institutions.map((i) => (
                      <option key={i.institution_id} value={i.institution_id}>
                        {i.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div>
                  <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">DEPARTMENT</div>
                  <input
                    type="text"
                    placeholder="e.g. CSE, ECE"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    required
                    disabled={busy}
                    className="mt-2 w-full px-3 py-2 border border-line bg-bone-50 text-sm focus:outline-none"
                    data-testid="register-faculty-dept"
                  />
                </div>
              </>
            )}

            {/* Recruiter Specific */}
            {role === "recruiter" && (
              <div>
                <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">COMPANY NAME</div>
                <div className="mt-2 flex items-center gap-2 border border-line px-3 py-2 bg-bone-50">
                  <Building size={14} className="text-ink-400" />
                  <input
                    type="text"
                    placeholder="e.g. Google, Amazon"
                    value={companyName}
                    onChange={(e) => setCompanyName(e.target.value)}
                    required
                    disabled={busy}
                    className="bg-transparent text-sm w-full focus:outline-none"
                    data-testid="register-recruiter-company"
                  />
                </div>
              </div>
            )}

            {/* TPO Specific */}
            {role === "tpo" && (
              <>
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
              </>
            )}

          </div>

          <button
            type="submit"
            disabled={busy}
            className="btn w-full py-3 flex items-center justify-center gap-2 font-mono text-[10px] tracking-[0.22em] uppercase"
            data-testid="register-submit-btn"
          >
            <Building size={14} />
            {busy ? "REGISTERING…" : "CREATE ACCOUNT"}
          </button>
        </form>

        <div className="text-center pt-2">
          <button
            onClick={() => navigate("/login")}
            className="inline-flex items-center gap-1 text-xs text-ink-400 hover:text-ink-900 transition-colors font-mono tracking-wider"
          >
            ALREADY REGISTERED? LOG IN
          </button>
        </div>
      </div>
    </div>
  );
}
