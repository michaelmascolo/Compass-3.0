import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight, ArrowLeft, Loader2, MessageSquareQuote, Check, Map, Search, PauseCircle, Sparkles,
} from "lucide-react";
import {
  otIdeasInit, otIdeasInteract, otIdeasSave, otIdeasAdvance, otIdeasMap, otIdeasConfirmMap,
  otIdeasInquiryPlan, otIdeasPause, otIdeasResume, otIdeasConstructGuidance, otIdeasConstruct,
} from "@/lib/api";

const SOURCE_OPTIONS = [
  "assigned reading", "class notes", "textbook", "teacher-provided source", "the teacher", "an approved website",
];
const STATUS_OPTIONS = [
  ["can_answer", "I can answer this now"],
  ["partial", "I have part of an answer"],
  ["need_info", "I still need information"],
];

function CoachNote({ coach }) {
  if (!coach || !coach.message) return null;
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
      transition={{ duration: 0.35 }}
      data-testid="mi-coach-bubble"
      className="mt-4 bg-white border-l-2 border-[#8C3A2A] border-y border-r border-stone-200 rounded-sm p-4"
    >
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.18em] text-[#8C3A2A] font-mono-panel mb-1.5">
        <MessageSquareQuote className="h-3.5 w-3.5" /> Your coach
        {coach.structure && coach.structure !== "Other" && (
          <span data-testid="mi-structure" className="text-stone-400 normal-case tracking-normal">· {coach.structure}</span>
        )}
      </div>
      <p className="text-stone-800 leading-relaxed text-[15px] font-serif-display whitespace-pre-wrap" data-testid="mi-coach-message">
        {coach.message}
      </p>
    </motion.div>
  );
}

export default function MyIdeasWorkflow({ sessionId, ot, setOt }) {
  const ideas = ot?.ideas || null;
  const questions = ideas?.questions || [];
  const researchList = ideas?.research_list || [];
  const phase = ideas?.phase || "pass1";

  const [idx, setIdx] = useState(0);
  const [answer, setAnswer] = useState("");
  const [coach, setCoach] = useState(null);
  const [busy, setBusy] = useState(false);
  const [statusMap, setStatusMap] = useState({});
  const [selfAssessment, setSelfAssessment] = useState("");
  const [challenges, setChallenges] = useState([]);
  const [sources, setSources] = useState([]);
  const [planNote, setPlanNote] = useState("");
  const [guidance, setGuidance] = useState(null);
  const [constructText, setConstructText] = useState("");
  const syncedIdx = useRef(false);

  // Ensure the ideas sub-state exists.
  useEffect(() => {
    if (ot && !ot.ideas && sessionId) {
      otIdeasInit(sessionId).then((res) => setOt(res.ot)).catch(() => {});
    }
  }, [ot, sessionId, setOt]);

  // Sync the active question index from persisted state once.
  useEffect(() => {
    if (ideas && !syncedIdx.current) {
      setIdx(Math.min(ideas.index || 0, Math.max(0, questions.length - 1)));
      syncedIdx.current = true;
    }
  }, [ideas, questions.length]);

  const inPass = phase === "pass1" || phase === "pass2";
  const passNo = phase === "pass2" ? 2 : 1;
  const resp = (ideas?.responses || {})[String(idx)] || {};

  // Load the current answer into the editor when the question or pass changes.
  useEffect(() => {
    if (!inPass) return;
    const r = (ideas?.responses || {})[String(idx)] || {};
    setAnswer((passNo === 2 ? r.pass2_text : r.pass1_text) || "");
    setCoach(null);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idx, phase]);

  // Seed the knowledge-map status choices from what Compass suggested.
  useEffect(() => {
    if (phase !== "knowledge_map") return;
    const m = {};
    Object.entries(ideas?.responses || {}).forEach(([k, r]) => {
      m[k] = r.confirmed_status || r.recommended_status || "partial";
    });
    setStatusMap(m);
    setSelfAssessment(ideas?.self_assessment || "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  // Seed inquiry-plan editing fields.
  useEffect(() => {
    if (phase !== "inquiry_plan" && phase !== "inquiry_paused") return;
    const plan = ideas?.inquiry_plan || {};
    setSources(plan.sources || []);
    setPlanNote(plan.text || "");
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  // Generate construction guidance when entering the construct phase.
  useEffect(() => {
    if (phase !== "construct" || guidance || busy) return;
    setConstructText(ideas?.my_ideas_construct || "");
    setBusy(true);
    otIdeasConstructGuidance(sessionId)
      .then((res) => { setOt(res.ot); setGuidance(res.guidance || {}); })
      .catch(() => setGuidance({ guidance: "Look across your answers. Which ideas keep coming up? Which one is most central?", prompts: [] }))
      .finally(() => setBusy(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [phase]);

  const dirty = inPass && answer.trim() !== ((passNo === 2 ? resp.pass2_text : resp.pass1_text) || "").trim();

  const share = useCallback(async () => {
    if (!answer.trim() || busy) return;
    setBusy(true);
    try {
      const res = await otIdeasInteract(sessionId, idx, answer, passNo);
      setOt(res.ot);
      setCoach({ decision: res.decision, structure: res.structure, message: res.message, sufficiency: res.sufficiency });
    } finally { setBusy(false); }
  }, [answer, busy, sessionId, idx, passNo, setOt]);

  const persistIfDirty = useCallback(async () => {
    if (dirty && answer.trim()) {
      const res = await otIdeasSave(sessionId, idx, answer, passNo);
      setOt(res.ot);
    }
  }, [dirty, answer, sessionId, idx, passNo, setOt]);

  const goToQuestion = useCallback(async (nextIdx) => {
    if (busy) return;
    setBusy(true);
    try {
      await persistIfDirty();
      const res = await otIdeasAdvance(sessionId, nextIdx);
      setOt(res.ot);
      setIdx(nextIdx);
      setCoach(null);
    } finally { setBusy(false); }
  }, [busy, persistIfDirty, sessionId, setOt]);

  const toMap = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    try {
      await persistIfDirty();
      const res = await otIdeasMap(sessionId);
      setOt(res.ot);
    } finally { setBusy(false); }
  }, [busy, persistIfDirty, sessionId, setOt]);

  const saveReview = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    try {
      const items = Object.entries(statusMap).map(([k, status]) => ({ index: Number(k), status }));
      const res = await otIdeasConfirmMap(sessionId, items, selfAssessment);
      setOt(res.ot);
      setChallenges(res.challenges || []);
    } finally { setBusy(false); }
  }, [busy, statusMap, selfAssessment, sessionId, setOt]);

  const makePlan = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    try {
      const items = Object.entries(statusMap).map(([k, status]) => ({ index: Number(k), status }));
      await otIdeasConfirmMap(sessionId, items, selfAssessment);
      const res = await otIdeasInquiryPlan(sessionId);
      setOt(res.ot);
    } finally { setBusy(false); }
  }, [busy, statusMap, selfAssessment, sessionId, setOt]);

  const goPause = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    try {
      const res = await otIdeasPause(sessionId, { sources, text: planNote });
      setOt(res.ot);
    } finally { setBusy(false); }
  }, [busy, sessionId, sources, planNote, setOt]);

  const resume = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    try {
      const res = await otIdeasResume(sessionId);
      setOt(res.ot);
      setIdx(0);
    } finally { setBusy(false); }
  }, [busy, sessionId, setOt]);

  const toConstruct = useCallback(async () => {
    if (busy) return;
    setBusy(true);
    try {
      await persistIfDirty();
      const res = await otIdeasConstructGuidance(sessionId);
      setOt(res.ot);
      setGuidance(res.guidance || {});
      setConstructText(res.ot?.ideas?.my_ideas_construct || "");
    } finally { setBusy(false); }
  }, [busy, persistIfDirty, sessionId, setOt]);

  const saveIdeas = useCallback(async () => {
    if (busy || constructText.trim().length < 10) return;
    setBusy(true);
    try {
      const res = await otIdeasConstruct(sessionId, constructText.trim());
      setOt(res.ot);
    } finally { setBusy(false); }
  }, [busy, constructText, sessionId, setOt]);

  if (!ideas) {
    return (
      <div className="flex items-center gap-2 text-stone-500 py-8" data-testid="mi-loading">
        <Loader2 className="h-4 w-4 animate-spin text-[#8C3A2A]" /> Getting your questions ready…
      </div>
    );
  }

  const answered = (r) => ((r.pass2_text || r.pass1_text || "").trim());
  const allPass2Answered = questions.every((_, i) => {
    const persisted = (ideas.responses[String(i)]?.pass2_text || "").trim();
    // The current question's freshly typed answer counts too — toConstruct
    // persists it before advancing, so we should not gate on stale state.
    if (inPass && passNo === 2 && i === idx) return persisted || answer.trim();
    return persisted;
  });

  return (
    <div data-testid="my-ideas-workflow" className="mt-5">
      <p className="font-mono-panel text-[10px] uppercase tracking-[0.16em] text-stone-400 mb-4" data-testid="mi-phase">
        {phase === "pass1" && "First pass · your best current answers"}
        {phase === "knowledge_map" && "My understanding so far"}
        {phase === "inquiry_plan" && "Your plan for what to find out"}
        {phase === "inquiry_paused" && "Go gather what you need"}
        {phase === "pass2" && "Second pass · improve your answers"}
        {phase === "construct" && "Bring your ideas together"}
        {phase === "done" && "Your ideas are ready"}
      </p>

      {/* ---- PASS 1 / PASS 2: one question at a time ---- */}
      {inPass && (
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="font-mono-panel text-[10px] uppercase tracking-[0.14em] text-stone-400" data-testid="mi-question-index">
              Question {idx + 1} of {questions.length}
            </span>
          </div>
          <p className="font-serif-display text-xl leading-snug text-stone-900" data-testid="mi-question">
            {questions[idx]}
          </p>

          {passNo === 2 && (resp.pass1_text || "").trim() && (
            <div className="mt-3 bg-[#faf9f6] border border-stone-200 rounded-sm p-3" data-testid="mi-original-answer">
              <span className="font-mono-panel text-[9px] uppercase tracking-[0.14em] text-stone-400">Your earlier answer</span>
              <p className="mt-1 text-[14px] text-stone-600 whitespace-pre-wrap font-serif-display">{resp.pass1_text}</p>
              {(resp.research_need || "").trim() && (
                <div data-testid="mi-pass2-research-need" className="mt-2 pt-2 border-t border-stone-200">
                  <span className="font-mono-panel text-[9px] uppercase tracking-[0.14em] text-[#8C3A2A]">What you set out to learn</span>
                  <p className="mt-0.5 text-[13px] text-stone-700 font-serif-display">{resp.research_need}</p>
                </div>
              )}
              <p className="mt-2 text-[12px] text-stone-500">What did you find or now understand? Update your answer with your new knowledge — you're strengthening it, not starting over.</p>
            </div>
          )}

          <textarea
            data-testid="mi-answer-input"
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            rows={5}
            placeholder={passNo === 2 ? "Revise your answer in your own words…" : "Your best current answer — a genuine attempt is enough to move on."}
            className="mt-4 w-full bg-white border border-stone-300 rounded-sm p-4 text-[16px] leading-8 text-stone-900 placeholder:text-stone-400 outline-none focus:ring-1 focus:ring-stone-900 focus:border-stone-900 transition-colors resize-y min-h-[140px] font-serif-display"
          />

          <AnimatePresence>{coach && !busy && <CoachNote coach={coach} />}</AnimatePresence>
          {busy && (
            <div className="mt-4 flex items-center gap-2 text-stone-500" data-testid="mi-thinking">
              <Loader2 className="h-4 w-4 animate-spin text-[#8C3A2A]" />
              <span className="text-sm italic font-serif-display">Reading what you wrote…</span>
            </div>
          )}

          <div className="mt-5 flex flex-wrap items-center gap-4">
            {idx > 0 && (
              <button onClick={() => goToQuestion(idx - 1)} disabled={busy} data-testid="mi-prev-button"
                className="inline-flex items-center gap-1.5 text-[12px] font-mono-panel uppercase tracking-[0.14em] text-stone-400 hover:text-stone-700 transition-colors disabled:opacity-40">
                <ArrowLeft className="h-3.5 w-3.5" /> Previous
              </button>
            )}
            <button onClick={share} disabled={!answer.trim() || busy} data-testid="mi-share-button"
              className="inline-flex items-center gap-2 border border-stone-300 text-stone-800 px-4 py-2 rounded-sm font-medium hover:border-[#8C3A2A] hover:text-[#8C3A2A] transition-colors disabled:opacity-40">
              <MessageSquareQuote className="h-4 w-4" /> Share with my coach
            </button>
            {idx < questions.length - 1 ? (
              <button onClick={() => goToQuestion(idx + 1)} disabled={busy || !answer.trim()} data-testid="mi-next-button"
                className="group inline-flex items-center gap-2 bg-stone-800 text-white px-5 py-2 rounded-sm font-medium hover:bg-stone-700 transition-colors disabled:opacity-40">
                Next question <ArrowRight className="h-4 w-4" />
              </button>
            ) : passNo === 1 ? (
              <button onClick={toMap} disabled={busy || !answer.trim()} data-testid="mi-to-map-button"
                className="group inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-5 py-2 rounded-sm font-medium hover:bg-[#6B2C20] transition-colors disabled:opacity-40">
                <Map className="h-4 w-4" /> See my understanding so far
              </button>
            ) : (
              <button onClick={toConstruct} disabled={busy || !allPass2Answered} data-testid="mi-build-button"
                className="group inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-5 py-2 rounded-sm font-medium hover:bg-[#6B2C20] transition-colors disabled:opacity-40">
                <Sparkles className="h-4 w-4" /> Build my ideas
              </button>
            )}
          </div>
          {passNo === 1 && resp.pass1_state === "knowledge_limit" && (
            <div data-testid="mi-knowledge-limit" className="mt-3 flex items-start gap-2 text-[13px] text-[#8C3A2A] bg-[#8C3A2A]/[0.05] border border-[#8C3A2A]/20 rounded-sm p-2.5">
              <Search className="h-4 w-4 mt-0.5 shrink-0" />
              <span>You've developed this as far as your current understanding allows — I've added what's left to find out to your research list below.</span>
            </div>
          )}
          {passNo === 1 && (
            <p className="mt-2 text-[12px] text-stone-400">A weak or unfinished answer is fine here — a genuine attempt is enough to move on.</p>
          )}
          {passNo === 1 && (researchList.length > 0) && (
            <div data-testid="mi-research-list" className="mt-5 bg-[#faf9f6] border border-stone-200 rounded-sm p-4">
              <div className="flex items-center gap-1.5 font-mono-panel text-[10px] uppercase tracking-[0.16em] text-stone-500 mb-2">
                <Search className="h-3.5 w-3.5 text-[#8C3A2A]" /> Things to find out
              </div>
              <p className="text-[12px] text-stone-400 mb-2">Your research agenda — what to look up later. You'll come back and strengthen these answers once you've gathered them.</p>
              <ul className="space-y-1.5">
                {researchList.map((it, i) => (
                  <li key={i} data-testid={`mi-research-item-${it.index}`} className="text-[13px] text-stone-700 font-serif-display">
                    <span className="text-stone-400">Q{it.index + 1}:</span> {it.need}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* ---- KNOWLEDGE MAP: My Understanding So Far ---- */}
      {phase === "knowledge_map" && (
        <div data-testid="mi-knowledge-map">
          <p className="text-stone-600 text-[14px] leading-relaxed mb-4">
            Here is what your answers suggest so far. Look at the whole pattern, then mark where each one stands. You decide — change any of these.
          </p>
          <div className="space-y-3">
            {questions.map((q, i) => {
              const r = ideas.responses[String(i)] || {};
              return (
                <div key={i} data-testid={`mi-map-row-${i}`} className="bg-white border border-stone-200 rounded-sm p-4">
                  <p className="font-serif-display text-[15px] text-stone-900">{q}</p>
                  {answered(r) && (
                    <p className="mt-1 text-[13px] text-stone-500 whitespace-pre-wrap font-serif-display line-clamp-3">{r.pass1_text}</p>
                  )}
                  <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-[12px] text-stone-500">
                    {r.structure && r.structure !== "Other" && <span>Kind of thinking: <span className="text-stone-700">{r.structure}</span></span>}
                    {r.present && <span data-testid={`mi-map-present-${i}`}>Present: <span className="text-stone-700">{r.present}</span></span>}
                    {r.gap && <span data-testid={`mi-map-gap-${i}`}>May be missing: <span className="text-stone-700">{r.gap}</span></span>}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-2">
                    {STATUS_OPTIONS.map(([val, label]) => {
                      const on = statusMap[String(i)] === val;
                      return (
                        <button key={val} onClick={() => setStatusMap((m) => ({ ...m, [String(i)]: val }))}
                          data-testid={`mi-map-status-${i}-${val}`}
                          className={`text-[12px] px-3 py-1.5 rounded-sm border transition-colors ${on ? "border-[#8C3A2A] bg-[#8C3A2A]/[0.05] text-[#8C3A2A]" : "border-stone-200 text-stone-600 hover:border-stone-400"}`}>
                          {label}
                        </button>
                      );
                    })}
                  </div>
                  {challenges.filter((c) => c.index === i).map((c, ci) => (
                    <p key={ci} data-testid={`mi-challenge-${i}`} className="mt-2 text-[13px] text-amber-800 bg-amber-50 border border-amber-200 rounded-sm p-2.5">
                      {c.challenge}
                    </p>
                  ))}
                </div>
              );
            })}
          </div>

          <div className="mt-5">
            <label className="block font-mono-panel text-[10px] uppercase tracking-[0.14em] text-stone-500 mb-1.5">
              How does your understanding feel overall?
            </label>
            <p className="text-[12px] text-stone-400 mb-2">Which answers feel ready? Which have a piece but feel incomplete? Where are you relying on a guess?</p>
            <textarea data-testid="mi-self-assessment" value={selfAssessment} onChange={(e) => setSelfAssessment(e.target.value)} rows={3}
              placeholder="Think aloud about the overall state of your understanding…"
              className="w-full bg-white border border-stone-300 rounded-sm p-3 text-[14px] leading-relaxed text-stone-900 placeholder:text-stone-400 outline-none focus:ring-1 focus:ring-stone-900 resize-y font-serif-display" />
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-4">
            <button onClick={saveReview} disabled={busy} data-testid="mi-confirm-map-button"
              className="inline-flex items-center gap-2 border border-stone-300 text-stone-800 px-4 py-2 rounded-sm font-medium hover:border-[#8C3A2A] hover:text-[#8C3A2A] transition-colors disabled:opacity-40">
              {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />} Save my review
            </button>
            <button onClick={makePlan} disabled={busy} data-testid="mi-make-plan-button"
              className="group inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-5 py-2 rounded-sm font-medium hover:bg-[#6B2C20] transition-colors disabled:opacity-40">
              <Search className="h-4 w-4" /> Make my inquiry plan
            </button>
          </div>
        </div>
      )}

      {/* ---- INQUIRY PLAN ---- */}
      {phase === "inquiry_plan" && (
        <PlanView plan={ideas.inquiry_plan || {}} sources={sources} setSources={setSources} planNote={planNote} setPlanNote={setPlanNote} busy={busy}
          onGather={goPause} onReady={resume} />
      )}

      {/* ---- INQUIRY PAUSE ---- */}
      {phase === "inquiry_paused" && (
        <div data-testid="mi-paused" className="bg-white border border-stone-200 rounded-sm p-5">
          <div className="flex items-center gap-2 text-[#8C3A2A] font-mono-panel text-[10px] uppercase tracking-[0.16em] mb-3">
            <PauseCircle className="h-4 w-4" /> Paused for inquiry
          </div>
          <p className="text-stone-700 text-[15px] leading-relaxed font-serif-display">Go find what you need, then come back to improve your answers. Your work is saved.</p>
          {(ideas.inquiry_plan?.needs || []).length > 0 && (
            <div className="mt-4">
              <span className="font-mono-panel text-[9px] uppercase tracking-[0.14em] text-stone-400">What you're looking for</span>
              <ul className="mt-1 space-y-1">
                {ideas.inquiry_plan.needs.map((n, i) => <li key={i} className="text-[14px] text-stone-700 font-serif-display">• {n}</li>)}
              </ul>
            </div>
          )}
          {(ideas.inquiry_plan?.sources || []).length > 0 && (
            <p className="mt-3 text-[13px] text-stone-500">Where to look: {ideas.inquiry_plan.sources.join(", ")}</p>
          )}
          <button onClick={resume} disabled={busy} data-testid="mi-resume-button"
            className="mt-5 group inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-5 py-2.5 rounded-sm font-medium hover:bg-[#6B2C20] transition-colors disabled:opacity-40">
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <ArrowRight className="h-4 w-4" />} I'm back — refine my answers
          </button>
        </div>
      )}

      {/* ---- CONSTRUCT MY IDEAS ---- */}
      {phase === "construct" && (
        <div data-testid="mi-construct">
          {guidance && (
            <div className="bg-[#faf9f6] border border-stone-200 rounded-sm p-4" data-testid="mi-construct-guidance">
              <p className="text-stone-700 text-[14px] leading-relaxed font-serif-display">{guidance.guidance}</p>
              {(guidance.prompts || []).length > 0 && (
                <ul className="mt-2 space-y-1">
                  {guidance.prompts.map((p, i) => <li key={i} className="text-[13px] text-stone-600 font-serif-display">• {p}</li>)}
                </ul>
              )}
            </div>
          )}
          <div className="mt-4 space-y-2">
            <span className="font-mono-panel text-[9px] uppercase tracking-[0.14em] text-stone-400">Your revised answers</span>
            {questions.map((q, i) => {
              const r = ideas.responses[String(i)] || {};
              const a = (r.pass2_text || r.pass1_text || "").trim();
              if (!a) return null;
              return (
                <div key={i} className="text-[13px] text-stone-600">
                  <span className="text-stone-800 font-serif-display">{q}</span>
                  <p className="whitespace-pre-wrap font-serif-display">{a}</p>
                </div>
              );
            })}
          </div>
          <label className="mt-5 block font-mono-panel text-[10px] uppercase tracking-[0.14em] text-stone-500 mb-1.5">
            The ideas I now have
          </label>
          <textarea data-testid="mi-construct-input" value={constructText} onChange={(e) => setConstructText(e.target.value)} rows={6}
            placeholder="In your own words, what are the important ideas you now have? Which is most central, and how do the others support it?"
            className="w-full bg-white border border-stone-300 rounded-sm p-4 text-[16px] leading-8 text-stone-900 placeholder:text-stone-400 outline-none focus:ring-1 focus:ring-stone-900 focus:border-stone-900 resize-y min-h-[150px] font-serif-display" />
          <button onClick={saveIdeas} disabled={busy || constructText.trim().length < 10} data-testid="mi-construct-save"
            className="mt-4 group inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-5 py-2.5 rounded-sm font-medium hover:bg-[#6B2C20] transition-colors disabled:opacity-40">
            {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />} Save my ideas
          </button>
        </div>
      )}

      {/* ---- DONE ---- */}
      {phase === "done" && (
        <div data-testid="mi-done" className="bg-white border border-stone-200 rounded-sm p-5">
          <div className="flex items-center gap-2 text-[#8C3A2A] font-mono-panel text-[10px] uppercase tracking-[0.16em] mb-2">
            <Check className="h-4 w-4" /> Your ideas
          </div>
          <p className="text-stone-800 text-[15px] leading-relaxed whitespace-pre-wrap font-serif-display">
            {ideas.my_ideas_construct || ot.objects?.my_ideas}
          </p>
          <p className="mt-3 text-[12px] text-stone-400">Continue when you're ready to shape these into your current answer.</p>
        </div>
      )}
    </div>
  );
}

function PlanView({ plan, sources, setSources, planNote, setPlanNote, busy, onGather, onReady }) {
  const toggle = (s) => setSources((cur) => (cur.includes(s) ? cur.filter((x) => x !== s) : [...cur, s]));
  const noNeeds = (plan.needs || []).length === 0;
  return (
    <div data-testid="mi-inquiry-plan">
      <p className="text-stone-600 text-[14px] leading-relaxed mb-4">
        Here is one plan for what to find out — a manageable set, not a long list of errands.
      </p>
      {(plan.understood || []).length > 0 && (
        <div className="mb-4">
          <span className="font-mono-panel text-[9px] uppercase tracking-[0.14em] text-stone-400">What you already understand</span>
          <ul className="mt-1 space-y-1">
            {plan.understood.map((u, i) => <li key={i} className="text-[14px] text-stone-700 font-serif-display" data-testid={`mi-plan-understood-${i}`}>• {u}</li>)}
          </ul>
        </div>
      )}
      <div className="mb-4">
        <span className="font-mono-panel text-[9px] uppercase tracking-[0.14em] text-stone-400">What you still need to find out</span>
        {noNeeds ? (
          <p className="mt-1 text-[14px] text-stone-500 font-serif-display">You marked everything as ready — you can go straight to refining your answers.</p>
        ) : (
          <ul className="mt-1 space-y-1">
            {plan.needs.map((n, i) => <li key={i} className="text-[14px] text-stone-700 font-serif-display" data-testid={`mi-plan-need-${i}`}>• {n}</li>)}
          </ul>
        )}
      </div>
      <div className="mb-4">
        <span className="font-mono-panel text-[9px] uppercase tracking-[0.14em] text-stone-400">Where you could look</span>
        <div className="mt-2 flex flex-wrap gap-2">
          {SOURCE_OPTIONS.map((s) => {
            const on = sources.includes(s);
            return (
              <button key={s} onClick={() => toggle(s)} data-testid={`mi-plan-source-${s.replace(/\s+/g, "-")}`}
                className={`text-[12px] px-3 py-1.5 rounded-sm border transition-colors ${on ? "border-[#8C3A2A] bg-[#8C3A2A]/[0.05] text-[#8C3A2A]" : "border-stone-200 text-stone-600 hover:border-stone-400"}`}>
                {s}
              </button>
            );
          })}
        </div>
      </div>
      <textarea data-testid="mi-plan-text" value={planNote} onChange={(e) => setPlanNote(e.target.value)} rows={2}
        placeholder="Anything specific you'll look for (optional)…"
        className="w-full bg-white border border-stone-300 rounded-sm p-3 text-[14px] leading-relaxed text-stone-900 placeholder:text-stone-400 outline-none focus:ring-1 focus:ring-stone-900 resize-y font-serif-display" />
      <div className="mt-5 flex flex-wrap items-center gap-4">
        <button onClick={onGather} disabled={busy} data-testid="mi-pause-button"
          className="group inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-5 py-2.5 rounded-sm font-medium hover:bg-[#6B2C20] transition-colors disabled:opacity-40">
          {busy ? <Loader2 className="h-4 w-4 animate-spin" /> : <Search className="h-4 w-4" />} I'll go find this
        </button>
        <button onClick={onReady} disabled={busy} data-testid="mi-ready-button"
          className="inline-flex items-center gap-1.5 text-[12px] font-mono-panel uppercase tracking-[0.14em] text-stone-500 hover:text-[#8C3A2A] transition-colors disabled:opacity-40">
          I already have what I need — refine my answers <ArrowRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}
