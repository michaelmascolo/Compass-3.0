import { useState, useRef, useEffect, useCallback, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight,
  Loader2,
  Compass,
  MessageSquareQuote,
  X,
  CornerDownRight,
} from "lucide-react";
import { startPreview, getSession, interact, getNoticing, otStart, feedbackEvent } from "@/lib/api";
import { metacognitionSequence } from "@/lib/writerMetacognition";
import { findThesisRanges } from "@/lib/thesisMatch";
import ExperienceReflection from "@/components/ExperienceReflection";
import TeacherReflection from "@/components/TeacherReflection";
import OrganizingThought from "@/components/OrganizingThought";
import OTThinkingPanel from "@/components/OTThinkingPanel";
import StudentEntry from "@/components/StudentEntry";
import WelcomeScreen from "@/components/WelcomeScreen";
import WelcomeIntro from "@/components/feedback/WelcomeIntro";
import FeedbackButton from "@/components/feedback/FeedbackButton";
import FeedbackModal from "@/components/feedback/FeedbackModal";
import EarlyExitModal from "@/components/feedback/EarlyExitModal";

// Experience Compass public flow: Welcome (Ch3) -> Assignment (Ch4) -> Writing
// (Ch4 minimal interim) -> coaching -> reflection. The educator temporarily
// becomes the learner: they create an authentic assignment, then respond to it.
// Canonical v2 is the DEFAULT instructional architecture for all preview routes.
// Legacy (consolidated_v2) is retained only as a rollback: append ?legacy=1 to the
// URL to request it. WANT_CANONICAL drives both session creation and resume matching.
const WANT_CANONICAL = !new URLSearchParams(window.location.search).has("legacy");

// Canonical instructional orientation: CURRENT INSTRUCTIONAL FOCUS + vertical Writing Structure.
// All state is derived ONLY from authoritative backend fields (focus_of_work / established_structures).
const CANONICAL_STRUCTURES = ["Opening", "Thesis", "Elaboration", "Evidence / Example", "Conclusion"];

const OrientationMarker = ({ state }) => {
  if (state === "established")
    return <span aria-label="Established" className="text-emerald-700 font-bold w-3 inline-block text-center">✓</span>;
  if (state === "current")
    return <span aria-label="Current focus" className="text-[#8C3A2A] font-bold w-3 inline-block text-center">●</span>;
  return <span aria-label="Not currently in focus" className="text-stone-300 w-3 inline-block text-center">○</span>;
};

const CanonicalOrientation = ({ focus, description, thesis, thesisVerbatim, established }) => {
  const est = new Set(established || []);
  const stateOf = (name) => (name === focus ? "current" : est.has(name) ? "established" : "idle");
  const Row = ({ name, indented }) => {
    const s = stateOf(name);
    const slug = name.replace(/[^a-z]+/gi, "-").toLowerCase();
    return (
      <div
        data-testid={`writing-structure-row-${slug}`}
        aria-current={s === "current" ? "step" : undefined}
        className={`flex items-center gap-2 py-0.5 ${indented ? "ml-4" : ""} ${
          s === "current" ? "font-bold text-stone-900" : s === "established" ? "text-stone-600" : "text-stone-400"
        }`}
      >
        {indented && <span aria-hidden="true" className="text-stone-300 select-none">└──</span>}
        <OrientationMarker state={s} />
        <span className="text-[13px]">{name}</span>
        {s === "current" && (
          <span className="text-[9px] uppercase tracking-wider text-[#8C3A2A] border border-[#e0c4bd] rounded-sm px-1 py-px">
            focus
          </span>
        )}
      </div>
    );
  };
  return (
    <div data-testid="canonical-orientation" className="mb-4 space-y-3">
      <div
        data-testid="preview-focus-of-work"
        className="border border-stone-300 bg-stone-50 rounded-sm px-3 py-2"
      >
        <div className="text-[10px] uppercase tracking-[0.18em] text-stone-500 font-mono-panel">
          Current Instructional Focus
        </div>
        <div
          data-testid="preview-focus-of-work-structure"
          className="text-[15px] font-serif-display text-[#8C3A2A] font-bold mt-0.5 uppercase tracking-wide"
        >
          {focus}
        </div>
        {description && (
          <div className="text-[12px] text-stone-600 mt-0.5 leading-snug">{description}</div>
        )}
      </div>
      {thesis && (
        <div
          data-testid="preview-your-thesis"
          className="border border-[#e0c4bd] bg-[#fbf5f3] rounded-sm px-3 py-2"
        >
          <div className="text-[10px] uppercase tracking-[0.18em] text-[#8C3A2A] font-mono-panel">
            {thesisVerbatim ? "Your Thesis" : "Compass's current reading of your thesis"}
          </div>
          <div
            data-testid="preview-your-thesis-text"
            className="text-[13px] text-stone-800 mt-1 leading-snug italic font-serif-display"
          >
            {thesisVerbatim ? <>&ldquo;{thesis}&rdquo;</> : thesis}
          </div>
        </div>
      )}
      <div data-testid="writing-structure-map" className="border border-stone-200 rounded-sm px-3 py-2">
        <div className="text-[10px] uppercase tracking-[0.18em] text-stone-400 font-mono-panel mb-1">
          Writing Structure
        </div>
        <Row name="Opening" />
        <Row name="Thesis" />
        <div aria-hidden="true" className="ml-[3px] text-stone-400 text-[14px] leading-none" title="Thesis and Elaboration develop each other">⇅</div>
        <Row name="Elaboration" />
        <Row name="Evidence / Example" indented />
        <Row name="Conclusion" />
        <div className="mt-2 pt-1.5 border-t border-stone-100 text-[10px] text-stone-400 flex flex-wrap gap-x-3 gap-y-0.5">
          <span><span className="text-emerald-700 font-bold">✓</span> Established</span>
          <span><span className="text-[#8C3A2A] font-bold">●</span> Current</span>
          <span><span className="text-stone-300">○</span> Not in focus</span>
        </div>
      </div>
    </div>
  );
};

// Render the draft with the recognized thesis sentence(s) wrapped in a subtle
// highlight. Used as a transparent-text overlay behind the editable textarea so the
// tint sits under the learner's own words without altering them.
function renderThesisSegments(text, ranges) {
  if (!ranges || ranges.length === 0) return text;
  const out = [];
  let cursor = 0;
  ranges.forEach(([s, e], i) => {
    if (s > cursor) out.push(text.slice(cursor, s));
    out.push(
      <mark
        key={`thesis-${i}`}
        data-testid="thesis-highlight"
        className="bg-[#f3e2c0] text-transparent rounded-[2px] box-decoration-clone"
      >
        {text.slice(s, e)}
      </mark>
    );
    cursor = e;
  });
  if (cursor < text.length) out.push(text.slice(cursor));
  return out;
}

export default function PublicPreview({ mode = "ot" }) {
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
  // Organizing Thought (Phase 2) — the five-object prewriting flow, before Writing.
  const [otPhase, setOtPhase] = useState(false);
  const [otData, setOtData] = useState(null);
  // Post-experience: the teacher chooses to review their own experience.
  const [reviewingAsTeacher, setReviewingAsTeacher] = useState(false);
  // Chapter 6 — Pedagogical Noticing: the "I understand you" beats shown before
  // the frozen engine's developmental response, on the FIRST encounter only.
  const [noticing, setNoticing] = useState(null); // {observations: [obs1, obs2?]}
  const [revealStage, setRevealStage] = useState(0); // 0 none · 1 first observation · 2 second observation
  const submitAtRef = useRef(0); // when the learner submitted (to pace the first observation ~3-5s)
  // Compass Developmental Feedback System.
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const [earlyExitOpen, setEarlyExitOpen] = useState(false);

  const isProcessing = !!session?.turns?.some((t) => t.status === "processing");
  const busy = starting || sending || isProcessing;

  const allTurns = session?.turns || [];
  const studentTurns = allTurns.filter((t) => t.role === "student");
  const completedAi = allTurns.filter((t) => t.role === "ai" && t.status === "complete" && t.content);
  const activeCoaching = completedAi.length ? completedAi[completedAi.length - 1] : null;
  // Highlight, in place, the sentence(s) Compass currently recognizes as the thesis —
  // always the same text shown in the YOUR THESIS panel (activeCoaching.current_thesis).
  const docRef = useRef(null);
  const highlightRef = useRef(null);
  const activeThesis = activeCoaching?.current_thesis || "";
  const thesisRanges = useMemo(() => findThesisRanges(draft, activeThesis), [draft, activeThesis]);
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
  // Mode separation: 'teacher' = teacher-simulation wrapper (Experience Compass
  // welcome + create-assignment + teacher reflection). 'writing' / 'ot' = GENUINE
  // student entries — the learner completes an assignment they were given, with
  // no teacher framing.
  const isTeacher = mode === "teacher";
  const isStudent = !isTeacher;
  const hasStudentTurn = studentTurns.length > 0;
  const showWelcome = isTeacher && !entered && !session;
  const showAssignment = isTeacher && entered && !session && !writingStarted && !otPhase;
  const showStudentEntry = isStudent && !session && !writingStarted && !otPhase && !hasStudentTurn;
  const showOT = otPhase && !hasStudentTurn;
  const showWriting = writingStarted && !hasStudentTurn && !otPhase;

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

  // Reveal the interim observations as a paced, grounded sequence. The FIRST
  // observation is held until ~6.5s (5–8s window) after the learner submitted (so
  // it reads as a genuine reading of their writing, never an instant message); a
  // SECOND grounded observation, if present, follows ~3s later. They never delay
  // the full coaching response, which replaces them when reasoning completes.
  useEffect(() => {
    if (!noticing || !(noticing.observations || []).length) {
      setRevealStage(0);
      return;
    }
    const elapsed = Date.now() - (submitAtRef.current || 0);
    const firstDelay = Math.max(0, 6500 - elapsed); // ~5-8s before the first observation
    const t1 = setTimeout(() => setRevealStage((s) => (s < 1 ? 1 : s)), firstDelay);
    const t2 = setTimeout(() => setRevealStage((s) => (s < 2 ? 2 : s)), firstDelay + 3000);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [noticing]);

  // Student entry → create/resume the session with the student's OWN assignment
  // (the task they were given), then enter the selected student workflow. Same
  // session model; no teacher-experience state attached.
  const enterStudent = useCallback(async (assignmentText) => {
    if (starting || !assignmentText.trim()) return;
    setStarting(true);
    try {
      const s = await startPreview({ assignment: assignmentText.trim(), canonical: WANT_CANONICAL });
      setSession(s);
      setAssignment(assignmentText.trim());
      if (mode === "ot") {
        const ot = await otStart(s.id);
        setOtData(ot);
        setOtPhase(true);
      } else {
        setWritingStarted(true);
      }
      try {
        localStorage.setItem("compass_student_session", JSON.stringify({ id: s.id, mode }));
      } catch (e) { /* ignore */ }
    } catch (e) {
      /* stay on entry */
    } finally {
      setStarting(false);
    }
  }, [starting, mode]);

  // My Plan reached sufficiency → hand the student into the EXISTING Writing
  // workflow on the same session. Capture the final OT state so the Writing
  // context panel can display it (session.ot also covers refresh/resume).
  const finishOrganizing = useCallback((finalOt) => {
    if (finalOt) setOtData(finalOt);
    setOtPhase(false);
    setWritingStarted(true);
  }, []);

  // Writing Screen submit — reuse the session when it already exists (came via
  // Organizing Thought); otherwise (direct Writing entry) create it now with the
  // educator's authentic assignment as the authoritative task. Submits the
  // student's EXACT response (validated on trimmed value, transmitted unaltered).
  const submitResponse = useCallback(async () => {
    if (response.trim().length < 15 || starting) return;
    setStarting(true);
    submitAtRef.current = Date.now();
    setNoticing(null);
    setRevealStage(0);
    try {
      let s = session;
      if (!s) {
        s = await startPreview({ assignment: assignment.trim(), canonical: WANT_CANONICAL });
        setSession(s);
      }
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
  }, [response, starting, session, assignment]);

  // "Try another paragraph" — return to a CLEARED Assignment Screen (never the
  // Welcome Screen during the same visit) and begin a completely fresh session.
  const restart = useCallback(() => {
    setSession(null);
    setAssignment("");
    setResponse("");
    setDraft("");
    setWritingStarted(false);
    setOtPhase(false);
    setOtData(null);
    setCardOpen(false);
    setOpenCoachingId(null);
    setReplyOpen(false);
    setReply("");
    setReviewingAsTeacher(false);
    setNoticing(null);
    setRevealStage(0);
    try { localStorage.removeItem("compass_student_session"); localStorage.removeItem("compass_ot_session"); } catch (e) { /* ignore */ }
  }, []);

  // Resume an in-progress STUDENT session on refresh/return. The session id is
  // remembered client-side WITH its mode, so we never pull an incompatible
  // session (e.g. a teacher-preview or other-mode session) into this mode.
  useEffect(() => {
    if (!isStudent) return;
    let raw;
    try { raw = localStorage.getItem("compass_student_session"); } catch (e) { raw = null; }
    if (!raw) return;
    let parsed;
    try { parsed = JSON.parse(raw); } catch (e) { parsed = null; }
    if (!parsed || !parsed.id || parsed.mode !== mode) return;
    getSession(parsed.id)
      .then((s) => {
        if (!s) {
          try { localStorage.removeItem("compass_student_session"); } catch (e) { /* ignore */ }
          return;
        }
        // Honor the ?canon flag: never resume a session whose canonical state does
        // not match the current request. Otherwise a stale consolidated_v2 (legacy)
        // session would be restored under ?canon=1, silently bypassing the canonical
        // path (no Focus of Work, legacy Explanation teaching). Drop it and let the
        // learner start a fresh session with the correct reasoning mode.
        const isCanon = s.reasoning_mode === "canonical_v2";
        if (WANT_CANONICAL !== isCanon) {
          try { localStorage.removeItem("compass_student_session"); } catch (e) { /* ignore */ }
          return;
        }
        const students = (s.turns || []).filter((t) => t.role === "student");
        setSession(s);
        feedbackEvent(s.id, "resume", {});
        setAssignment(s.assignment || "");
        if (s.ot) setOtData(s.ot);
        if (students.length) {
          setDraft(students[students.length - 1].content || "");
        } else if (mode === "ot" && s.ot && !s.ot.handoff_ready) {
          setOtData(s.ot);
          setOtPhase(true);
        } else {
          setWritingStarted(true);
        }
      })
      .catch(() => {
        try { localStorage.removeItem("compass_student_session"); } catch (e) { /* ignore */ }
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // --- Automatic developmental analytics (supplement, never replace, feedback) ---
  useEffect(() => {
    if (session?.id && otData?.current_stage) feedbackEvent(session.id, "stage_enter", { stage: `ot:${otData.current_stage}` });
  }, [otData?.current_stage, session?.id]);
  useEffect(() => {
    if (session?.id && writingStarted) feedbackEvent(session.id, "stage_enter", { stage: "writing" });
  }, [writingStarted, session?.id]);
  useEffect(() => {
    if (session?.id && inReflection) feedbackEvent(session.id, "stage_enter", { stage: "reflection" });
  }, [inReflection, session?.id]);
  // At the natural END of the experience, invite developmental feedback once.
  const endPrompted = useRef(false);
  useEffect(() => {
    if (inReflection && !reviewingAsTeacher && !endPrompted.current) {
      endPrompted.current = true;
      setFeedbackOpen(true);
    }
  }, [inReflection, reviewingAsTeacher]);
  // Record real tab-close / navigation as a best-effort early-exit signal.
  useEffect(() => {
    const onUnload = () => {
      if (session?.id && !inReflection && (hasStudentTurn || otPhase || writingStarted)) {
        try {
          const url = `${process.env.REACT_APP_BACKEND_URL}/api/feedback/${session.id}/event`;
          navigator.sendBeacon?.(url, new Blob([JSON.stringify({ event: "early_exit_unload", data: {} })], { type: "application/json" }));
        } catch (e) { /* ignore */ }
      }
    };
    window.addEventListener("beforeunload", onUnload);
    return () => window.removeEventListener("beforeunload", onUnload);
  }, [session?.id, inReflection, hasStudentTurn, otPhase, writingStarted]);

  const dirty = draft.trim() !== (studentTurns[studentTurns.length - 1]?.content || "").trim();

  // Fire the interim-observations side channel for the CURRENT wait (every turn,
  // not just the first). Resets pacing so the grounded observations appear ~3.5s
  // and ~7s into the wait while the deeper reasoning completes.
  const fireNoticing = useCallback((sid) => {
    submitAtRef.current = Date.now();
    setNoticing(null);
    setRevealStage(0);
    getNoticing(sid)
      .then((res) => {
        if (res && res.ok) setNoticing(res);
      })
      .catch(() => {});
  }, []);

  const sendRevision = useCallback(async () => {
    if (!draft.trim() || busy || !session || !dirty) return;
    setSending(true);
    try {
      const updated = await interact(session.id, { kind: "revise", content: draft.trim() });
      setSession(updated);
      setOpenCoachingId(null);
      fireNoticing(session.id);
    } catch (e) {
      /* polling / retry */
    } finally {
      setSending(false);
    }
  }, [draft, busy, session, dirty, fireNoticing]);

  const sendExplain = useCallback(async () => {
    if (busy || !session) return;
    feedbackEvent(session.id, "help_requested", { where: "writing" });
    setSending(true);
    try {
      const updated = await interact(session.id, {
        kind: "explain",
        content: "Can you say a little more about what you mean?",
      });
      setSession(updated);
      fireNoticing(session.id);
    } catch (e) {
      /* ignore */
    } finally {
      setSending(false);
    }
  }, [busy, session, fireNoticing]);

  const sendReply = useCallback(async () => {
    if (!reply.trim() || busy || !session) return;
    setSending(true);
    const content = reply.trim();
    setReply("");
    setReplyOpen(false);
    try {
      const updated = await interact(session.id, { kind: "answer", content });
      setSession(updated);
      fireNoticing(session.id);
    } catch (e) {
      /* ignore */
    } finally {
      setSending(false);
    }
  }, [reply, busy, session, fireNoticing]);

  const wordCount = draft.trim() ? draft.trim().split(/\s+/).length : 0;

  const wide = showOT || (showWriting && !!(otData || session?.ot));
  const containerW = wide ? "max-w-5xl" : "max-w-2xl";
  const experienceActive = !!(session || otPhase || writingStarted || hasStudentTurn);
  const onEntryScreen = showStudentEntry || showAssignment;
  return (
    <div className="min-h-screen paper-grain flex flex-col items-center">
      {!showWelcome && (
        <header className={`w-full ${containerW} flex items-center justify-between px-6 py-5`}>
          <div className="flex items-center gap-2 font-serif-display text-lg text-stone-800">
            <Compass className="h-5 w-5 text-[#8C3A2A]" />
            Compass
            <span
              data-testid="preview-reasoning-mode-badge"
              title="Active instructional reasoning mode (developer indicator)"
              className="ml-1 text-[9px] font-mono-panel uppercase tracking-[0.14em] text-stone-400 border border-stone-200 rounded-sm px-1.5 py-0.5"
            >
              {(session?.reasoning_mode === "canonical_v2" || (!session && WANT_CANONICAL))
                ? "Canonical v2"
                : "Legacy v2"}
            </span>
          </div>
          {isStudent && experienceActive && !inReflection && (
            <button
              onClick={() => setEarlyExitOpen(true)}
              data-testid="exit-experience-button"
              className="inline-flex items-center gap-1.5 text-[11px] font-mono-panel uppercase tracking-[0.14em] text-stone-400 hover:text-[#8C3A2A] transition-colors"
            >
              <X className="h-3.5 w-3.5" /> Exit
            </button>
          )}
        </header>
      )}

      <main className={`w-full ${containerW} flex-1 flex flex-col px-6 pb-12`}>
        {onEntryScreen && <WelcomeIntro />}
        {showWelcome ? (
          <WelcomeScreen onBegin={() => setEntered(true)} />
        ) : showAssignment ? (
          <AssignmentScreen
            assignment={assignment}
            setAssignment={setAssignment}
            onContinue={() => setWritingStarted(true)}
            onBack={() => setEntered(false)}
          />
        ) : showStudentEntry ? (
          <StudentEntry
            mode={mode}
            initialAssignment={assignment}
            onSubmit={enterStudent}
            submitting={starting}
          />
        ) : showOT ? (
          <OrganizingThought
            sessionId={session?.id}
            initialOt={otData}
            onComplete={finishOrganizing}
          />
        ) : showWriting ? (
          <WritingScreen
            assignment={assignment}
            ot={otData || session?.ot}
            response={response}
            setResponse={setResponse}
            onSubmit={submitResponse}
            onBack={() => {
              setWritingStarted(false);
              if (mode === "ot" && session) setOtPhase(true);
              else if (isStudent) setSession(null);
            }}
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
              onReviewAsTeacher={isTeacher ? () => setReviewingAsTeacher(true) : undefined}
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

            {/* The passage — document canvas, editable in place. A transparent-text
                overlay sits behind the textarea to tint the recognized thesis. */}
            <div className="relative bg-white border border-stone-300 rounded-sm">
              <div
                ref={highlightRef}
                aria-hidden="true"
                data-testid="preview-document-highlight"
                className="absolute inset-0 overflow-hidden pointer-events-none px-7 sm:px-10 py-8 text-[17px] leading-9 font-serif-display whitespace-pre-wrap break-words text-transparent"
              >
                {renderThesisSegments(draft, thesisRanges)}
                {"\n"}
              </div>
              <textarea
                data-testid="preview-document"
                ref={docRef}
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onScroll={() => {
                  if (highlightRef.current && docRef.current)
                    highlightRef.current.scrollTop = docRef.current.scrollTop;
                }}
                placeholder="Your response…"
                className="relative block w-full min-h-[34vh] bg-transparent px-7 sm:px-10 py-8 text-[17px] leading-9 text-stone-900 placeholder:text-stone-400 outline-none resize-none custom-scroll font-serif-display whitespace-pre-wrap break-words"
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
            {/* Interim observations: grounded "reading" of the student's latest
                writing, shown during the reasoning wait on EVERY turn. */}
            {noticing && (noticing.observations || []).length > 0 && (
              <NoticingBeats noticing={noticing} revealStage={revealStage} />
            )}

            {busy && (
              <div data-testid="preview-thinking" className="mt-4">
                {noticing && (noticing.observations || []).length > 0 ? <ThinkingWith /> : <Thinking />}
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
                  {activeCoaching.focus_of_work && (
                    <CanonicalOrientation
                      focus={activeCoaching.focus_of_work}
                      description={activeCoaching.focus_description}
                      thesis={activeCoaching.current_thesis}
                      thesisVerbatim={activeCoaching.thesis_is_verbatim}
                      established={activeCoaching.established_structures || []}
                    />
                  )}
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

      {experienceActive && !earlyExitOpen && (
        <FeedbackButton onClick={() => setFeedbackOpen(true)} />
      )}
      {feedbackOpen && session?.id && (
        <FeedbackModal sessionId={session.id} onClose={() => setFeedbackOpen(false)} />
      )}
      {earlyExitOpen && (
        <EarlyExitModal
          sessionId={session?.id}
          onLeave={() => { setEarlyExitOpen(false); restart(); }}
        />
      )}
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
function WritingScreen({ assignment, ot, response, setResponse, onSubmit, onBack, submitting }) {
  const meaningful = response.trim().length >= 15;
  const hasOt = !!ot;
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className={`flex-1 flex flex-col w-full py-10 ${hasOt ? "max-w-5xl" : "max-w-xl mx-auto justify-center"}`}
      data-testid="writing-screen"
    >
      <div className={hasOt ? "grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_20rem] gap-6 lg:gap-10" : ""}>
        <div className="min-w-0 flex flex-col">
      <h1 className="font-serif-display text-3xl sm:text-4xl leading-snug text-stone-900">
        Write your response
      </h1>
      <p className="text-stone-600 mt-4 text-[15px] leading-relaxed">
        Respond to your assignment in one thoughtful paragraph. Write a genuine first draft. Do not
        try to make it perfect before Compass sees it.
      </p>

      {!hasOt && (
        <>
          <p className="mt-7 font-mono-panel text-[11px] uppercase tracking-[0.14em] text-stone-500 mb-1.5">
            Your assignment
          </p>
          <div
            data-testid="writing-assignment-display"
            className="bg-[#faf9f6] border border-stone-200 rounded-sm p-4 text-[15px] leading-relaxed text-stone-800 whitespace-pre-wrap font-serif-display"
          >
            {assignment}
          </div>
        </>
      )}

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
        </div>
        {hasOt && (
          <OTThinkingPanel
            ot={ot}
            only={["__original", "the_assignment", "my_current_answer", "my_plan"]}
            title="From your planning"
          />
        )}
      </div>
    </motion.div>
  );
}

// The wait period is now instructional. Instead of a generic loading state, it
// models how experienced writers think (writer metacognition), then bridges to
// Compass's instructional focus. It NEVER narrates Compass's internal reasoning.
function MetacognitionCue({ testid, toFocus }) {
  const seqRef = useRef(null);
  if (seqRef.current === null) {
    seqRef.current = metacognitionSequence({ toFocus, general: toFocus ? 3 : 4 });
  }
  const seq = seqRef.current;
  const [i, setI] = useState(0);
  useEffect(() => {
    const t = setInterval(() => {
      // When bridging to focus, hold on the final focus line; otherwise cycle.
      setI((n) => (toFocus ? Math.min(n + 1, seq.length - 1) : (n + 1) % seq.length));
    }, 4800);
    return () => clearInterval(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [seq.length, toFocus]);
  const isFocus = toFocus && i === seq.length - 1;
  return (
    <div className="flex items-start gap-3 pl-1" data-testid={testid}>
      <div className="flex items-center gap-1.5 mt-2">
        <span className="thinking-dot h-2 w-2 rounded-full bg-[#8C3A2A]" />
        <span className="thinking-dot h-2 w-2 rounded-full bg-[#8C3A2A]" style={{ animationDelay: "0.2s" }} />
        <span className="thinking-dot h-2 w-2 rounded-full bg-[#8C3A2A]" style={{ animationDelay: "0.4s" }} />
      </div>
      <motion.p
        key={i}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: isFocus ? 0.9 : 0.72, y: 0 }}
        transition={{ duration: 0.7, ease: "easeOut" }}
        data-testid={`${testid}-line`}
        className={`text-sm leading-relaxed font-serif-display max-w-md ${isFocus ? "text-[#8C3A2A] italic" : "text-stone-600"}`}
      >
        {seq[i]}
      </motion.p>
    </div>
  );
}

// Shown when interim observations have NOT arrived yet: pure writer metacognition
// (keeps cycling until the acknowledgement or coaching appears).
function Thinking() {
  return <MetacognitionCue testid="preview-thinking-cue" toFocus={false} />;
}

// Chapter 6 — shown AFTER the grounded acknowledgement (the interim observations).
// Progresses from writer metacognition toward Compass's instructional focus while
// the frozen engine finishes. Never narrates Compass's internal reasoning.
function ThinkingWith() {
  return <MetacognitionCue testid="preview-thinking-with" toFocus={true} />;
}

// The interim observations. Grounded observation 1 (emerging central idea) →
// (pause) → grounded observation 2 (the structural relationship/distinction),
// if present. Same voice and surface as the coaching that follows, so the
// encounter reads as one continuous, developing line of instruction.
function NoticingBeats({ noticing, revealStage }) {
  const observations = (noticing && noticing.observations) || [];
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
        {observations[0] && (
          <Beat show={revealStage >= 1} testid="preview-noticing-observation-1">
            {observations[0]}
          </Beat>
        )}
        {observations[1] && (
          <Beat show={revealStage >= 2} testid="preview-noticing-observation-2">
            {observations[1]}
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
