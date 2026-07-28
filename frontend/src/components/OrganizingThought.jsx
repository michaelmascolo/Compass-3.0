import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Compass, ArrowRight, ArrowLeft, Loader2, Check, MessageSquareQuote, AlertCircle,
} from "lucide-react";
import { otStart, otSaveObject, otInteract, otAdvance, otHandoff } from "@/lib/api";
import OTThinkingPanel from "@/components/OTThinkingPanel";
import MyIdeasWorkflow from "@/components/MyIdeasWorkflow";

// Organizing Thought — five persistent objects the student builds BEFORE Writing.
// Student-visible names are fixed; no technical labels, classifications, or metadata.
const STAGE_ORDER = ["the_assignment", "questions", "my_ideas", "my_current_answer", "my_plan"];
const STAGE_META = {
  the_assignment: {
    name: "The Assignment",
    task: "What is this assignment actually asking you to do? Capture the topic, the intellectual task, any separate parts, and the constraints that matter (audience, evidence, sources, format, length, scope, perspective).",
    placeholder: "In your own words, what does this assignment require?",
  },
  questions: {
    name: "Questions I Need to Answer",
    task: "What questions would you need to answer to do this well? Keep the ones that matter for this assignment — not every possible question.",
    placeholder: "List the questions you need to answer…",
  },
  my_ideas: {
    name: "My Ideas",
    task: "Work out your own ideas that help answer your questions. An idea is your own thinking — not copied wording or a list of facts.",
    placeholder: "What are your ideas so far, and which question does each help answer?",
  },
  my_current_answer: {
    name: "My Current Answer",
    task: "Pull your ideas together into your best answer to the assignment right now. It can be provisional — it does not need to be a polished thesis.",
    placeholder: "What is your best current answer to the assignment?",
  },
  my_plan: {
    name: "My Plan",
    task: "Plan how to help a reader understand your answer. What should come first, next, and why? Let the order follow your answer — not a fixed template.",
    placeholder: "How will you order your ideas so a reader can follow your answer?",
  },
};

export default function OrganizingThought({ sessionId, initialOt, onComplete }) {
  const [ot, setOt] = useState(initialOt || null);
  const [active, setActive] = useState((initialOt && initialOt.current_stage) || "the_assignment");
  const [drafts, setDrafts] = useState(() => (initialOt && initialOt.objects) || {});
  const [coach, setCoach] = useState(null); // { decision, message }
  const [sending, setSending] = useState(false);
  const [moving, setMoving] = useState(false);

  useEffect(() => {
    if (ot) return;
    otStart(sessionId).then((o) => {
      setOt(o);
      setActive(o.current_stage || "the_assignment");
      setDrafts(o.objects || {});
    });
  }, [sessionId, ot]);

  const meta = STAGE_META[active];
  const draft = drafts[active] || "";
  const setDraft = (v) => setDrafts((d) => ({ ...d, [active]: v }));
  const isMyIdeas = active === "my_ideas";
  const hasQuestions = !!((ot?.objects?.questions) || "").trim();

  // Autosave the student's own words so nothing is lost on leave/return.
  const saveDraft = useCallback(async () => {
    const v = drafts[active];
    if (!v || !v.trim()) return;
    try {
      const o = await otSaveObject(sessionId, active, v);
      setOt(o);
    } catch (e) {
      /* non-blocking */
    }
  }, [drafts, active, sessionId]);
  const idx = STAGE_ORDER.indexOf(active);
  const isLast = idx === STAGE_ORDER.length - 1;
  const sufficient = ot && ot.status && ot.status[active] === "sufficient";
  const needsReview = ot && (ot.needs_review || []).includes(active);
  const busy = sending || moving;

  const share = useCallback(async () => {
    if (!draft.trim() || busy) return;
    setSending(true);
    setCoach(null);
    try {
      const res = await otInteract(sessionId, active, draft);
      setOt(res.ot);
      setCoach({ decision: res.decision, message: res.message });
    } catch (e) {
      setCoach({ decision: "ask", message: "Something interrupted us — try sharing that again." });
    } finally {
      setSending(false);
    }
  }, [draft, busy, sessionId, active]);

  const goTo = useCallback(async (stage) => {
    if (busy || stage === active) return;
    setMoving(true);
    try {
      if (draft.trim()) await otSaveObject(sessionId, active, draft);
      const o = await otAdvance(sessionId, stage);
      setOt(o);
      setDrafts(o.objects || {});
      setActive(stage);
      setCoach(null);
    } finally {
      setMoving(false);
    }
  }, [busy, active, draft, sessionId]);

  // My Ideas depends on the student's questions. If they reach it with none,
  // send them back to build their questions first.
  useEffect(() => {
    if (ot && active === "my_ideas" && !((ot.objects?.questions) || "").trim() && !busy) {
      goTo("questions");
    }
  }, [ot, active, busy, goTo]);

  const proceed = useCallback(async () => {
    if (busy) return;
    setMoving(true);
    try {
      let latest = ot;
      if (draft.trim()) latest = await otSaveObject(sessionId, active, draft);
      if (isLast) {
        const handoffOt = await otHandoff(sessionId);
        onComplete(handoffOt || latest);
        return;
      }
      const next = STAGE_ORDER[idx + 1];
      const o = await otAdvance(sessionId, next);
      setOt(o);
      setDrafts(o.objects || {});
      setActive(next);
      setCoach(null);
    } finally {
      setMoving(false);
    }
  }, [busy, draft, sessionId, active, isLast, idx, onComplete, ot]);

  const canProceed = sufficient || (coach && coach.decision === "proceed");

  if (!ot) {
    return (
      <div className="flex-1 flex items-center justify-center py-16 text-stone-500">
        <Loader2 className="h-5 w-5 animate-spin text-[#8C3A2A]" />
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
      className="flex-1 flex flex-col py-4" data-testid="organizing-thought"
    >
      <p className="font-mono-panel text-[10px] uppercase tracking-[0.18em] text-stone-400 mb-3">
        Organizing your thinking
      </p>

      <div className="grid grid-cols-1 lg:grid-cols-[minmax(0,1fr)_20rem] gap-6 lg:gap-10">
        <div className="min-w-0 flex flex-col">
      {/* Stage rail — revisitable */}
      <div className="flex flex-wrap gap-2 mb-6" data-testid="ot-stage-rail">
        {STAGE_ORDER.map((s, i) => {
          const done = ot.status && ot.status[s] === "sufficient";
          const flagged = (ot.needs_review || []).includes(s);
          const isActive = s === active;
          return (
            <button
              key={s}
              onClick={() => goTo(s)}
              data-testid={`ot-stage-${s}`}
              disabled={busy}
              className={`inline-flex items-center gap-1.5 text-left rounded-sm border px-3 py-2 transition-colors
                ${isActive ? "border-[#8C3A2A] bg-[#8C3A2A]/[0.04]" : "border-stone-200 bg-white hover:border-stone-400"}`}
            >
              <span className={`font-mono-panel text-[10px] ${isActive ? "text-[#8C3A2A]" : "text-stone-400"}`}>
                {String(i + 1).padStart(2, "0")}
              </span>
              <span className={`text-[13px] ${isActive ? "text-stone-900" : "text-stone-600"}`}>
                {STAGE_META[s].name}
              </span>
              {done && <Check className="h-3.5 w-3.5 text-[#8C3A2A]" />}
              {flagged && <AlertCircle className="h-3.5 w-3.5 text-amber-600" data-testid={`ot-flag-${s}`} />}
            </button>
          );
        })}
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={active}
          initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
          transition={{ duration: 0.3 }}
          className="flex-1 flex flex-col"
        >
          <h1 className="font-serif-display text-3xl sm:text-4xl leading-snug text-stone-900" data-testid="ot-stage-name">
            {meta.name}
          </h1>
          <p className="text-stone-600 mt-4 text-[15px] leading-relaxed" data-testid="ot-stage-task">
            {meta.task}
          </p>

          {needsReview && (
            <div className="mt-4 flex items-start gap-2 bg-amber-50 border border-amber-200 rounded-sm p-3 text-[13px] text-amber-800" data-testid="ot-review-note">
              <AlertCircle className="h-4 w-4 mt-0.5 shrink-0" />
              An earlier change may affect this. Take a look and revise if you need to — your work here is still here.
            </div>
          )}

          {isMyIdeas ? (
            hasQuestions ? (
              <MyIdeasWorkflow sessionId={sessionId} ot={ot} setOt={setOt} />
            ) : null
          ) : (
            <>
          <textarea
            data-testid="ot-object-input"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            onBlur={saveDraft}
            rows={8}
            placeholder={meta.placeholder}
            className="mt-5 w-full bg-white border border-stone-300 rounded-sm p-5 text-[16px] leading-8 text-stone-900 placeholder:text-stone-400 outline-none focus:ring-1 focus:ring-stone-900 focus:border-stone-900 transition-colors resize-y min-h-[200px] font-serif-display"
          />

          {/* Coach response */}
          <AnimatePresence>
            {coach && !sending && (
              <motion.div
                initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
                transition={{ duration: 0.35 }}
                data-testid="ot-coach-bubble"
                className="mt-5 bg-white border-l-2 border-[#8C3A2A] border-y border-r border-stone-200 rounded-sm p-5"
              >
                <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.18em] text-[#8C3A2A] font-mono-panel mb-2">
                  <MessageSquareQuote className="h-3.5 w-3.5" />
                  Your coach
                </div>
                <p className="text-stone-800 leading-relaxed text-[16px] font-serif-display whitespace-pre-wrap" data-testid="ot-coach-message">
                  {coach.message}
                </p>
              </motion.div>
            )}
          </AnimatePresence>

          {sending && (
            <div className="mt-5 flex items-center gap-2 text-stone-500" data-testid="ot-thinking">
              <Loader2 className="h-4 w-4 animate-spin text-[#8C3A2A]" />
              <span className="text-sm italic font-serif-display">Reading what you wrote…</span>
            </div>
          )}
            </>
          )}

          {/* Actions */}
          <div className="mt-6 flex flex-wrap items-center gap-4">
            {idx > 0 && (
              <button
                onClick={() => goTo(STAGE_ORDER[idx - 1])}
                disabled={busy}
                data-testid="ot-back-button"
                className="inline-flex items-center gap-1.5 text-[12px] font-mono-panel uppercase tracking-[0.14em] text-stone-400 hover:text-stone-700 transition-colors disabled:opacity-40"
              >
                <ArrowLeft className="h-3.5 w-3.5" /> Back
              </button>
            )}
            <button
              onClick={share}
              disabled={!draft.trim() || busy}
              data-testid="ot-share-button"
              className={`inline-flex items-center gap-2 border border-stone-300 text-stone-800 px-5 py-2.5 rounded-sm font-medium hover:border-[#8C3A2A] hover:text-[#8C3A2A] transition-colors disabled:opacity-40 ${isMyIdeas ? "hidden" : ""}`}
            >
              {sending ? <Loader2 className="h-4 w-4 animate-spin" /> : <MessageSquareQuote className="h-4 w-4" />}
              Share with my coach
            </button>
            <button
              onClick={proceed}
              disabled={busy || !canProceed}
              data-testid="ot-continue-button"
              className="group inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-6 py-2.5 rounded-sm font-medium tracking-wide hover:bg-[#6B2C20] enabled:hover:-translate-y-px transition-[background-color,transform] disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {moving ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
              {isLast ? "Start writing" : "Continue"}
              {!moving && <ArrowRight className="h-4 w-4 transition-transform group-enabled:group-hover:translate-x-0.5" />}
            </button>
            {!canProceed && !sending && (
              <span className="text-[12px] text-stone-400" data-testid="ot-continue-hint">
                {isMyIdeas
                  ? "Work through your questions to build your ideas, then continue."
                  : "Share your work with your coach when you're ready to move on."}
              </span>
            )}
          </div>
        </motion.div>
      </AnimatePresence>
        </div>
        <OTThinkingPanel ot={ot} active={active} onRevisit={goTo} />
      </div>

      <div className="mt-8 flex items-center justify-center gap-2 text-stone-400 font-mono-panel text-[10px] uppercase tracking-[0.16em]">
        <Compass className="h-3.5 w-3.5" />
        Experience Compass
      </div>
    </motion.div>
  );
}
