import React, { useEffect, useState } from "react";
import { api } from "../lib/api";
import { Trophy } from "lucide-react";

export default function DSAIntelligence() {
  const [d, setD] = useState(null);
  const [selectedStudent, setSelectedStudent] = useState(null);
  const [studentTopics, setStudentTopics] = useState([]);
  const [loadingStudentDSA, setLoadingStudentDSA] = useState(false);
  const [expandedTopicCode, setExpandedTopicCode] = useState(null);

  const [selectedQuestion, setSelectedQuestion] = useState(null);
  const [attempts, setAttempts] = useState([]);
  const [comments, setComments] = useState([]);
  const [loadingQuestionDetails, setLoadingQuestionDetails] = useState(false);
  const [newCommentBody, setNewCommentBody] = useState("");
  const [submittingComment, setSubmittingComment] = useState(false);

  const loadData = () => {
    api.get("/dsa/intelligence").then(({ data }) => setD(data));
  };

  useEffect(() => {
    loadData();
  }, []);

  const loadStudentDSA = async (studentId) => {
    setLoadingStudentDSA(true);
    setExpandedTopicCode(null);
    setSelectedQuestion(null);
    setAttempts([]);
    setComments([]);
    try {
      const { data } = await api.get(`/dsa/student/${studentId}/questions`);
      setStudentTopics(data.topics || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingStudentDSA(false);
    }
  };

  const loadQuestionDetails = async (studentId, questionId) => {
    setLoadingQuestionDetails(true);
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
      setLoadingQuestionDetails(false);
    }
  };

  const submitComment = async (e) => {
    e.preventDefault();
    if (!selectedStudent || !selectedQuestion || !newCommentBody.trim()) return;
    setSubmittingComment(true);
    try {
      const studentId = selectedStudent.student_id;
      const questionId = selectedQuestion.question_id;

      await api.post(`/dsa/student/${studentId}/comment`, {
        question_id: questionId,
        body: newCommentBody,
      });

      setNewCommentBody("");
      await loadQuestionDetails(studentId, questionId);
      // Also refresh the overall dashboard to ensure solves count etc. are fresh
      loadData();
    } catch (err) {
      console.error(err);
    } finally {
      setSubmittingComment(false);
    }
  };

  if (!d) return <div className="font-mono text-xs text-ink-400">LOADING DSA …</div>;

  const total = d.total_problems;
  const topicCount = d.by_topic?.length || 0;

  return (
    <div className="space-y-10">
      <div className="grid grid-cols-12 gap-3">
        <div className="col-span-12 md:col-span-8 editorial p-10 lg:p-12">
          <div className="font-mono text-[10px] tracking-[0.28em] text-ink-400">§ DSA · FACULTY INTERACTION</div>
          <h1 className="font-display text-5xl md:text-6xl tracking-tightest mt-3" data-testid="dsa-heading">
            {d.scope?.startsWith("department:") ? (
              <>Department <span className="text-accent">DSA pulse.</span></>
            ) : (
              <>Institutional DSA <span className="text-accent">readiness map.</span></>
            )}
          </h1>
          <p className="font-serif text-lg text-ink-500 mt-3 max-w-xl">
            {d.scope?.startsWith("department:")
              ? `Scoped to your department (${d.scope.split(":")[1]}). Every curriculum topic, every student you teach.`
              : "Every curriculum topic. Every student. Every solve. Use the topic map to find weak areas and the leaderboard to find your top contenders."}
          </p>
          {d.scope?.startsWith("department:") && (
            <div className="mt-4 inline-flex pill" data-testid="dsa-scope-badge" style={{ color: "#4a5d3a", borderColor: "#4a5d3a" }}>
              FACULTY SCOPE · {d.scope.split(":")[1]}
            </div>
          )}
        </div>
        <div className="col-span-12 md:col-span-4 editorial bg-ink-900 text-bone-100 p-10">
          <div className="font-mono text-[10px] tracking-[0.28em] text-bone-100/40">PROBLEMS · SHEET TOTAL</div>
          <div className="font-display text-[8vw] md:text-[6vw] tracking-tightest leading-[0.9] tnum">{total}</div>
          <div className="text-bone-100/60 text-sm">across {topicCount} sections</div>
        </div>
      </div>

      {/* Topics heatmap */}
      <div className="editorial p-8" data-testid="dsa-topics">
        <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">TOPICS · INSTITUTIONAL AVERAGE</div>
        <h3 className="font-display text-2xl tracking-tight mt-1">Topic mastery map</h3>
        <div className="mt-6 grid grid-cols-12 gap-3">
          {d.by_topic.map((t) => {
            const pct = t.students && t.total ? Math.round((t.solved / (t.students * t.total)) * 100) : 0;
            return (
              <div key={t._id} className="col-span-6 md:col-span-4 lg:col-span-3 border border-line p-5 bg-bone-50" data-testid={`dsa-topic-${t._id}`}>
                <div className="font-mono text-[10px] tracking-[0.2em] text-ink-400">{t._id}</div>
                <div className="font-display text-xl tracking-tight mt-1">{t.topic_name}</div>
                <div className="font-display text-4xl mt-3 tnum">{pct}%</div>
                <div className="mt-3 h-1.5 bg-bone-300 relative">
                  <div className="absolute inset-y-0 left-0" style={{ width: `${pct}%`, background: pct >= 60 ? "#0a0a0a" : pct >= 30 ? "#d4a017" : "#ff3b00" }} />
                </div>
                <div className="text-xs text-ink-500 mt-2 tnum">{t.solved} solves · {t.students} students · {t.total} problems</div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Leaderboard */}
      <div className="editorial" data-testid="dsa-leaderboard">
        <div className="p-6 border-b border-line">
          <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">LEADERBOARD · TOP 20</div>
          <h3 className="font-display text-2xl tracking-tight mt-1 flex items-center gap-3"><Trophy size={20} className="text-accent" /> Most solves</h3>
        </div>
        <div className="grid grid-cols-12 px-6 py-3 border-b border-line font-mono text-[10px] tracking-[0.24em] text-ink-400">
          <div className="col-span-1">#</div>
          <div className="col-span-4">STUDENT</div>
          <div className="col-span-2">ROLL</div>
          <div className="col-span-2">DEPT</div>
          <div className="col-span-2 text-right">SOLVED</div>
          <div className="col-span-1 text-right">READINESS</div>
        </div>
        {d.leaderboard.map((s, i) => (
          <div
            key={s.student_id}
            onClick={() => {
              setSelectedStudent(s);
              loadStudentDSA(s.student_id);
            }}
            className="grid grid-cols-12 px-6 py-4 border-b border-line items-center hover:bg-bone-200 cursor-pointer transition-colors"
            data-testid={`dsa-leader-${i}`}
          >
            <div className="col-span-1 font-mono text-sm text-ink-400">{String(i + 1).padStart(2, "0")}</div>
            <div className="col-span-4 font-medium hover:text-accent transition-colors">{s.name}</div>
            <div className="col-span-2 font-mono text-sm tnum">{s.roll_number}</div>
            <div className="col-span-2"><span className="pill bg-bone-100">{s.department}</span></div>
            <div className="col-span-2 text-right font-mono tnum">{s.solved}<span className="text-ink-400">/{total}</span></div>
            <div className="col-span-1 text-right font-mono text-accent tnum">{s.readiness}%</div>
          </div>
        ))}
      </div>

      {/* Student Details Sidebar Sheet/Drawer */}
      {selectedStudent && (
        <div className="fixed inset-0 bg-ink-900/60 backdrop-blur-sm z-50 flex justify-end" onClick={() => setSelectedStudent(null)}>
          <div
            className="w-full max-w-2xl bg-bone-50 border-l border-line h-full flex flex-col shadow-2xl overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Drawer Header */}
            <div className="p-6 border-b border-line flex items-start justify-between bg-bone-100">
              <div>
                <div className="font-mono text-[10px] tracking-[0.2em] text-ink-400">STUDENT DETAILS</div>
                <h3 className="font-display text-2xl tracking-tight mt-1">{selectedStudent.name}</h3>
                <div className="mt-2 flex gap-2 font-mono text-xs">
                  <span className="px-2 py-0.5 bg-bone-200 border border-line text-ink-600">{selectedStudent.department}</span>
                  <span className="px-2 py-0.5 bg-bone-200 border border-line text-ink-600">{selectedStudent.solved} / {total} Solved</span>
                  <span className="px-2 py-0.5 bg-accent/25 border border-accent text-ink-900 font-bold">{selectedStudent.readiness}% Readiness</span>
                </div>
              </div>
              <button
                onClick={() => setSelectedStudent(null)}
                className="font-mono text-xs text-ink-400 hover:text-ink-900 border border-line px-2 py-1 bg-bone-50 transition-colors"
              >
                CLOSE
              </button>
            </div>

            {/* Drawer Content */}
            <div className="flex-1 overflow-y-auto p-6 md:p-8 grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Left Column: Topics Accordion */}
              <div className="space-y-4">
                <div className="font-mono text-[10px] tracking-[0.24em] text-ink-400">TOPICS & PROGRESS</div>
                {loadingStudentDSA ? (
                  <div className="text-xs text-ink-400 font-mono">LOADING TOPICS…</div>
                ) : studentTopics.length === 0 ? (
                  <div className="text-xs text-ink-400 font-mono">No topics available.</div>
                ) : (
                  <div className="space-y-2 max-h-[70vh] overflow-y-auto pr-1">
                    {studentTopics.map((t) => {
                      const isExpanded = expandedTopicCode === t.topic_code;
                      return (
                        <div key={t.topic_code} className="border border-line bg-bone-100">
                          <button
                            onClick={() => setExpandedTopicCode(isExpanded ? null : t.topic_code)}
                            className="w-full px-3 py-2.5 flex justify-between items-center hover:bg-bone-200 transition-colors text-left"
                          >
                            <div className="min-w-0 pr-2">
                              <span className="font-mono text-[9px] text-ink-400 block leading-none">{t.topic_code}</span>
                              <span className="font-display font-medium text-xs text-ink-900 truncate block mt-0.5">{t.topic_name}</span>
                            </div>
                            <div className="flex items-center gap-2 shrink-0">
                              <span className="font-mono text-[10px] text-ink-500">{t.solved}/{t.total}</span>
                              <span className="font-mono text-[9px] text-ink-400">{isExpanded ? "▲" : "▼"}</span>
                            </div>
                          </button>

                          {isExpanded && (
                            <div className="border-t border-line bg-bone-50 p-1.5 space-y-1">
                              {t.questions?.map((q) => {
                                const isQSelected = selectedQuestion?.question_id === q.question_id;
                                return (
                                  <button
                                    key={q.question_id}
                                    onClick={() => {
                                      setSelectedQuestion(q);
                                      loadQuestionDetails(selectedStudent.student_id, q.question_id);
                                    }}
                                    className={`w-full text-left px-2 py-1.5 text-xs flex justify-between items-center transition-colors border ${
                                      isQSelected ? "border-ink-900 bg-bone-200" : "border-transparent hover:bg-bone-100"
                                    }`}
                                  >
                                    <span className={`flex items-center gap-1.5 truncate ${q.solved ? "text-ink-900 font-medium" : "text-ink-500"}`}>
                                      <span className={`w-1.5 h-1.5 rounded-full shrink-0 ${q.solved ? "bg-accent" : "bg-ink-300"}`} />
                                      <span className="truncate">{q.title}</span>
                                    </span>
                                    <span className="font-mono text-[9px] text-ink-400 shrink-0 ml-1">{q.difficulty}</span>
                                  </button>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Right Column: Question Details, Attempts & Faculty Comment Form */}
              <div>
                {selectedQuestion ? (
                  <div className="border border-line p-4 bg-bone-100 space-y-5 sticky top-0">
                    <div>
                      <div className="font-mono text-[10px] tracking-[0.2em] text-ink-400">SELECTED QUESTION</div>
                      <h4 className="font-display font-semibold text-sm text-ink-900 mt-1">{selectedQuestion.title}</h4>
                      <div className="mt-1 flex gap-1.5 font-mono text-[9px]">
                        <span className="px-1 bg-bone-200 border border-line text-ink-600">{selectedQuestion.difficulty}</span>
                        {selectedQuestion.solved ? (
                          <span className="px-1 bg-emerald-50 text-emerald-800 border border-emerald-200">SOLVED</span>
                        ) : (
                          <span className="px-1 bg-amber-50 text-amber-800 border border-amber-200">UNSOLVED</span>
                        )}
                      </div>
                    </div>

                    {/* Attempts history list */}
                    <div className="space-y-2">
                      <div className="font-mono text-[9px] tracking-[0.24em] text-ink-400">STUDENT ATTEMPTS</div>
                      {loadingQuestionDetails ? (
                        <div className="text-[11px] text-ink-400 font-mono">LOADING...</div>
                      ) : attempts.length === 0 ? (
                        <div className="text-[11px] text-ink-400 font-mono">No attempts logged yet.</div>
                      ) : (
                        <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1">
                          {attempts.map((att) => (
                            <div key={att.attempt_id} className="p-2 border border-line bg-bone-50 text-[11px] font-mono leading-relaxed">
                              <div className="flex justify-between items-center text-[9px] mb-1">
                                <span className={`px-1 py-0.2 ${att.status === "solved" ? "bg-emerald-50 text-emerald-800" : "bg-amber-50 text-amber-800"}`}>
                                  {att.status.toUpperCase()}
                                </span>
                                <span className="text-ink-400">
                                  {att.created_at ? new Date(att.created_at).toLocaleDateString() : ""}
                                </span>
                              </div>
                              {att.time_taken && <div>Time taken: {att.time_taken} mins</div>}
                              {att.language && <div>Language: {att.language}</div>}
                              {att.approach && <div>Approach: {att.approach}</div>}
                              {att.notes && <div className="text-ink-500 italic mt-0.5">"{att.notes}"</div>}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Comments log */}
                    <div className="space-y-2">
                      <div className="font-mono text-[9px] tracking-[0.24em] text-ink-400">FACULTY COMMENTS</div>
                      {loadingQuestionDetails ? (
                        <div className="text-[11px] text-ink-400 font-mono">LOADING...</div>
                      ) : comments.length === 0 ? (
                        <div className="text-[11px] text-ink-400 font-mono">No comments left yet.</div>
                      ) : (
                        <div className="space-y-1.5 max-h-32 overflow-y-auto pr-1">
                          {comments.map((cmt) => (
                            <div key={cmt.comment_id} className="p-2 border border-line bg-accent/5 text-[11px] font-mono leading-relaxed">
                              <div className="flex justify-between text-ink-500 font-semibold text-[9px] mb-1">
                                <span>{cmt.faculty_name || "Faculty"}</span>
                                <span className="font-normal">
                                  {cmt.created_at ? new Date(cmt.created_at).toLocaleDateString() : ""}
                                </span>
                              </div>
                              <div className="text-ink-700">{cmt.body || cmt.comment}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Leave comment form */}
                    <form onSubmit={submitComment} className="space-y-2 border-t border-line/50 pt-3">
                      <div className="font-mono text-[9px] tracking-[0.24em] text-ink-400">LEAVE A NEW COMMENT</div>
                      <textarea
                        value={newCommentBody}
                        onChange={(e) => setNewCommentBody(e.target.value)}
                        placeholder="Provide comment or guidance..."
                        className="w-full bg-bone-50 border border-line p-2 text-xs focus:outline-none h-14 resize-none"
                        required
                      />
                      <button
                        type="submit"
                        disabled={submittingComment}
                        className="w-full py-1 bg-ink-900 text-bone-100 hover:bg-accent hover:text-ink-900 transition-colors font-mono text-[10px] disabled:opacity-50"
                      >
                        {submittingComment ? "SUBMITTING..." : "SUBMIT COMMENT"}
                      </button>
                    </form>
                  </div>
                ) : (
                  <div className="h-full flex items-center justify-center border border-dashed border-line p-6 bg-bone-100 text-ink-400 font-mono text-xs">
                    Select a question from the left list to see attempts, comments, and leave feedback.
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
