import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { useNavigate } from "react-router-dom";
import Editor from "@monaco-editor/react";
import { CheckCircle2, Circle, Plus, Minus, Play, Send } from "lucide-react";
import { Button, Input, Textarea, Select, Badge, Progress, SheetRoot, SheetContent } from "../components/Primitives";
import { PageTransition, DashboardReveal, CounterAnimation } from "../components/Motion";

export default function StudentDSA() {
  const navigate = useNavigate();
  const [d, setD] = useState(null);
  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [attempts, setAttempts] = useState([]);
  const [comments, setComments] = useState([]);
  const [loadingDetails, setLoadingDetails] = useState(false);

  // Form states for logging attempt
  const [formStatus, setFormStatus] = useState("attempted");
  const [formTimeTaken, setFormTimeTaken] = useState("");
  const [formLanguage, setFormLanguage] = useState("");
  const [formApproach, setFormApproach] = useState("");
  const [formNotes, setFormNotes] = useState("");
  const [submittingAttempt, setSubmittingAttempt] = useState(false);
  const [codeLanguage, setCodeLanguage] = useState("python");
  const [code, setCode] = useState("def solve():\n    pass\n\nsolve()\n");
  const [customInput, setCustomInput] = useState("");
  const [execution, setExecution] = useState(null);
  const [runningCode, setRunningCode] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [difficultyFilter, setDifficultyFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const load = async () => {
    const [{ data: dashboard }, { data: questionProgress }] = await Promise.all([
      api.get("/me/dashboard"),
      api.get("/me/dsa/questions"),
    ]);
    setD({ ...dashboard, dsa_question_progress: questionProgress });
  };

  useEffect(() => { load(); }, []);

  const adjust = async (topic_code, delta) => {
    try {
      await api.post("/me/dsa/toggle", { topic_code, delta });
      load();
    } catch {}
  };

  const submitAttempt = async (e) => {
    e.preventDefault();
    const studentId = d?.dsa_question_progress?.student_id;
    if (!selectedQuestion || !studentId) return;
    setSubmittingAttempt(true);
    try {
      const qid = selectedQuestion.question_id;

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

      // 3. Clear/reset form inputs
      setFormTimeTaken("");
      setFormApproach("");
      setFormNotes("");

      // 4. Reload all info
      await load();
      await loadQuestionDetails(qid);
    } catch (err) {
      console.error(err);
    } finally {
      setSubmittingAttempt(false);
    }
  };

  const loadQuestionDetails = async (questionId) => {
    const studentId = d?.dsa_question_progress?.student_id;
    if (!studentId) return;
    setLoadingDetails(true);
    try {
      const [attemptsRes, commentsRes] = await Promise.all([
        api.get(`/dsa/student/${studentId}/attempts?question_id=${questionId}`),
        api.get(`/dsa/student/${studentId}/comments`),
      ]);
      setAttempts(attemptsRes.data?.attempts || []);
      const questionComments = (commentsRes.data?.comments || []).filter(
        (c) => c.question_id === questionId
      );
      setComments(questionComments);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDetails(false);
    }
  };

  const runCode = async (kind = "run") => {
    if (!selectedQuestion) return;
    setRunningCode(true);
    try {
      const endpoint = kind === "submit" ? "/me/dsa/submissions/submit" : "/me/dsa/submissions/run";
      const { data } = await api.post(endpoint, {
        question_id: selectedQuestion.question_id,
        language: codeLanguage,
        code,
        custom_input: customInput,
      });
      setExecution(data);
      await load();
      await loadQuestionDetails(selectedQuestion.question_id);
    } catch (err) {
      setExecution({ result: { status: "Error", errors: err?.response?.data?.detail || "Execution failed" } });
    } finally {
      setRunningCode(false);
    }
  };

  if (!d) return <div className="font-mono text-xs text-ink-400 p-8">LOADING…</div>;
  const solved = d.dsa.reduce((a, t) => a + t.solved, 0);
  const pct = Math.round((solved / d.dsa_total) * 100);

  return (
    <PageTransition className="space-y-10">
      <DashboardReveal className="grid grid-cols-12 gap-4">
        <div className="col-span-12 md:col-span-8 editorial p-10 dash-reveal">
          <div className="font-mono text-[10px] tracking-[0.28em] text-ink-400">§ DSA · CURRICULUM</div>
          <h1 className="font-display text-5xl md:text-6xl tracking-tightest mt-3" data-testid="sdsa-heading">
            Your <span className="text-accent">solve sheet.</span>
          </h1>
          <p className="font-serif text-lg text-ink-500 mt-2 max-w-xl">
            Click + as you solve each problem. CareerOS updates your readiness in real time.
          </p>
        </div>
        <div className="col-span-12 md:col-span-4 editorial bg-ink text-bone p-10 flex flex-col justify-between dash-reveal">
          <div>
            <div className="font-mono text-[10px] tracking-[0.28em] text-bone/45">TOTAL · SOLVED</div>
            <div className="font-display text-[8vw] md:text-[6vw] tracking-tightest leading-[0.9] tnum text-accent">
              <CounterAnimation value={solved} />
            </div>
            <div className="text-bone/60 text-sm mt-1">/ {d.dsa_total} problems · {pct}%</div>
          </div>
          <div className="mt-6">
            <Progress value={pct} />
          </div>
        </div>
      </DashboardReveal>

      {/* Filters Bar */}
      <div className="border border-line bg-paper p-6 flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="w-full md:w-1/3">
          <label className="block font-mono text-[9px] tracking-wider text-ink-400 mb-1.5 uppercase font-semibold">Search Problems</label>
          <Input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by title, e.g. Two Sum..."
            className="w-full py-2 px-3 text-xs bg-bone-50"
          />
        </div>
        <div className="flex flex-wrap items-center gap-4 w-full md:w-auto">
          <div>
            <label className="block font-mono text-[9px] tracking-wider text-ink-400 mb-1.5 uppercase font-semibold">Difficulty</label>
            <div className="flex items-center border border-line bg-bone-50 p-0.5">
              {["all", "easy", "medium", "hard"].map((dFilter) => (
                <button
                  key={dFilter}
                  onClick={() => setDifficultyFilter(dFilter)}
                  className={`px-3 py-1.5 text-[10px] font-mono uppercase transition-all ${
                    difficultyFilter === dFilter ? "bg-ink text-bone font-semibold" : "text-ink/65 hover:bg-bone-100"
                  }`}
                >
                  {dFilter}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block font-mono text-[9px] tracking-wider text-ink-400 mb-1.5 uppercase font-semibold">Status</label>
            <div className="flex items-center border border-line bg-bone-50 p-0.5">
              {["all", "solved", "unsolved"].map((sFilter) => (
                <button
                  key={sFilter}
                  onClick={() => setStatusFilter(sFilter)}
                  className={`px-3 py-1.5 text-[10px] font-mono uppercase transition-all ${
                    statusFilter === sFilter ? "bg-ink text-bone font-semibold" : "text-ink/65 hover:bg-bone-100"
                  }`}
                >
                  {sFilter}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      <DashboardReveal className="grid grid-cols-12 gap-4" data-testid="sdsa-topics">
        {d.dsa.map((t) => {
          const p = Math.round((t.solved / t.total) * 100);
          const topicDetail = d.dsa_question_progress?.topics?.find((row) => row.topic_code === t.topic_code);
          const questions = topicDetail?.questions || [];
          const filteredQuestions = questions.filter((q) => {
            const matchesSearch = searchQuery ? q.title.toLowerCase().includes(searchQuery.toLowerCase()) : true;
            const matchesDifficulty = difficultyFilter === "all" ? true : q.difficulty?.toLowerCase() === difficultyFilter;
            const matchesStatus = statusFilter === "all" ? true : statusFilter === "solved" ? q.solved : !q.solved;
            return matchesSearch && matchesDifficulty && matchesStatus;
          });
          return (
            <div key={t.topic_code} className="col-span-12 md:col-span-6 lg:col-span-4 editorial p-6 flex flex-col justify-between dash-reveal" data-testid={`sdsa-${t.topic_code}`}>
              <div>
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="font-mono text-[10px] tracking-[0.2em] text-ink-400">{t.topic_code}</div>
                    <div className="font-display text-xl tracking-tight mt-1 truncate max-w-[200px]" title={t.topic_name}>{t.topic_name}</div>
                  </div>
                  <div className="font-display text-3xl tnum">{p}%</div>
                </div>
                <div className="mt-4">
                  <Progress value={p} />
                </div>
              </div>

              <div className="mt-5 flex items-center justify-between">
                <div className="font-mono text-sm tnum">{t.solved}<span className="text-ink-400">/{t.total}</span></div>
                <div className="flex items-center gap-1.5">
                  <button onClick={() => adjust(t.topic_code, -1)} data-testid={`sdsa-minus-${t.topic_code}`} className="w-9 h-9 border border-line bg-paper hover:bg-ink hover:text-bone transition-all grid place-items-center active:scale-[0.95]">
                    <Minus size={14} />
                  </button>
                  <button onClick={() => adjust(t.topic_code, 1)} data-testid={`sdsa-plus-${t.topic_code}`} className="w-9 h-9 bg-ink text-bone hover:bg-accent transition-all grid place-items-center active:scale-[0.95]">
                    <Plus size={14} />
                  </button>
                </div>
              </div>

              <div className="mt-5 border-t border-line pt-4 flex-1">
                <div className="flex items-center justify-between">
                  <div className="font-mono text-[9px] tracking-[0.18em] text-ink-400">QUESTION QUEUE</div>
                  <Badge variant="outline" className="text-[8px] py-0.2">{topicDetail?.attempted || 0} ATTEMPTS</Badge>
                </div>
                <div className="mt-3 max-h-64 overflow-y-auto pr-1 space-y-1" data-testid={`sdsa-questions-${t.topic_code}`}>
                  {filteredQuestions.map((question) => (
                    <button
                      key={question.question_id}
                      onClick={() => {
                        navigate(`/student/dsa/${question.question_id}`);
                      }}
                      className="w-full grid grid-cols-[20px_1fr_auto] gap-2 items-center text-left px-2.5 py-2 border border-transparent hover:border-line-strong hover:bg-bone-100/50 transition-all font-sans"
                      data-testid={`sdsa-question-${question.question_id}`}
                    >
                      {question.solved ? <CheckCircle2 size={15} className="text-accent" /> : <Circle size={15} className="text-ink-300" />}
                      <span className={`text-xs leading-snug truncate ${question.solved ? "text-ink font-semibold" : "text-ink/65"}`}>{question.title}</span>
                      <span className="font-mono text-[9px] text-ink/40 uppercase">{question.difficulty}</span>
                    </button>
                  ))}
                  {filteredQuestions.length === 0 && (
                    <div className="text-[10px] text-ink-400 italic px-2.5 py-2">No problems match filters.</div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </DashboardReveal>

      {/* Slide Drawer for Question Details */}
      <SheetRoot open={!!selectedQuestion} onOpenChange={(open) => !open && setSelectedQuestion(null)}>
        {selectedQuestion && (
          <SheetContent title={selectedQuestion.title}>
            <div className="space-y-6 pt-2">
              <div className="flex flex-wrap gap-2">
                <Badge variant="solid">{selectedQuestion.difficulty}</Badge>
                <Badge variant="accent">{selectedQuestion.topic_code}</Badge>
                {selectedQuestion.solved ? (
                  <Badge variant="success">SOLVED</Badge>
                ) : (
                  <Badge variant="warning">UNSOLVED</Badge>
                )}
              </div>

              <div className="border border-line-strong bg-bone-100/80 p-5 space-y-4" data-testid="dsa-coding-workspace">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">CODING WORKSPACE</div>
                    <div className="text-xs text-ink-500 mt-1">Run against custom input, then submit to update readiness.</div>
                  </div>
                  <Select value={codeLanguage} onChange={(e) => setCodeLanguage(e.target.value)} className="w-36 py-2 text-xs">
                    <option value="python">Python</option>
                    <option value="javascript">JavaScript</option>
                    <option value="java">Java</option>
                    <option value="cpp">C++</option>
                  </Select>
                </div>
                <div className="border border-line bg-ink overflow-hidden">
                  <Editor
                    height="320px"
                    language={codeLanguage === "cpp" ? "cpp" : codeLanguage}
                    value={code}
                    onChange={(value) => setCode(value || "")}
                    theme="vs-dark"
                    options={{ minimap: { enabled: false }, fontSize: 13, wordWrap: "on", scrollBeyondLastLine: false }}
                  />
                </div>
                <Textarea
                  value={customInput}
                  onChange={(e) => setCustomInput(e.target.value)}
                  placeholder="Custom input..."
                  className="min-h-[70px] py-2 px-3 text-xs"
                />
                <div className="grid grid-cols-2 gap-3">
                  <Button type="button" disabled={runningCode} onClick={() => runCode("run")} className="py-2.5">
                    <Play size={14} /> {runningCode ? "RUNNING..." : "RUN CODE"}
                  </Button>
                  <Button type="button" disabled={runningCode} onClick={() => runCode("submit")} className="py-2.5">
                    <Send size={14} /> SUBMIT CODE
                  </Button>
                </div>
                {execution?.result && (
                  <div className="border border-line bg-paper p-4 text-xs font-mono space-y-2">
                    <div className="flex justify-between">
                      <span className="text-ink">{execution.result.status}</span>
                      <span className="text-ink-400 uppercase tracking-[0.16em] text-[10px]">not executed · not graded</span>
                    </div>
                    {execution.result.output && <div className="text-ink-500">{execution.result.output}</div>}
                    {execution.result.errors && <div className="text-red-700">{execution.result.errors}</div>}
                    {(execution.result.signals || []).map((signal) => (
                      <div key={signal.label} className={`flex gap-2 ${signal.met ? "text-accent" : "text-ink-400"}`}>
                        <span aria-hidden="true">{signal.met ? "+" : "-"}</span><span>{signal.label}</span>
                      </div>
                    ))}
                    {execution.result.note && <p className="text-ink-400 leading-relaxed">{execution.result.note}</p>}
                  </div>
                )}
              </div>

              {/* Log new attempt form */}
              <form onSubmit={submitAttempt} className="space-y-4 border border-line-strong p-5 bg-bone-100/80">
                <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">LOG NEW ATTEMPT</div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] font-mono text-ink-500 mb-1">STATUS</label>
                    <Select
                      value={formStatus}
                      onChange={(e) => setFormStatus(e.target.value)}
                      required
                      className="py-2 px-3 text-xs"
                    >
                      <option value="attempted">Attempted</option>
                      <option value="solved">Solved</option>
                    </Select>
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono text-ink-500 mb-1">TIME TAKEN (MINUTES)</label>
                    <Input
                      type="number"
                      min="1"
                      value={formTimeTaken}
                      onChange={(e) => setFormTimeTaken(e.target.value)}
                      placeholder="e.g. 25"
                      className="py-2 px-3 text-xs"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-[10px] font-mono text-ink-500 mb-1">LANGUAGE</label>
                    <Input
                      type="text"
                      value={formLanguage}
                      onChange={(e) => setFormLanguage(e.target.value)}
                      placeholder="e.g. Python, C++"
                      className="py-2 px-3 text-xs"
                    />
                  </div>
                  <div>
                    <label className="block text-[10px] font-mono text-ink-500 mb-1">APPROACH</label>
                    <Input
                      type="text"
                      value={formApproach}
                      onChange={(e) => setFormApproach(e.target.value)}
                      placeholder="e.g. Two Pointer, BFS"
                      className="py-2 px-3 text-xs"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-[10px] font-mono text-ink-500 mb-1">NOTES</label>
                  <Textarea
                    value={formNotes}
                    onChange={(e) => setFormNotes(e.target.value)}
                    placeholder="Write difficulties, complexity details..."
                    className="min-h-[70px] py-2 px-3 text-xs"
                  />
                </div>

                <Button
                  type="submit"
                  disabled={submittingAttempt}
                  className="w-full py-2.5"
                >
                  {submittingAttempt ? "RECORDING..." : "RECORD ATTEMPT"}
                </Button>
              </form>

              {/* History log */}
              <div className="space-y-3">
                <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">ATTEMPT HISTORY</div>
                {loadingDetails ? (
                  <div className="text-xs text-ink-400 font-mono">LOADING HISTORY…</div>
                ) : attempts.length === 0 ? (
                  <div className="text-xs text-ink-400 font-mono italic">No attempts logged yet.</div>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {attempts.map((att) => (
                      <div key={att.attempt_id} className="p-3 border border-line bg-paper text-xs font-mono space-y-1.5">
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
                          <div className="text-ink-600 mt-1.5 border-t border-line/40 pt-1.5 font-serif italic">"{att.notes}"</div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Faculty comments */}
              <div className="space-y-3">
                <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">FACULTY COACH COMMENTS</div>
                {loadingDetails ? (
                  <div className="text-xs text-ink-400 font-mono">LOADING COMMENTS…</div>
                ) : comments.length === 0 ? (
                  <div className="text-xs text-ink-400 font-mono italic">No comments from faculty yet.</div>
                ) : (
                  <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                    {comments.map((cmt) => (
                      <div key={cmt.comment_id} className="p-3 border border-line-strong bg-accent/5 text-xs font-mono space-y-1.5">
                        <div className="flex justify-between items-center text-ink/75 font-semibold">
                          <span>{cmt.faculty_name || "Faculty"}</span>
                          <span className="text-[9px] font-normal">
                            {cmt.created_at ? new Date(cmt.created_at).toLocaleDateString() : ""}
                          </span>
                        </div>
                        <div className="text-ink-700 mt-1 font-serif">{cmt.body || cmt.comment}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </SheetContent>
        )}
      </SheetRoot>
    </PageTransition>
  );
}
