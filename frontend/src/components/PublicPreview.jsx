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
import { startPreview, getSession, interact } from "@/lib/api";
import ExperienceReflection from "@/components/ExperienceReflection";
import WelcomeScreen from "@/components/WelcomeScreen";

const PASSAGE_TYPES = ["Let Compass infer it", "Introduction", "Body paragraph", "Transition", "Conclusion", "Other"];

// A faithful miniature of the canonical Student Workspace: the passage is the
// center, editable in place, and Compass anchors ONE coaching note to it. No
// chat column, no scoring, no jargon, no developer panel.
export default function PublicPreview() {
  const [session, setSession] = useState(null);
  const [seed, setSeed] = useState("");
  const [draft, setDraft] = useState("");
  const [starting, setStarting] = useState(false);
  const [sending, setSending] = useState(false);
  const [passageType, setPassageType] = useState("Let Compass infer it");
  const [essayAbout, setEssayAbout] = useState("");
  const [cardOpen, setCardOpen] = useState(false);
  const [openCoachingId, setOpenCoachingId] = useState(null);
  const [replyOpen, setReplyOpen] = useState(false);
  const [reply, setReply] = useState("");
  // Chapter 3 — Welcome Screen gate. Shows before the seed screen on first entry
  // this visit; "Try another paragraph" (restart) does NOT re-show it.
  const [entered, setEntered] = useState(false);

  const isProcessing = !!session?.turns?.some((t) => t.status === "processing");
  const busy = starting || sending || isProcessing;

  const allTurns = session?.turns || [];
  const studentTurns = allTurns.filter((t) => t.role === "student");
  const completedAi = allTurns.filter((t) => t.role === "ai" && t.status === "complete" && t.content);
  const activeCoaching = completedAi.length ? completedAi[completedAi.length - 1] : null;
  const started = !!session;
  const reviseCount = studentTurns.filter((t) => t.kind === "revise").length;
  // Completion is driven ONLY by the single-objective experience_control phase,
  // never by an AI turn count.
  const phase = session?.experience_control?.phase || "active";
  const inReflection = phase === "reflection";
  const showWelcome = !entered && !started;

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

  // A new coaching target auto-surfaces its marker.
  useEffect(() => {
    if (activeCoaching) {
      setCardOpen(true);
      setOpenCoachingId(null);
    }
  }, [activeCoaching?.id]);

  const beginPreview = useCallback(async () => {
    if (!seed.trim() || starting) return;
    setStarting(true);
    try {
      const s = await startPreview({ essay_about: essayAbout.trim(), passage_type: passageType });
      const updated = await interact(s.id, { kind: "writing", content: seed.trim() });
      setDraft(seed.trim());
      setSession(updated);
    } catch (e) {
      /* stay on seed screen */
    } finally {
      setStarting(false);
    }
  }, [seed, starting, essayAbout, passageType]);

  // "Try another paragraph" — begin a COMPLETELY fresh preview session. Never
  // reuse or continue the completed one.
  const restart = useCallback(() => {
    setSession(null);
    setSeed("");
    setDraft("");
    setPassageType("Let Compass infer it");
    setEssayAbout("");
    setCardOpen(false);
    setOpenCoachingId(null);
    setReplyOpen(false);
    setReply("");
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
        ) : !started ? (
          <SeedScreen
            seed={seed}
            setSeed={setSeed}
            onBegin={beginPreview}
            starting={starting}
            passageType={passageType}
            setPassageType={setPassageType}
            essayAbout={essayAbout}
            setEssayAbout={setEssayAbout}
          />
        ) : inReflection ? (
          <ExperienceReflection
            reflection={session?.experience_control?.reflection}
            draft={draft}
            onRestart={restart}
          />
        ) : (
          <div className="flex-1 flex flex-col py-4">
            {started && (
              <p
                data-testid="preview-revision-progress"
                className="font-mono-panel text-[10px] uppercase tracking-[0.18em] text-stone-400 mb-3"
              >
                {reviseCount > 0 ? `Revision ${reviseCount}` : "Your passage"}
              </p>
            )}

            {/* The passage — document canvas, editable in place. */}
            <div className="relative bg-white border border-stone-300 rounded-sm">
              <textarea
                data-testid="preview-document"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder="Your passage…"
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
                    title="Your coach has a note on this passage"
                  >
                    <span className="coach-pulse h-3.5 w-3.5 rounded-full bg-[#8C3A2A] ring-4 ring-[#8C3A2A]/15" />
                    <span className="hidden group-hover:inline-block text-[10px] font-mono-panel uppercase tracking-[0.15em] text-[#8C3A2A] bg-white border border-[#8C3A2A]/30 rounded-sm px-2 py-1">
                      Coach note
                    </span>
                  </motion.button>
                )}
              </AnimatePresence>
            </div>

            {busy && (
              <div data-testid="preview-thinking" className="mt-4">
                <Thinking />
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
                      Revise your passage above, then send it back.
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
                        placeholder="Think aloud to your coach (this doesn't change your passage)…"
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
                Change something in your passage to send a revision.
              </p>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

function SeedScreen({ seed, setSeed, onBegin, starting, passageType, setPassageType, essayAbout, setEssayAbout }) {
  const empty = !seed.trim();
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="flex-1 flex flex-col justify-center max-w-xl mx-auto w-full py-10"
      data-testid="preview-seed-screen"
    >
      <h1 className="font-serif-display text-3xl sm:text-4xl leading-snug text-stone-900">
        Try Compass with a short piece of Grade 9 writing.
      </h1>
      <p className="text-stone-600 mt-4 text-[15px] leading-relaxed">
        Choose any essay topic. Write or paste a short passage as though it were part of a Grade 9
        student’s essay. You might enter an introduction, a body paragraph, a transition, or a
        conclusion.
      </p>
      <p className="text-stone-500 mt-2 text-[14px] leading-relaxed">
        The writing can be imperfect. The purpose is to experience how Compass helps a student
        develop it — you'll revise the passage right on the page.
      </p>

      <div className="mt-7">
        <label className="block font-mono-panel text-[11px] uppercase tracking-[0.14em] text-stone-500 mb-1.5">
          What is the essay about? <span className="text-stone-400 normal-case tracking-normal">Optional</span>
        </label>
        <input
          data-testid="preview-essay-about"
          value={essayAbout}
          onChange={(e) => setEssayAbout(e.target.value)}
          placeholder="Briefly describe the topic or assignment."
          className="w-full bg-white border border-stone-300 rounded-sm px-3.5 py-2.5 text-[15px] text-stone-900 placeholder:text-stone-400 outline-none focus:ring-1 focus:ring-[#8C3A2A] focus:border-[#8C3A2A] transition-colors"
        />
      </div>

      <div className="mt-4">
        <label className="block font-mono-panel text-[11px] uppercase tracking-[0.14em] text-stone-500 mb-1.5">
          What kind of passage are you entering? <span className="text-stone-400 normal-case tracking-normal">Optional</span>
        </label>
        <select
          data-testid="preview-passage-type"
          value={passageType}
          onChange={(e) => setPassageType(e.target.value)}
          className="w-full bg-white border border-stone-300 rounded-sm px-3.5 py-2.5 text-[15px] text-stone-900 outline-none focus:ring-1 focus:ring-[#8C3A2A] focus:border-[#8C3A2A] transition-colors"
        >
          {PASSAGE_TYPES.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      <textarea
        data-testid="preview-seed-input"
        value={seed}
        onChange={(e) => setSeed(e.target.value)}
        rows={7}
        autoFocus
        placeholder="Enter a short passage here…"
        className="mt-5 w-full bg-white border border-stone-300 rounded-sm p-5 text-[16px] leading-8 text-stone-900 placeholder:text-stone-400 outline-none focus:ring-1 focus:ring-stone-900 focus:border-stone-900 transition-colors resize-none"
      />
      <button
        onClick={onBegin}
        data-testid="preview-begin-button"
        disabled={empty || starting}
        className="mt-5 self-start group inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-7 py-3 rounded-sm font-medium tracking-wide hover:bg-[#6B2C20] enabled:hover:-translate-y-px transition-[background-color,transform] disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {starting ? (
          <>
            <Loader2 className="h-4 w-4 animate-spin" />
            Reading…
          </>
        ) : (
          <>
            Try Compass
            <ArrowRight className="h-4 w-4 transition-transform group-enabled:group-hover:translate-x-0.5" />
          </>
        )}
      </button>
      {empty && (
        <span className="text-stone-400 text-[13px] mt-2" data-testid="preview-empty-hint">
          Enter a short passage to continue.
        </span>
      )}
    </motion.div>
  );
}

function Thinking() {
  const lines = [
    "Reading your passage as a reader would…",
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
