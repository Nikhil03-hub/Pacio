import React, { createContext, useContext, useEffect, useState } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { Toaster } from "sonner";
import { api } from "./lib/api";

// Pages
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import OnboardingPending from "./pages/OnboardingPending";
import VerifyCertificate from "./pages/VerifyCertificate";

// Role layouts + homes
import RoleLayout from "./layouts/RoleLayout";
import { roleConfig } from "./layouts/roleConfig";

// Shared / module pages
import Overview from "./pages/Overview";
import Roster from "./pages/StudentRoster";
import Cohorts from "./pages/Cohorts";
import Training from "./pages/Training";
import MOU from "./pages/MOU";
import CollegeProfile from "./pages/CollegeProfile";
import AdminPanel from "./pages/AdminPanel";
import DSAIntelligence from "./pages/DSAIntelligence";
import AptitudeIntelligence from "./pages/AptitudeIntelligence";
import ATSIntelligence from "./pages/ATSIntelligence";
import InterviewIntelligence from "./pages/InterviewIntelligence";
import Applications from "./pages/Applications";
import Jobs from "./pages/Jobs";
import Recruiters from "./pages/Recruiters";
import Announcements from "./pages/Announcements";
import PlatformControl from "./pages/PlatformControl";
import Reports from "./pages/Reports";
import AnalyticsWorkbench from "./pages/AnalyticsWorkbench";
import InterviewSchedule from "./pages/InterviewSchedule";
import TeamInvites from "./pages/TeamInvites";
import RecruiterHome from "./pages/RecruiterHome";
import TalentPool from "./pages/TalentPool";
import StudentHome from "./pages/StudentHome";
import StudentDSA from "./pages/StudentDSA";
import StudentDSAProblem from "./pages/StudentDSAProblem";
import StudentAptitude from "./pages/StudentAptitude";
import StudentATS from "./pages/StudentATS";
import StudentInterviews from "./pages/StudentInterviews";
import PlacementIntelligence from "./pages/PlacementIntelligence";
import RecruiterAnalytics from "./pages/RecruiterAnalytics";
import ResetPassword from "./pages/ResetPassword";
import Register from "./pages/Register";
import FDPManagement from "./pages/FDPManagement";
import CommLog from "./pages/CommLog";
import Revenue from "./pages/Revenue";
import StudentResume from "./pages/StudentResume";
import StudentSkillGap from "./pages/StudentSkillGap";
import StudentCareer from "./pages/StudentCareer";
import StudentAIAnalysis from "./pages/StudentAIAnalysis";
import WorkshopRequests from "./pages/WorkshopRequests";
import PartnerBenchmarking from "./pages/PartnerBenchmarking";
import PartnerChat from "./pages/PartnerChat";

const AuthCtx = createContext(null);
export const useAuth = () => useContext(AuthCtx);
const USER_CACHE_KEY = "careeros_user";

function readCachedUser() {
  try {
    const raw = window.localStorage.getItem(USER_CACHE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function AuthProvider({ children }) {
  const [user, setUserState] = useState(() => readCachedUser());
  const [loading, setLoading] = useState(() => !readCachedUser());
  const setUser = (next) => {
    setUserState(next);
    try {
      if (next) window.localStorage.setItem(USER_CACHE_KEY, JSON.stringify(next));
      else window.localStorage.removeItem(USER_CACHE_KEY);
    } catch {
      // Token/cookie auth still work when storage is unavailable.
    }
  };
  const refresh = async () => {
    try { const { data } = await api.get("/auth/me"); setUser(data); }
    catch { setUser(null); }
    finally { setLoading(false); }
  };
  useEffect(() => {
    refresh();
    // eslint-disable-next-line
  }, []);
  return <AuthCtx.Provider value={{ user, setUser, loading, refresh }}>{children}</AuthCtx.Provider>;
}

const ROLE_HOME = {
  super_admin: "/platform",
  institution_admin: "/institution",
  tpo: "/tpo",
  faculty: "/faculty",
  student: "/student",
  recruiter: "/recruiter",
};

function Protected({ children, allow }) {
  const { user, loading } = useAuth();
  const loc = useLocation();
  if (loading) return <div className="min-h-screen flex items-center justify-center font-mono text-xs tracking-[0.3em] text-ink-400">LOADING ·</div>;
  if (!user) return <Navigate to="/login" state={{ from: loc }} replace />;
  if (!user.approved && user.role !== "super_admin") return <Navigate to="/pending" replace />;
  if (allow && !allow.includes(user.role)) return <Navigate to={ROLE_HOME[user.role] || "/"} replace />;
  return children;
}

function RoleRedirect() {
  const { user, loading } = useAuth();
  if (loading) return null;
  if (!user) return <Navigate to="/login" replace />;
  if (!user.approved && user.role !== "super_admin") return <Navigate to="/pending" replace />;
  return <Navigate to={ROLE_HOME[user.role] || "/"} replace />;
}

function AppRouter() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/pending" element={<OnboardingPending />} />
      <Route path="/app" element={<RoleRedirect />} />
      <Route path="/reset-password" element={<ResetPassword />} />
      <Route path="/register" element={<Register />} />
      {/* Public certificate verification - the code printed on every certificate. */}
      <Route path="/verify/:certId" element={<VerifyCertificate />} />

      {/* ===== PLATFORM (super admin) ===== */}
      <Route path="/platform" element={<Protected allow={["super_admin"]}><RoleLayout {...roleConfig.super_admin} /></Protected>}>
        <Route index element={<PlatformControl />} />
        <Route path="institutions" element={<AdminPanel />} />
        <Route path="recruiters" element={<Recruiters />} />
        <Route path="analytics" element={<AnalyticsWorkbench />} />
        <Route path="placements" element={<PlacementIntelligence />} />
        <Route path="announcements" element={<Announcements />} />
        <Route path="mou" element={<MOU />} />
        <Route path="fdp" element={<FDPManagement />} />
        <Route path="revenue" element={<Revenue />} />
        <Route path="reports" element={<Reports />} />
        <Route path="comm-log" element={<CommLog />} />
        <Route path="partner-chat" element={<PartnerChat />} />
        <Route path="workshops" element={<WorkshopRequests />} />
        <Route path="benchmarking" element={<PartnerBenchmarking />} />
        <Route path="team" element={<TeamInvites />} />
      </Route>

      {/* ===== INSTITUTION ADMIN ===== */}
      <Route path="/institution" element={<Protected allow={["institution_admin", "super_admin"]}><RoleLayout {...roleConfig.institution_admin} /></Protected>}>
        <Route index element={<Overview />} />
        <Route path="profile" element={<CollegeProfile />} />
        <Route path="departments" element={<Roster />} />
        <Route path="programs" element={<Cohorts />} />
        <Route path="analytics" element={<AnalyticsWorkbench />} />
        <Route path="outcomes" element={<PlacementIntelligence />} />
        <Route path="dsa" element={<DSAIntelligence />} />
        <Route path="aptitude" element={<AptitudeIntelligence />} />
        <Route path="ats" element={<ATSIntelligence />} />
        <Route path="interviews" element={<InterviewIntelligence />} />
        <Route path="team" element={<TeamInvites />} />
        <Route path="mou" element={<MOU />} />
        <Route path="reports" element={<Reports />} />
        <Route path="announcements" element={<Announcements />} />
        <Route path="fdp" element={<FDPManagement />} />
        <Route path="revenue" element={<Revenue />} />
        <Route path="partner-chat" element={<PartnerChat />} />
        <Route path="workshops" element={<WorkshopRequests />} />
        <Route path="benchmarking" element={<PartnerBenchmarking />} />
      </Route>

      {/* ===== TPO ===== */}
      <Route path="/tpo" element={<Protected allow={["tpo", "super_admin"]}><RoleLayout {...roleConfig.tpo} /></Protected>}>
        <Route index element={<Overview />} />
        <Route path="roster" element={<Roster />} />
        <Route path="cohorts" element={<Cohorts />} />
        <Route path="outcomes" element={<PlacementIntelligence />} />
        <Route path="analytics" element={<AnalyticsWorkbench />} />
        <Route path="training" element={<Training />} />
        <Route path="dsa" element={<DSAIntelligence />} />
        <Route path="aptitude" element={<AptitudeIntelligence />} />
        <Route path="ats" element={<ATSIntelligence />} />
        <Route path="interviews" element={<InterviewIntelligence />} />
        <Route path="schedule" element={<InterviewSchedule />} />
        <Route path="applications" element={<Applications />} />
        <Route path="jobs" element={<Jobs />} />
        <Route path="recruiters" element={<Recruiters />} />
        <Route path="team" element={<TeamInvites />} />
        <Route path="reports" element={<Reports />} />
        <Route path="mou" element={<MOU />} />
        <Route path="announcements" element={<Announcements />} />
        <Route path="fdp" element={<FDPManagement />} />
        <Route path="comm-log" element={<CommLog />} />
        <Route path="revenue" element={<Revenue />} />
        <Route path="partner-chat" element={<PartnerChat />} />
        <Route path="workshops" element={<WorkshopRequests />} />
        <Route path="benchmarking" element={<PartnerBenchmarking />} />
      </Route>

      {/* ===== FACULTY ===== */}
      <Route path="/faculty" element={<Protected allow={["faculty", "super_admin"]}><RoleLayout {...roleConfig.faculty} /></Protected>}>
        <Route index element={<Overview />} />
        <Route path="roster" element={<Roster />} />
        <Route path="analytics" element={<AnalyticsWorkbench />} />
        <Route path="dsa" element={<DSAIntelligence />} />
        <Route path="aptitude" element={<AptitudeIntelligence />} />
        <Route path="ats" element={<ATSIntelligence />} />
        <Route path="training" element={<Training />} />
        <Route path="interviews" element={<InterviewIntelligence />} />
        <Route path="fdp" element={<FDPManagement />} />
        <Route path="workshops" element={<WorkshopRequests />} />
        <Route path="benchmarking" element={<PartnerBenchmarking />} />
      </Route>

      {/* ===== STUDENT ===== */}
      <Route path="/student" element={<Protected allow={["student"]}><RoleLayout {...roleConfig.student} /></Protected>}>
        <Route index element={<StudentHome />} />
        <Route path="dsa" element={<StudentDSA />} />
        <Route path="dsa/:questionId" element={<StudentDSAProblem />} />
        <Route path="aptitude" element={<StudentAptitude />} />
        <Route path="ats" element={<StudentATS />} />
        <Route path="interviews" element={<StudentInterviews />} />
        <Route path="applications" element={<Applications />} />
        <Route path="jobs" element={<Jobs />} />
        <Route path="schedule" element={<InterviewSchedule />} />
        <Route path="announcements" element={<Announcements />} />
        <Route path="resume" element={<StudentResume />} />
        <Route path="skill-gap" element={<StudentSkillGap />} />
        <Route path="ai-analysis" element={<StudentAIAnalysis />} />
        <Route path="career" element={<StudentCareer />} />
      </Route>

      {/* ===== RECRUITER ===== */}
      <Route path="/recruiter" element={<Protected allow={["recruiter", "super_admin"]}><RoleLayout {...roleConfig.recruiter} /></Protected>}>
        <Route index element={<RecruiterHome />} />
        <Route path="jobs" element={<Jobs />} />
        <Route path="talent" element={<TalentPool />} />
        <Route path="schedule" element={<InterviewSchedule />} />
        <Route path="applications" element={<Applications />} />
        <Route path="analytics" element={<RecruiterAnalytics />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <Toaster position="top-right" theme="light" toastOptions={{ style: { borderRadius: 0, border: "1px solid rgba(10,10,10,0.18)", fontFamily: "Satoshi, system-ui" } }} />
      <AppRouter />
    </AuthProvider>
  );
}
