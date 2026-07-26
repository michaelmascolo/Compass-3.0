import { useState, useRef, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  Loader2,
  Compass,
  MessageSquareQuote,
  X,
  CornerDownRight,
} from "lucide-react";
import { startPreview, getSession, interact, getNoticing } from "@/lib/api";
import ExperienceReflection from "@/components/ExperienceReflection";
import TeacherReflection from "@/components/TeacherReflection";
import WelcomeScreen from "@/components/WelcomeScreen";

// Experience Compass public flow: Welcome (Ch3) -> Assignment (Ch4) -> Writing
// (Ch4 minimal interim) -> coaching -> reflection. The educator temporarily
// becomes the learner: they create an authentic assignment, then respond to it.
export default function PublicPreview() {
  const [session, setSession] = useState(null);
  const [assignment, setAssignment] = useState("");   // Ch4 — the educator's authentic assignment (authoritative task)
  const [response, setResponse] = useState("");        // Ch4 — the one-paragraph response written on the Writing Screen
  const [draft, setDraft] = useState("");
  const [starting, setStarting] = useState(false);
  const [sending, setSending] = useState(false);
  const [cardOpen, setCardOpen] = useState(false);
  const [openCoachingId, setOpenCoachingId] = useState(null);
  const [replyOpen, setReplyOpen] = useState(false);
  const [reply, setReply] = useState("");
  // Chapter 3 — Welcome gate. Shows before the Assignment screen on first entry
  // this visit; "Try another paragraph" (restart) does NOT re-show it.
  const [entered, setEntered] = useState(false);
  // Chapter 4 — once the educator confirms the assignment, advance to the Writing screen.
  const [writingStarted, setWritingStarted] = useState(false);
  // Post-experience: the teacher chooses to review their own experience.
  const [reviewingAsTeacher, setReviewingAsTeacher] = useState(false);
  // Chapter 6 — Pedagogical Noticing: the "I understand you" beats shown before
  // the frozen engine's developmental response, on the FIRST encounter only.
  const [noticing, setNoticing] = useState(null); // {understanding, recognition, bridge}
  const [revealStage, setRevealStage] = useState(0); // 0 none · 1 understanding · 2 +recognition · 3 +bridge

  const isProcessing = !!session?.turns?.some((t) => t.status === "processing");
  const busy = starting || sending || isProcessing;

  const allTurns = session?.turns || [];
  const studentTurns = allTurns.filter((t) => t.role === "student");
  const completedAi = allTurns.filter((t) => t.role === "ai" && t.status === "complete" && t.content);
  const activeCoaching = completedAi.length ? completedAi[completedAi.length - 1] : null;
  const started = !!session;
  const reviseCount = studentTurns.filter((t) => t.kind === "revise").length;
  // Chapter 6 — the "first encounter" is the learner's first draft and Compass's
  // first response to it. Pedagogical Noticing runs only here; later revisions
  // keep the established relationship (existing coaching behavior).
  const isFirstMoment = started && reviseCount === 0;
  // Completion is driven ONLY by the single-objective experience_control phase,
  // never by an AI turn count.
  const phase = session?.experience_control?.phase || "active";
  const inReflection = phase === "reflection";
  const showWelcome = !entered && !started;
  const showAssignment = entered && !writingStarted && !started;
  const showWriting = entered && writingStarted && !started;

  // Poll while the engine is reasoning in the background.
  useEffect(() => {
    if (!session?.id || !isProcessing) return;
    const id = session.id;
    let cancelled = false;
    const timer = setInterval(async () => {
      try {
        const s = await getSession(id);
        if (!cancelled) setSession(s);
      } catch (e) {
        /* transient — keep polling */
      }
    }, 1500);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [session?.id, isProcessing]);

  // A new coaching target auto-surfaces its marker. On the FIRST encounter the
  // developmental response auto-expands so it flows continuously from the
  // noticing beats (no marker click, no abrupt screen change).
  useEffect(() => {
    if (activeCoaching) {
      setCardOpen(true);
      setOpenCoachingId(isFirstMoment ? activeCoaching.id : null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeCoaching?.id]);

  // Chapter 6 — reveal the noticing beats as a conversational sequence: subtle
  // timing (gentle fades), never a performed animation.
  useEffect(() => {
    if (!noticing) {
      setRevealStage(0);
      return;
    }
    setRevealStage(1);
    const t2 = setTimeout(() => setRevealStage((s) => (s < 2 ? 2 : s)), 1400);
    const t3 = setTimeout(() => setRevealStage((s) => (s < 3 ? 3 : s)), 2800);
    return () => {
      clearTimeout(t2);
      clearTimeout(t3);
    };
  }, [noticing]);

  // Writing Screen submit — creates the session with the educator's authentic
  // assignment as the authoritative task, then submits their EXACT response
  // (validated on the trimmed value, but transmitted/preserved unaltered).
  const submitResponse = useCallback(async () => {
    if (response.trim().length < 15 || starting) return;
    setStarting(true);
    try {
      const s = await startPreview({ assignment: assignment.trim() });
      const updated = await interact(s.id, { kind: "writing", content: response });
      setDraft(response);
      setSession(updated);
      // Chapter 6 — establish the relationship first. Fire Pedagogical Noticing
      // in parallel with the frozen engine's background reasoning. If it fails
      // or times out, the generic thinking experience remains (graceful).
      getNoticing(s.id)
        .then((res) => {
          if (res && res.ok) setNoticing(res);
        })
        .catch(() => {});
    } catch (e) {
      /* stay on writing screen */
    } finally {
      setStarting(false);
    }
  }, [response, starting, assignment]);

  // "Try another paragraph" — return to a CLEARED Assignment Screen (never the
  // Welcome Screen during the same visit) and begin a completely fresh session.
  const restart = useCallback(() => {
    setSession(null);
    setAssignment("");
    setResponse("");
    setDraft("");
    setWritingStarted(false);
    setCardOpen(false);
    setOpenCoachingId(null);
    setReplyOpen(false);
    setReply("");
    setReviewingAsTeacher(false);
    setNoticing(null);
    setRevealStage(0);
  }, []);

  const dirty = draft.trim() !== (studentTurns[studentTurns.length - 1]?.content || "").trim();

  const sendRevision = useCallback(async () => {
    if (!draft.trim() || busy || !session || !dirty) return;
    setSending(true);
    try {
      const updated = await interact(session.id, { kind: "revise", content: draft.trim() });
      setSession(updated);
      setOpenCoachingId(null);
    } catch (e) {
      /* polling / retry */
    } finally {
      setSending(false);
    }
  }, [draft, busy, session, dirty]);

  const sendExplain = useCallback(async () => {
    if (busy || !session) return;
    setSending(true);
    try {
      const updated = await interact(session.id, {
        kind: "explain",
        content: "Can you say a little more about what you mean?",
      });
      setSession(updated);
    } catch (e) {
      /* ignore */
    } finally {
      setSending(false);
    }
  }, [busy, session]);

  const sendReply = useCallback(async () => {
    if (!reply.trim() || busy || !session) return;
    setSending(true);
    const content = reply.trim();
    setReply("");
    setReplyOpen(false);
    try {
      const updated = await interact(session.id, { kind: "answer", content });
      setSession(updated);
    } catch (e) {
      /* ignore */
    } finally {
      setSending(false);
    }
  }, [reply, busy, session]);

  const wordCount = draft.trim() ? draft.trim().split(/\s+/).length : 0;

  return (
    <div className="min-h-screen paper-grain flex flex-col items-center">
      {!showWelcome && (
        <header className="w-full max-w-2xl flex items-center justify-between px-6 py-5">
          <div className="flex items-center gap-2 font-serif-display text-lg text-stone-800">
            <Compass className="h-5 w-5 text-[#8C3A2A]" />
            Compass
          </div>
        </header>
      )}

      <main className="w-full max-w-2xl flex-1 flex flex-col px-6 pb-12">
        {showWelcome ? (
          <WelcomeScreen onBegin={() => setEntered(true)} />
        ) : showAssignment ? (
          <AssignmentScreen
            assignment={assignment}
            setAssignment={setAssignment}
            onContinue={() => setWritingStarted(true)}
            onBack={() => setEntered(false)}
          />
        ) : showWriting ? (
          <WritingScreen
            assignment={assignment}
            response={response}
            setResponse={setResponse}
            onSubmit={submitResponse}
            onBack={() => setWritingStarted(false)}
            submitting={starting}
          />
        ) : inReflection ? (
          reviewingAsTeacher ? (
            <TeacherReflection
              sessionId={session?.id}
              onBack={() => setReviewingAsTeacher(false)}
            />
          ) : (
            <ExperienceReflection
              reflection={session?.experience_control?.reflection}
              draft={draft}
              onRestart={restart}
              onReviewAsTeacher={() => setReviewingAsTeacher(true)}
            />
          )
        ) : (
          <div className="flex-1 flex flex-col py-4">
            {started && (
              <p
                data-testid="preview-revision-progress"
                className="font-mono-panel text-[10px] uppercase tracking-[0.18em] text-stone-400 mb-3"
              >
                {reviseCount > 0 ? `Revision ${reviseCount}` : "Your first draft"}
              </p>
            )}

            {/* The passage — document canvas, editable in place. */}
            <div className="relative bg-white border border-stone-300 rounded-sm">
              <textarea
                data-testid="preview-document"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Your response…"
                className="block w-full min-h-[34vh] bg-transparent px-7 sm:px-10 py-8 text-[17px] leading-9 text-stone-900 placeholder:text-stone-400 outline-none resize-none custom-scroll font-serif-display"
              />
              <AnimatePresence>
                {activeCoaching && !busy && cardOpen && openCoachingId !== activeCoaching.id && (
                  <motion.button
                    key={`marker-${activeCoaching.id}`}
                    initial={{ opacity: 0, scale: 0.6 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.6 }}
                    onClick={() => setOpenCoachingId(activeCoaching.id)}
                    data-testid="preview-coaching-marker"
                    className="absolute right-[-12px] bottom-8 group flex items-center gap-2 p-2 -m-2"
                    title="Your coach has a note on this response"
                  >
                    <span className="coach-pulse h-3.5 w-3.5 rounded-full bg-[#8C3A2A] ring-4 ring-[#8C3A2A]/15" />
                    <span className="hidden group-hover:inline-block text-[10px] font-mono-panel uppercase tracking-[0.15em] text-[#8C3A2A] bg-white border border-[#8C3A2A]/30 rounded-sm px-2 py-1">
                      Coach note
                    </span>
                  </motion.button>
                )}
              </AnimatePresence>
            </div>

            {/* Chapter 6 — Pedagogical Noticing beats: "I understand you" before
                any teaching. First encounter only; continuous with the response. */}
            {isFirstMoment && noticing && (
              <NoticingBeats noticing={noticing} revealStage={revealStage} />
            )}

            {busy && (
              <div data-testid="preview-thinking" className="mt-4">
                {isFirstMoment && noticing ? <ThinkingWith /> : <Thinking />}
              </div>
            )}

            {/* Inline coaching prompt — adjacent to the passage, coach's voice. */}
            <AnimatePresence>
              {activeCoaching && openCoachingId === activeCoaching.id && !busy && (
                <motion.div
                  key={`card-${activeCoaching.id}`}
                  initial={{ opacity: 0, y: 8 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 8 }}
                  transition={{ duration: 0.35, ease: "easeOut" }}
                  data-testid="preview-coaching-card"
                  className="mt-5 bg-white border-l-2 border-[#8C3A2A] border-y border-r border-stone-200 rounded-sm p-5"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.18em] text-[#8C3A2A] font-mono-panel">
                      <MessageSquareQuote className="h-3.5 w-3.5" />
                      Your coach
                    </div>
                    <button
                      onClick={() => setOpenCoachingId(null)}
                      data-testid="preview-coaching-card-collapse"
                      className="text-stone-400 hover:text-stone-700"
                      aria-label="Set this note aside"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>
                  <p
                    data-testid="preview-coaching-invitation"
                    className="text-stone-800 leading-relaxed text-[16px] font-serif-display whitespace-pre-wrap"
                  >
                    {activeCoaching.content}
                  </p>
                  <div className="mt-4 flex flex-wrap items-center gap-4">
                    <span className="inline-flex items-center gap-1.5 text-[11px] text-stone-500">
                      <CornerDownRight className="h-3.5 w-3.5" />
                      Revise your response above, then send it back.
                    </span>
                    <button
                      onClick={sendExplain}
                      disabled={busy}
                      data-testid="preview-explain-more"
                      className="text-[11px] font-mono-panel uppercase tracking-[0.14em] text-stone-500 hover:text-[#8C3A2A] transition-colors disabled:opacity-40"
                    >
                      Explain more
                    </button>
                    <button
                      onClick={() => setReplyOpen((v) => !v)}
                      data-testid="preview-reply-toggle"
                      className="text-[11px] font-mono-panel uppercase tracking-[0.14em] text-stone-500 hover:text-[#8C3A2A] transition-colors"
                    >
                      Reply
                    </button>
                  </div>
                  {replyOpen && (
                    <div className="mt-3 flex items-end gap-2">
                      <textarea
                        data-testid="preview-reply-input"
                        value={reply}
                        onChange={(e) => setReply(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) sendReply();
                        }}
                        rows={2}
                        placeholder="Think aloud to your coach (this doesn't change your response)…"
                        className="flex-1 bg-[#faf9f6] border border-stone-300 rounded-sm p-2.5 text-sm text-stone-900 placeholder:text-stone-400 outline-none focus:ring-1 focus:ring-stone-900 resize-none"
                      />
                      <button
                        onClick={sendReply}
                        data-testid="preview-send-reply"
                        disabled={!reply.trim() || busy}
                        className="shrink-0 bg-stone-900 text-white text-xs px-3 py-2 rounded-sm hover:bg-stone-700 transition-colors disabled:opacity-40"
                      >
                        Send
                      </button>
                    </div>
                  )}
                </motion.div>
              )}
            </AnimatePresence>

            {/* Primary action bar. */}
            <div className="mt-6 flex items-center justify-between">
              <span className="text-xs text-stone-500 font-mono-panel" data-testid="preview-word-count">
                {wordCount} words
              </span>
              <button
                onClick={sendRevision}
                data-testid="preview-send-revision"
                disabled={!draft.trim() || busy || !dirty}
                className="group inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-6 py-3 rounded-sm font-medium tracking-wide hover:bg-[#6B2C20] enabled:hover:-translate-y-px transition-[background-color,transform] disabled:opacity-40 disabled:cursor-not-allowed"
              >
                {busy ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Reading…
                  </>
                ) : (
                  <>
                    Send revision
                    <ArrowRight className="h-4 w-4 transition-transform group-enabled:group-hover:translate-x-0.5" />
                  </>
                )}
              </button>
            </div>
            {!dirty && !busy && activeCoaching && (
              <p className="mt-2 text-right text-[11px] text-stone-400">
                Change something in your response to send a revision.
              </p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

const HELP_STARTERS = [
  "Explain why…",
  "Compare…",
  "What do you think about…",
  "How would you apply…",
  "What caused…",
  "What might happen if…",
  "Describe the relationship between…",
  "Use evidence to support…",
];

// Chapter 4 — Assignment Screen. The educator creates a brief, authentic
// assignment in their own words. No subject/grade/standard/type is required; no
// evaluation, rewriting, or analysis happens here; no session is created yet.
function AssignmentScreen({ assignment, setAssignment, onContinue, onBack }) {
  const [helpOpen, setHelpOpen] = useState(false);
  const meaningful = assignment.trim().length >= 10;
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="flex-1 flex flex-col justify-center max-w-xl mx-auto w-full py-10"
      data-testid="assignment-screen"
    >
      <h1 className="font-serif-display text-3xl sm:text-4xl leading-snug text-stone-900">
        Create a brief assignment
      </h1>
      <p className="text-stone-600 mt-4 text-[15px] leading-relaxed">
        Think of an assignment you might genuinely give to a student. Enter a prompt that could be
        answered in one thoughtful paragraph. It might ask a learner to explain, interpret, compare,
        argue, reflect, or apply an idea.
      </p>

      <label
        htmlFor="assignment-input"
        className="mt-7 block font-mono-panel text-[11px] uppercase tracking-[0.14em] text-stone-500 mb-1.5"
      >
        Your assignment
      </label>
      <textarea
        id="assignment-input"
        data-testid="assignment-input"
        value={assignment}
        onChange={(e) => setAssignment(e.target.value)}
        rows={5}
        autoFocus
        placeholder="For example: Explain why a character made an important decision, compare two approaches to solving a problem, or describe how a concept applies to a real situation."
        className="w-full bg-white border border-stone-300 rounded-sm p-5 text-[16px] leading-8 text-stone-900 placeholder:text-stone-400 outline-none focus:ring-1 focus:ring-stone-900 focus:border-stone-900 transition-colors resize-none"
      />
      <p className="mt-2 text-[13px] text-stone-500">
        Keep the assignment brief. You will respond to it yourself in the next step.
      </p>
      <p className="mt-1 text-[12px] text-stone-400" data-testid="assignment-privacy-note">
        Please do not include a student's name or other identifying information.
      </p>

      <div className="mt-3">
        <button
          type="button"
          onClick={() => setHelpOpen((v) => !v)}
          data-testid="assignment-help-toggle"
          aria-expanded={helpOpen}
          className="text-[12px] font-mono-panel uppercase tracking-[0.14em] text-stone-500 hover:text-[#8C3A2A] transition-colors"
        >
          Help me create one
        </button>
        {helpOpen && (
          <div
            data-testid="assignment-help-area"
            className="mt-3 bg-[#faf9f6] border border-stone-200 rounded-sm p-4"
          >
            <p className="text-[13px] text-stone-600 mb-2">Try beginning with one of these:</p>
            <ul className="space-y-1">
              {HELP_STARTERS.map((s) => (
                <li key={s} className="text-[14px] text-stone-700 font-serif-display">• {s}</li>
              ))}
            </ul>
            <p className="text-[13px] text-stone-600 mt-3">
              Choose one beginning and complete it in your own words.
            </p>
          </div>
        )}
      </div>

      <div className="mt-7 flex items-center gap-5">
        <button
          onClick={onContinue}
          data-testid="assignment-continue-button"
          disabled={!meaningful}
          className="group inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-7 py-3 rounded-sm font-medium tracking-wide hover:bg-[#6B2C20] enabled:hover:-translate-y-px transition-[background-color,transform] disabled:opacity-40 disabled:cursor-not-allowed"
        >
          Continue
          <ArrowRight className="h-4 w-4 transition-transform group-enabled:group-hover:translate-x-0.5" />
        </button>
        <button
          type="button"
          onClick={onBack}
          data-testid="assignment-back-button"
          className="text-[12px] font-mono-panel uppercase tracking-[0.14em] text-stone-400 hover:text-stone-700 transition-colors"
        >
          Back
        </button>
      </div>
      {!meaningful && (
        <span className="text-stone-400 text-[13px] mt-2" data-testid="assignment-hint">
          Please enter the assignment you would like to respond to.
        </span>
      )}
    </motion.div>
  );
}

// Chapter 5 — Writing Screen. The educator responds, as a learner, to their
// authentic assignment with one genuine first-draft paragraph. The assignment
// is shown read-only; no live AI/grammar/autocomplete assistance appears; the
// exact response is preserved. Submit hands off to the existing thinking state.
function WritingScreen({ assignment, response, setResponse, onSubmit, onBack, submitting }) {
  const meaningful = response.trim().length >= 15;
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="flex-1 flex flex-col justify-center max-w-xl mx-auto w-full py-10"
      data-testid="writing-screen"
    >
      <h1 className="font-serif-display text-3xl sm:text-4xl leading-snug text-stone-900">
        Write your response
      </h1>
      <p className="text-stone-600 mt-4 text-[15px] leading-relaxed">
        Respond to your assignment in one thoughtful paragraph. Write a genuine first draft. Do not
        try to make it perfect before Compass sees it.
      </p>

      <p className="mt-7 font-mono-panel text-[11px] uppercase tracking-[0.14em] text-stone-500 mb-1.5">
        Your assignment
      </p>
      <div
        data-testid="writing-assignment-display"
        className="bg-[#faf9f6] border border-stone-200 rounded-sm p-4 text-[15px] leading-relaxed text-stone-800 whitespace-pre-wrap font-serif-display"
      >
        {assignment}
      </div>

      <label
        htmlFor="writing-input"
        className="mt-6 block font-mono-panel text-[11px] uppercase tracking-[0.14em] text-stone-500 mb-1.5"
      >
        Your first draft
      </label>
      <textarea
        id="writing-input"
        data-testid="writing-input"
        value={response}
        onChange={(e) => setResponse(e.target.value)}
        rows={9}
        autoFocus
        placeholder="Write one paragraph in response to your assignment."
        className="w-full bg-white border border-stone-300 rounded-sm p-5 text-[16px] leading-8 text-stone-900 placeholder:text-stone-400 outline-none focus:ring-1 focus:ring-stone-900 focus:border-stone-900 transition-colors resize-y min-h-[220px]"
      />
      <p className="mt-2 text-[13px] text-stone-500">
        Stop when you have expressed your main idea. Compass will work with what you have written.
      </p>

      <div className="mt-7 flex items-center gap-5">
        <button
          onClick={onSubmit}
          data-testid="writing-submit-button"
          disabled={!meaningful || submitting}
          className="group inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-7 py-3 rounded-sm font-medium tracking-wide hover:bg-[#6B2C20] enabled:hover:-translate-y-px transition-[background-color,transform] disabled:opacity-40 disabled:cursor-not-allowed"
        >
          {submitting ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Sending…
            </>
          ) : (
            <>
              Share with Compass
              <ArrowRight className="h-4 w-4 transition-transform group-enabled:group-hover:translate-x-0.5" />
            </>
          )}
        </button>
        <button
          type="button"
          onClick={onBack}
          data-testid="writing-back-button"
          className="text-[12px] font-mono-panel uppercase tracking-[0.14em] text-stone-400 hover:text-stone-700 transition-colors"
        >
          Back to assignment
        </button>
      </div>
      {!meaningful && (
        <span className="text-stone-400 text-[13px] mt-2" data-testid="writing-hint">
          Please write enough for Compass to understand the idea you are trying to express.
        </span>
      )}
    </motion.div>
  );
}

function Thinking() {
  const lines = [
    "Reading your response as a reader would…",
    "Sitting with what you actually said…",
    "Thinking about what a reader needs here…",
  ];
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => setI((n) => (n + 1) % lines.length), 4000);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <div className="flex items-center gap-3 pl-1">
      <div className="flex items-center gap-1.5">
        <span className="thinking-dot h-2 w-2 rounded-full bg-[#8C3A2A]" />
        <span className="thinking-dot h-2 w-2 rounded-full bg-[#8C3A2A]" style={{ animationDelay: "0.2s" }} />
        <span className="thinking-dot h-2 w-2 rounded-full bg-[#8C3A2A]" style={{ animationDelay: "0.4s" }} />
      </div>
      <motion.span
        key={i}
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.7 }}
        transition={{ duration: 0.6 }}
        className="text-stone-500 text-sm italic font-serif-display"
      >
        {lines[i]}
      </motion.span>
    </div>
  );
}

// Chapter 6 — a subtle "thinking with you" cue shown AFTER the noticing beats,
// while the frozen engine finishes its developmental response. Conversational,
// not a performance.
function ThinkingWith() {
  return (
    <div className="flex items-center gap-3 pl-1" data-testid="preview-thinking-with">
      <div className="flex items-center gap-1.5">
        <span className="thinking-dot h-2 w-2 rounded-full bg-[#8C3A2A]" />
        <span className="thinking-dot h-2 w-2 rounded-full bg-[#8C3A2A]" style={{ animationDelay: "0.2s" }} />
        <span className="thinking-dot h-2 w-2 rounded-full bg-[#8C3A2A]" style={{ animationDelay: "0.4s" }} />
      </div>
      <span className="text-stone-500 text-sm italic font-serif-display">
        Thinking with you about your response…
      </span>
    </div>
  );
}

// Chapter 6 — the Pedagogical Noticing beats. Understanding → (pause) →
// Recognition (only if genuine) → (pause) → Bridge. Same voice and surface as
// the coaching that follows, so the encounter reads as one continuous
// conversation. Gentle fades only.
function NoticingBeats({ noticing, revealStage }) {
  const { understanding, recognition, bridge } = noticing || {};
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.6, ease: "easeOut" }}
      data-testid="preview-noticing"
      className="mt-5 bg-white border-l-2 border-[#8C3A2A] border-y border-r border-stone-200 rounded-sm p-5"
    >
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.18em] text-[#8C3A2A] font-mono-panel mb-3">
        <MessageSquareQuote className="h-3.5 w-3.5" />
        Your coach
      </div>
      <div className="space-y-3">
        <Beat show={revealStage >= 1} testid="preview-noticing-understanding">
          {understanding}
        </Beat>
        {recognition && (
          <Beat show={revealStage >= 2} testid="preview-noticing-recognition">
            {recognition}
          </Beat>
        )}
        {bridge && (
          <Beat show={revealStage >= 3} testid="preview-noticing-bridge">
            {bridge}
          </Beat>
        )}
      </div>
    </motion.div>
  );
}

function Beat({ show, testid, children }) {
  if (!show) return null;
  return (
    <motion.p
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.7, ease: "easeOut" }}
      data-testid={testid}
      className="text-stone-800 leading-relaxed text-[16px] font-serif-display"
    >
      {children}
    </motion.p>
  );
}
