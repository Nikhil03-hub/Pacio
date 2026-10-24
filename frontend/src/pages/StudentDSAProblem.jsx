import React, { useCallback, useEffect, useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import Editor from "@monaco-editor/react";
import { api } from "../lib/api";
import { Badge, Button, Progress, Select, Textarea, Input } from "../components/Primitives";
import { ChevronLeft, ChevronRight, Play, Send } from "lucide-react";
import { toast } from "sonner";

const starter = {
  python: "def solve():\n    pass\n\nsolve()\n",
  javascript: "function solve() {\n  return null;\n}\n\nconsole.log(solve());\n",
  java: "public class Main {\n  public static void main(String[] args) {\n    // write code here\n  }\n}\n",
  cpp: "#include <bits/stdc++.h>\nusing namespace std;\n\nint main() {\n  return 0;\n}\n",
};

export default function StudentDSAProblem() {
  const { questionId } = useParams();
  const navigate = useNavigate();
  const [payload, setPayload] = useState(null);
  const [attempts, setAttempts] = useState([]);
  const [language, setLanguage] = useState("python");
  const [code, setCode] = useState(starter.python);
  const [customInput, setCustomInput] = useState("");
  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(false);

  // Tabbed sidebar states
  const [activeTab, setActiveTab] = useState("description"); // "description", "log", "submissions", "comments"
  const [comments, setComments] = useState([]);
  const [loadingComments, setLoadingComments] = useState(false);

  // Manual attempt logging states
  const [formStatus, setFormStatus] = useState("attempted");
  const [formTimeTaken, setFormTimeTaken] = useState("");
  const [formLanguage, setFormLanguage] = useState("");
  const [formApproach, setFormApproach] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [submittingAttempt, setSubmittingAttempt] = useState(false);

  const load = useCallback(async () => {
    const { data } = await api.get("/me/dsa/questions");
    setPayload(data);
    const studentId = data.student_id;
    if (studentId) {
      setLoadingComments(true);
      try {
        const [attemptsRes, commentsRes] = await Promise.all([
          api.get(`/dsa/student/${studentId}/attempts?question_id=${questionId}`),
          api.get(`/dsa/student/${studentId}/comments`),
        ]);
        setAttempts(attemptsRes.data.attempts || []);
        const questionComments = (commentsRes.data?.comments || []).filter(
          (c) => c.question_id === questionId
        );
        setComments(questionComments);
      } catch (err) {
        console.error(err);
      } finally {
        setLoadingComments(false);
      }
    }
  }, [questionId]);

  useEffect(() => { load(); }, [load]);

  const question = useMemo(() => (payload?.questions || []).find((row) => row.question_id === questionId), [payload, questionId]);
  const index = useMemo(() => (payload?.questions || []).findIndex((row) => row.question_id === questionId), [payload, questionId]);
  const prev = index > 0 ? payload.questions[index - 1] : null;
  const next = index >= 0 && index < (payload?.questions || []).length - 1 ? payload.questions[index + 1] : null;

  const changeLanguage = (value) => {
    setLanguage(value);
    setCode(starter[value] || starter.python);
  };

  const execute = async (kind) => {
    if (!question) return;
    setRunning(true);
    try {
      const endpoint = kind === "submit" ? "/me/dsa/submissions/submit" : "/me/dsa/submissions/run";
      const { data } = await api.post(endpoint, {
        question_id: question.question_id,
        language,
        code,
        custom_input: customInput,
      });
      setResult(data.result || data);
      await load();
      toast.success(kind === "submit" ? "Code submitted" : "Code executed");
    } catch (err) {
      setResult({ status: "Error", errors: err?.response?.data?.detail || "Execution failed" });
    } finally {
      setRunning(false);
    }
  };

  const submitAttempt = async (e) => {
    e.preventDefault();
    const studentId = payload?.student_id;
    if (!question || !studentId) return;
    setSubmittingAttempt(true);
    try {
      const qid = question.question_id;

      // 1. POST new attempt
      await api.post(`/dsa/student/${studentId}/attempt`, {
        question_id: qid,
        status: formStatus,
        time_taken: formTimeTaken ? parseInt(formTimeTaken, 10) : null,
        language: formLanguage,
        approach: formApproach,
        notes: formNotes,
      });

      // 2. PATCH question solved status
      await api.patch(`/me/dsa/questions/${qid}`, {
        solved: formStatus === "solved",
        attempted: true,
        mastery: formStatus === "solved" ? 85 : 35,
        notes: formNotes,
      });

      setFormTimeTaken("");
      setFormApproach("");
      setFormNotes("");

      toast.success("Attempt logged successfully!");
      await load();
    } catch (err) {
      toast.error("Failed to log attempt");
      console.error(err);
    } finally {
      setSubmittingAttempt(false);
    }
  };

  if (!payload || !question) return <div className="p-8 font-mono text-xs text-ink-400">LOADING PROBLEM...</div>;

  return (
    <div className="min-h-screen bg-bone text-ink">
      <div className="border-b border-line bg-paper px-6 py-4 flex items-center justify-between">
        <Link to="/student/dsa" className="btn px-4 py-2 text-xs"><ChevronLeft size={14} /> Back to sheet</Link>
        <div className="font-mono text-xs text-ink-400">{index + 1} / {payload.total}</div>
      </div>

      <div className="grid grid-cols-12 min-h-[calc(100vh-65px)]">
        <aside className="col-span-12 lg:col-span-4 border-r border-line bg-paper flex flex-col h-full overflow-hidden">
          {/* LeetCode-Style Sidebar Tab Selector */}
          <div className="flex border-b border-line bg-bone-100 p-0.5 gap-0.5">
            {["description", "log attempt", "submissions", "comments"].map((tab) => {
              const id = tab.split(" ")[0];
              return (
                <button
                  key={id}
                  onClick={() => setActiveTab(id)}
                  className={`flex-1 py-2 text-[9px] font-mono uppercase tracking-wider transition-all text-center border border-transparent ${
                    activeTab === id
                      ? "bg-paper text-ink font-semibold border-line"
                      : "text-ink/65 hover:bg-bone-200"
                  }`}
                >
                  {tab}
                </button>
              );
            })}
          </div>

          <div className="p-6 overflow-y-auto flex-1">
            {/* 1. Description Tab */}
            {activeTab === "description" && (
              <div className="space-y-6 animate-fade-in">
                <div>
                  <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">{question.topic_code}</div>
                  <h1 className="font-display text-4xl tracking-tight mt-3">{question.title}</h1>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <Badge variant="solid">{question.difficulty}</Badge>
                    <Badge variant={question.solved ? "success" : "warning"}>{question.solved ? "Solved" : "Unsolved"}</Badge>
                    <Badge variant="outline">{question.subtopic_name}</Badge>
                  </div>
                </div>

                <div className="border-t border-b border-line py-5">
                  <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 mb-2 uppercase font-semibold">Problem Description</div>
                  <p className="font-serif text-sm text-ink-800 leading-relaxed whitespace-pre-line">
                    {question.prompt || "No problem statement has been written for this entry yet."}
                  </p>
                  <p className="mt-4 font-serif text-sm text-ink-600 leading-relaxed">
                    {question.gradable
                      ? "This problem has a validated test specification, but the app still cannot execute your code. "
                      : "This problem has no validated test specification yet, so it cannot be graded at all. "}
                    Solve it in the Monaco editor and submit your approach. Pacio does not compile or run submitted code in this build, so a submission is recorded as an attempt with a static review of its structure - it is not graded, does not mark the problem solved, and does not change your placement metrics.
                  </p>
                  {question.why_it_matters && (
                    <div className="mt-4 border-l-2 border-accent pl-3">
                      <div className="font-mono text-[10px] uppercase tracking-[0.18em] text-ink-400">Why this is asked</div>
                      <p className="mt-1 font-serif text-sm text-ink-600 leading-relaxed">{question.why_it_matters}</p>
                    </div>
                  )}
                </div>

                <div>
                  <div className="flex justify-between text-sm">
                    <span className="font-mono text-xs uppercase tracking-wider text-ink-400">Mastery Score</span>
                    <span className="font-display text-accent font-semibold">{question.mastery || 0}%</span>
                  </div>
                  <Progress value={question.mastery || 0} className="mt-2" />
                </div>

                <div className="grid grid-cols-2 gap-3 pt-4 border-t border-line/60">
                  <button disabled={!prev} onClick={() => navigate(`/student/dsa/${prev.question_id}`)} className="btn justify-center py-2.5 text-xs"><ChevronLeft size={14} /> Prev</button>
                  <button disabled={!next} onClick={() => navigate(`/student/dsa/${next.question_id}`)} className="btn justify-center py-2.5 text-xs">Next <ChevronRight size={14} /></button>
                </div>
              </div>
            )}

            {/* 2. Log Attempt Tab */}
            {activeTab === "log" && (
              <form onSubmit={submitAttempt} className="space-y-4 animate-fade-in">
                <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 uppercase font-semibold">Log Manual Attempt</div>
                
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[9px] font-mono text-ink-500 mb-1.5 uppercase font-semibold">Status</label>
                    <Select
                      value={formStatus}
                      onChange={(e) => setFormStatus(e.target.value)}
                      required
                      className="py-2 px-3 text-xs w-full"
                    >
                      <option value="attempted">Attempted</option>
                      <option value="solved">Solved</option>
                    </Select>
                  </div>
                  <div>
                    <label className="block text-[9px] font-mono text-ink-500 mb-1.5 uppercase font-semibold">Time (Minutes)</label>
                    <Input
                      type="number"
                      min="1"
                      value={formTimeTaken}
                      onChange={(e) => setFormTimeTaken(e.target.value)}
                      placeholder="e.g. 20"
                      className="py-2 px-3 text-xs w-full bg-bone-50"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[9px] font-mono text-ink-500 mb-1.5 uppercase font-semibold">Language</label>
                    <Input
                      type="text"
                      value={formLanguage}
                      onChange={(e) => setFormLanguage(e.target.value)}
                      placeholder="e.g. Python, C++"
                      className="py-2 px-3 text-xs w-full bg-bone-50"
                    />
                  </div>
                  <div>
                    <label className="block text-[9px] font-mono text-ink-500 mb-1.5 uppercase font-semibold">Approach</label>
                    <Input
                      type="text"
                      value={formApproach}
                      onChange={(e) => setFormApproach(e.target.value)}
                      placeholder="e.g. DFS, Two Pointer"
                      className="py-2 px-3 text-xs w-full bg-bone-50"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[9px] font-mono text-ink-500 mb-1.5 uppercase font-semibold">Notes</label>
                  <Textarea
                    value={formNotes}
                    onChange={(e) => setFormNotes(e.target.value)}
                    placeholder="Describe your logical steps, runtime complexity, or blockers..."
                    className="min-h-[100px] py-2 px-3 text-xs w-full"
                  />
                </div>

                <Button
                  type="submit"
                  disabled={submittingAttempt}
                  className="w-full py-3 text-xs"
                >
                  {submittingAttempt ? "RECORDING..." : "RECORD ATTEMPT"}
                </Button>
              </form>
            )}

            {/* 3. Submissions Tab */}
            {activeTab === "submissions" && (
              <div className="space-y-4 animate-fade-in">
                <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 uppercase font-semibold">Attempt & Submissions History</div>
                <div className="space-y-2 max-h-[480px] overflow-y-auto pr-1">
                  {attempts.map((att) => (
                    <div key={att.submission_id || att.attempt_id} className="p-4 border border-line bg-bone-50 text-xs font-mono space-y-2">
                      <div className="flex justify-between items-center">
                        {(att.status === "solved" || att.status === "Accepted") ? (
                          <Badge variant="success" className="text-[8px] py-0.2">SOLVED</Badge>
                        ) : (
                          <Badge variant="warning" className="text-[8px] py-0.2">{att.status || "ATTEMPTED"}</Badge>
                        )}
                        <span className="text-ink-400 text-[10px]">
                          {att.created_at ? new Date(att.created_at).toLocaleDateString() : ""}
                        </span>
                      </div>
                      {att.time_taken && (
                        <div><span className="text-ink-400">TIME:</span> {att.time_taken} mins</div>
                      )}
                      {att.language && (
                        <div><span className="text-ink-400">LANGUAGE:</span> {att.language}</div>
                      )}
                      {att.runtime_ms && (
                        <div><span className="text-ink-400">RUNTIME:</span> {att.runtime_ms}ms / {att.memory_kb}KB</div>
                      )}
                      {att.approach && (
                        <div><span className="text-ink-400">APPROACH:</span> {att.approach}</div>
                      )}
                      {att.notes && (
                        <div className="text-ink-600 mt-2 border-t border-line/40 pt-2 font-serif italic">"{att.notes}"</div>
                      )}
                    </div>
                  ))}
                  {attempts.length === 0 && (
                    <div className="text-xs text-ink-400 font-mono italic">No submissions or attempts recorded.</div>
                  )}
                </div>
              </div>
            )}

            {/* 4. Comments Tab */}
            {activeTab === "comments" && (
              <div className="space-y-4 animate-fade-in">
                <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 uppercase font-semibold">Faculty Feedback</div>
                <div className="space-y-2 max-h-[480px] overflow-y-auto pr-1">
                  {loadingComments ? (
                    <div className="text-xs text-ink-400 font-mono">Loading feedback…</div>
                  ) : comments.length === 0 ? (
                    <div className="text-xs text-ink-400 font-mono italic">No comments from faculty yet.</div>
                  ) : (
                    comments.map((cmt) => (
                      <div key={cmt.comment_id} className="p-4 border border-line bg-accent/5 text-xs font-mono space-y-1.5 animate-fade-in">
                        <div className="flex justify-between items-center text-ink/75 font-semibold">
                          <span>{cmt.faculty_name || "Faculty Coach"}</span>
                          <span className="text-[9px] font-normal">
                            {cmt.created_at ? new Date(cmt.created_at).toLocaleDateString() : ""}
                          </span>
                        </div>
                        <div className="text-ink-700 mt-1 font-serif leading-relaxed">{cmt.body || cmt.comment}</div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </aside>

        <main className="col-span-12 lg:col-span-8 grid grid-rows-[1fr_auto] min-h-[calc(100vh-65px)]">
          <div className="grid grid-cols-12 min-h-[540px]">
            <section className="col-span-12 xl:col-span-8 border-r border-line bg-ink relative">
              <div className="absolute inset-0 h-full w-full">
                <Editor
                  height="100%"
                  language={language === "cpp" ? "cpp" : language}
                  value={code}
                  onChange={(value) => setCode(value || "")}
                  theme="vs-dark"
                  options={{ minimap: { enabled: true }, fontSize: 14, wordWrap: "on", scrollBeyondLastLine: false }}
                />
              </div>
            </section>
            <section className="col-span-12 xl:col-span-4 bg-paper p-5 flex flex-col justify-between overflow-y-auto">
              <div className="space-y-5">
                <label className="font-mono text-[9px] tracking-[0.18em] text-ink-400 uppercase font-semibold">Language Selection
                  <Select value={language} onChange={(e) => changeLanguage(e.target.value)} className="mt-2 w-full">
                    <option value="python">Python</option>
                    <option value="javascript">JavaScript</option>
                    <option value="java">Java</option>
                    <option value="cpp">C++</option>
                  </Select>
                </label>
                <label className="font-mono text-[9px] tracking-[0.18em] text-ink-400 uppercase font-semibold block">Custom Run Input
                  <Textarea value={customInput} onChange={(e) => setCustomInput(e.target.value)} placeholder="Provide mock input payload..." className="mt-2 min-h-[100px]" />
                </label>
                <div className="grid grid-cols-2 gap-3">
                  <Button disabled={running} onClick={() => execute("run")} className="py-2.5 text-xs"><Play size={14} /> Run Code</Button>
                  <Button disabled={running} onClick={() => execute("submit")} className="py-2.5 text-xs"><Send size={14} /> Submit Code</Button>
                </div>
              </div>
              
              <div className="mt-6 border border-line bg-bone-50 p-4 min-h-[220px] flex flex-col justify-between">
                <div>
                  <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400 uppercase font-semibold">Console Results</div>
                  {result ? (
                    <div className="mt-4 space-y-3 text-sm animate-fade-in">
                      <div className="flex justify-between items-baseline"><span className="font-display text-2xl text-ink font-bold">{result.status}</span><span className="font-mono text-[10px] uppercase tracking-[0.18em] text-ink-400">not executed · not graded</span></div>
                      {(result.signals || []).map((signal) => (
                        <div key={signal.label} className={`flex items-start gap-2 font-mono text-[11px] ${signal.met ? "text-accent" : "text-ink-400"}`}>
                          <span aria-hidden="true">{signal.met ? "+" : "-"}</span><span>{signal.label}</span>
                        </div>
                      ))}
                      {result.note && <p className="text-[11px] leading-relaxed text-ink-400 border-t border-line pt-2">{result.note}</p>}
                      {result.output && <div className="border border-line bg-paper p-3 font-mono text-[11px] leading-relaxed max-h-36 overflow-y-auto whitespace-pre-wrap">{result.output}</div>}
                      {result.errors && <div className="border border-red-200 bg-red-50 p-3 font-mono text-[11px] text-red-700 max-h-36 overflow-y-auto whitespace-pre-wrap">{result.errors}</div>}

                    </div>
                  ) : (
                    <div className="mt-4 text-xs text-ink-400 italic">No output yet. Write your code and click Run.</div>
                  )}
                </div>
              </div>
            </section>
          </div>
        </main>
      </div>
    </div>
  );
}
