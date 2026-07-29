import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Compass, ArrowLeft, Eye, Sparkles, Target, HelpCircle, TrendingUp, Layers, ArrowRight, Loader2 } from "lucide-react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Teacher Review — inspect how the frozen engine responds to representative
// students on one shared assignment. Uses PRECOMPUTED cases (no live latency).
// Modular: the "Compass Thinking" + "Developmental Response" blocks are isolated
// so the finalized Chapter 6 experience can replace them without touching this.
export default function TeacherReview() {
  const [data, setData] = useState(null);
  const [selected, setSelected] = useState(null);
  const [thinking, setThinking] = useState(false);

  useEffect(() => {
    fetch(`${API}/teacher-review/cases`).then((r) => r.json()).then(setData).catch(() => setData({ cases: [] }));
  }, []);

  const openCase = (c) => {
    setSelected(c);
    setThinking(true);
    setTimeout(() => setThinking(false), 1400); // brief thinking beat (pre-Ch6 stand-in)
  };

  return (
    <div className="min-h-screen paper-grain text-stone-900">
      <div className="max-w-5xl mx-auto px-6 md:px-10 pb-24">
        <header className="flex items-center justify-between pt-8">
          <a href="/" data-testid="review-home-link" className="flex items-center gap-2 text-stone-700 hover:text-[#8C3A2A] transition-colors">
            <Compass className="h-5 w-5 text-[#8C3A2A]" />
            <span className="font-serif-display text-lg">Compass</span>
          </a>
          <span className="font-mono-panel text-[11px] uppercase tracking-[0.2em] text-stone-500">Teacher Review</span>
        </header>

        <section className="pt-12 max-w-2xl">
          <p className="font-mono-panel text-[11px] uppercase tracking-[0.2em] text-stone-500 mb-4">The assignment</p>
          <h1 className="font-serif-display text-3xl md:text-4xl tracking-tight leading-snug text-stone-900">
            One assignment, six students
          </h1>
          <p className="text-stone-700 leading-relaxed mt-4">
            Every student below responded to the same prompt. Select one to see how Compass reads the
            writing, chooses a single instructional focus, and the reasoning behind that choice.
          </p>
          {data?.assignment && (
            <blockquote data-testid="review-assignment" className="mt-6 bg-white border-l-2 border-[#8C3A2A] border-y border-r border-stone-200 rounded-sm p-5 text-[15px] leading-relaxed text-stone-800 font-serif-display">
              {data.assignment}
            </blockquote>
          )}
        </section>

        {/* Student selector */}
        <section className="pt-10">
          <p className="font-mono-panel text-[11px] uppercase tracking-[0.2em] text-stone-500 mb-3">Choose a student</p>
          {!data ? (
            <div className="flex items-center gap-2 text-stone-500"><Loader2 className="h-4 w-4 animate-spin" /> Loading cases…</div>
          ) : (
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3" data-testid="review-student-grid">
              {data.cases.map((c) => (
                <button
                  key={c.id}
                  onClick={() => openCase(c)}
                  data-testid={`review-student-${c.id}`}
                  className={`text-left bg-white border rounded-md p-4 transition-[transform,border-color] duration-200 hover:-translate-y-0.5 hover:border-stone-400 focus:ring-2 focus:ring-[#8C3A2A] focus:outline-none ${selected?.id === c.id ? "border-[#8C3A2A]" : "border-stone-200"}`}
                >
                  <span className="font-serif-display text-lg text-stone-900">{c.label}</span>
                  <span className="block text-[13px] text-stone-500 mt-1 line-clamp-2">{c.response.slice(0, 70)}…</span>
                </button>
              ))}
            </div>
          )}
        </section>

        {/* Selected case */}
        <AnimatePresence mode="wait">
          {selected && (
            <motion.section
              key={selected.id}
              initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }}
              transition={{ duration: 0.4 }}
              className="pt-12 space-y-8"
              data-testid="review-case-detail"
            >
              {/* Student response */}
              <Block label={`${selected.label}'s response`} icon={Eye}>
                <p className="text-[16px] leading-8 text-stone-800 font-serif-display whitespace-pre-wrap">{selected.response}</p>
              </Block>

              {thinking ? (
                <div className="flex items-center gap-2 text-stone-500 py-6" data-testid="review-thinking">
                  <Loader2 className="h-4 w-4 animate-spin text-[#8C3A2A]" />
                  <span className="font-mono-panel text-[12px] uppercase tracking-[0.16em]">Compass is reading…</span>
                </div>
              ) : (
                <>
                  {/* Developmental Response (modular — Chapter 6 will replace this block) */}
                  <Block label="Compass's developmental response" icon={Sparkles} accent>
                    <p className="text-[16px] leading-8 text-stone-800 whitespace-pre-wrap">{selected.invitation}</p>
                  </Block>

                  {/* Teacher-facing explanation */}
                  <div data-testid="review-explanation" className="bg-white border border-stone-200 rounded-md p-6 md:p-8">
                    <p className="font-mono-panel text-[11px] uppercase tracking-[0.2em] text-stone-500 mb-6">The instructional reasoning</p>
                    <div className="space-y-6">
                      <Q icon={Eye} q="What did Compass understand the student to be trying to accomplish?">
                        <ul className="list-disc pl-5 space-y-1">{selected.explanation.understood.map((s, i) => <li key={i}>{s}</li>)}</ul>
                      </Q>
                      {selected.explanation.recognized.length > 0 && (
                        <Q icon={Sparkles} q="What strengths did Compass recognize?">
                          <ul className="list-disc pl-5 space-y-1">{selected.explanation.recognized.map((s, i) => <li key={i}>{s}</li>)}</ul>
                        </Q>
                      )}
                      <Q icon={Target} q="What developmental focus did Compass choose?">
                        <p><span className="font-medium text-stone-900">{selected.explanation.focus.element || selected.explanation.focus.target}</span>{selected.explanation.focus.purpose ? ` — ${selected.explanation.focus.purpose}` : ""}</p>
                        {selected.explanation.focus.target && selected.explanation.focus.target !== selected.explanation.focus.element && (
                          <p className="text-stone-600 mt-1">{selected.explanation.focus.target}</p>
                        )}
                      </Q>
                      {selected.explanation.why && (
                        <Q icon={HelpCircle} q="Why was that focus selected instead of another?">
                          <p>{selected.explanation.why}</p>
                          {selected.explanation.set_aside.length > 0 && (
                            <p className="text-stone-600 mt-2"><span className="font-mono-panel text-[11px] uppercase tracking-[0.14em] text-stone-400">Set aside for later: </span>{selected.explanation.set_aside.join("; ")}</p>
                          )}
                        </Q>
                      )}
                      {selected.explanation.architecture?.length > 0 && (
                        <Q icon={Layers} q="Where does this element fit within the architecture of the essay?">
                          <ul className="list-disc pl-5 space-y-1" data-testid="review-architecture">{selected.explanation.architecture.map((s, i) => <li key={i}>{s}</li>)}</ul>
                          {selected.explanation.exit_criterion && (
                            <p className="text-stone-600 mt-2"><span className="font-mono-panel text-[11px] uppercase tracking-[0.14em] text-stone-400">Ready to move on when: </span>{selected.explanation.exit_criterion}</p>
                          )}
                        </Q>
                      )}
                      {selected.explanation.next_step && (
                        <Q icon={ArrowRight} q="What should the writer learn next, once this element is strengthened?">
                          <p data-testid="review-next-step">{selected.explanation.next_step}</p>
                        </Q>
                      )}
                      {selected.explanation.broader && (
                        <Q icon={TrendingUp} q="What broader writing ability is this expected to develop?">
                          <p>{selected.explanation.broader}</p>
                        </Q>
                      )}
                    </div>
                  </div>
                </>
              )}
            </motion.section>
          )}
        </AnimatePresence>

        <div className="pt-16">
          <a href="/" data-testid="review-back-home" className="inline-flex items-center gap-2 text-stone-500 hover:text-[#8C3A2A] transition-colors font-mono-panel text-[12px] uppercase tracking-[0.16em]">
            <ArrowLeft className="h-4 w-4" /> Back to home
          </a>
        </div>
      </div>
    </div>
  );
}

function Block({ label, icon: Icon, accent, children }) {
  return (
    <div className={`bg-white border rounded-md p-6 md:p-8 ${accent ? "border-l-2 border-l-[#8C3A2A] border-y-stone-200 border-r-stone-200" : "border-stone-200"}`}>
      <div className="flex items-center gap-2 font-mono-panel text-[11px] uppercase tracking-[0.2em] text-stone-500 mb-4">
        <Icon className="h-4 w-4 text-[#8C3A2A]" />
        {label}
      </div>
      {children}
    </div>
  );
}

function Q({ icon: Icon, q, children }) {
  return (
    <div>
      <div className="flex items-start gap-2 mb-1.5">
        <Icon className="h-4 w-4 text-[#8C3A2A] mt-1 shrink-0" />
        <h3 className="font-serif-display text-lg text-stone-900 leading-snug">{q}</h3>
      </div>
      <div className="text-stone-700 leading-relaxed pl-6 text-[15px]">{children}</div>
    </div>
  );
}
