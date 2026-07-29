import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  Compass,
  ArrowLeft,
  Eye,
  Sparkles,
  Target,
  HelpCircle,
  TrendingUp,
  Layers,
  ArrowRight,
  Loader2,
  ArrowUpRight,
} from "lucide-react";
import { getTeacherReflection } from "@/lib/api";

// Post-experience teacher reflection. Explains Compass's instructional reasoning
// on the teacher's OWN Composition experience (the one they just completed) —
// not the sample students. Experience first; explanation second.
export default function TeacherReflection({ sessionId, onBack }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (!sessionId) return;
    getTeacherReflection(sessionId)
      .then(setData)
      .catch(() => setError(true));
  }, [sessionId]);

  const focus = data?.explanation?.focus || {};
  const focusLabel = focus.element || focus.target || "";

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="flex-1 flex flex-col py-4"
      data-testid="teacher-reflection"
    >
      <button
        onClick={onBack}
        data-testid="teacher-reflection-back"
        className="self-start inline-flex items-center gap-2 text-stone-500 hover:text-[#8C3A2A] transition-colors font-mono-panel text-[11px] uppercase tracking-[0.16em] mb-6"
      >
        <ArrowLeft className="h-4 w-4" /> Back to your experience
      </button>

      <p className="font-mono-panel text-[10px] uppercase tracking-[0.18em] text-stone-400 mb-3">
        Reviewing as a teacher
      </p>
      <h2 className="font-serif-display text-2xl sm:text-3xl leading-snug text-stone-900">
        What Compass just did — and why
      </h2>
      <p className="text-stone-600 mt-3 text-[15px] leading-relaxed max-w-xl">
        You just experienced Compass as one of your students would. Here is the instructional
        reasoning behind the response you received.
      </p>

      {error ? (
        <p className="mt-10 text-stone-500" data-testid="teacher-reflection-error">
          This reflection isn't available for this session.
        </p>
      ) : !data ? (
        <div className="mt-10 flex items-center gap-2 text-stone-500" data-testid="teacher-reflection-loading">
          <Loader2 className="h-4 w-4 animate-spin text-[#8C3A2A]" />
          <span className="font-mono-panel text-[12px] uppercase tracking-[0.16em]">
            Gathering the reasoning…
          </span>
        </div>
      ) : (
        <div className="mt-8 space-y-8" data-testid="teacher-reflection-detail">
          {/* Your response */}
          {data.response && (
            <Block label="Your response" icon={Eye}>
              <p className="text-[16px] leading-8 text-stone-800 font-serif-display whitespace-pre-wrap">
                {data.response}
              </p>
            </Block>
          )}

          {/* Compass's developmental response */}
          {data.invitation && (
            <Block label="What Compass said to you" icon={Sparkles} accent>
              <p className="text-[16px] leading-8 text-stone-800 whitespace-pre-wrap">
                {data.invitation}
              </p>
            </Block>
          )}

          {/* The instructional reasoning */}
          <div
            data-testid="teacher-reflection-reasoning"
            className="bg-white border border-stone-200 rounded-md p-6 md:p-8"
          >
            <p className="font-mono-panel text-[11px] uppercase tracking-[0.2em] text-stone-500 mb-6">
              The instructional reasoning
            </p>
            <div className="space-y-6">
              {data.explanation?.understood?.length > 0 && (
                <Q icon={Eye} q="What did Compass understand you to be trying to accomplish?">
                  <ul className="list-disc pl-5 space-y-1">
                    {data.explanation.understood.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </Q>
              )}
              {data.explanation?.recognized?.length > 0 && (
                <Q icon={Sparkles} q="What did Compass recognize you had already done well?">
                  <ul className="list-disc pl-5 space-y-1">
                    {data.explanation.recognized.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                </Q>
              )}
              {focusLabel && (
                <Q icon={Target} q="What developmental focus did Compass choose?">
                  <p>
                    <span className="font-medium text-stone-900">{focusLabel}</span>
                    {focus.purpose ? ` — ${focus.purpose}` : ""}
                  </p>
                  {focus.target && focus.target !== focus.element && (
                    <p className="text-stone-600 mt-1">{focus.target}</p>
                  )}
                </Q>
              )}
              {data.explanation?.why && (
                <Q icon={HelpCircle} q="Why that focus instead of another?">
                  <p>{data.explanation.why}</p>
                  {data.explanation.set_aside?.length > 0 && (
                    <p className="text-stone-600 mt-2">
                      <span className="font-mono-panel text-[11px] uppercase tracking-[0.14em] text-stone-400">
                        Set aside for later:{" "}
                      </span>
                      {data.explanation.set_aside.join("; ")}
                    </p>
                  )}
                </Q>
              )}
              {data.explanation?.architecture?.length > 0 && (
                <Q icon={Layers} q="Where does this element fit within the architecture of the essay?">
                  <ul className="list-disc pl-5 space-y-1" data-testid="reflection-architecture">
                    {data.explanation.architecture.map((s, i) => (
                      <li key={i}>{s}</li>
                    ))}
                  </ul>
                  {data.explanation.exit_criterion && (
                    <p className="text-stone-600 mt-2">
                      <span className="font-mono-panel text-[11px] uppercase tracking-[0.14em] text-stone-400">
                        Ready to move on when:{" "}
                      </span>
                      {data.explanation.exit_criterion}
                    </p>
                  )}
                </Q>
              )}
              {data.explanation?.next_step && (
                <Q icon={ArrowRight} q="What should the writer learn next, once this element is strengthened?">
                  <p data-testid="reflection-next-step">{data.explanation.next_step}</p>
                </Q>
              )}
              {data.explanation?.broader && (
                <Q icon={TrendingUp} q="What broader writing ability was Compass developing?">
                  <p>{data.explanation.broader}</p>
                </Q>
              )}
            </div>
          </div>

          {/* Optional exploration — offered only AFTER the teacher's own experience. */}
          <div className="border-t border-stone-200 pt-8">
            <a
              href="?review"
              data-testid="teacher-reflection-explore-samples"
              className="group inline-flex items-center gap-2 text-[#8C3A2A] font-medium"
            >
              Explore how Compass responds to other kinds of student writing
              <ArrowUpRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-0.5 group-hover:-translate-y-0.5" />
            </a>
            <p className="text-[13px] text-stone-500 mt-1.5">
              An optional way to see Compass read a range of student responses to one assignment.
            </p>
          </div>
        </div>
      )}

      <div className="mt-8 flex items-center justify-center gap-2 text-stone-400 font-mono-panel text-[10px] uppercase tracking-[0.16em]">
        <Compass className="h-3.5 w-3.5" />
        Experience Compass
      </div>
    </motion.div>
  );
}

function Block({ label, icon: Icon, accent, children }) {
  return (
    <div
      className={`bg-white border rounded-md p-6 md:p-8 ${
        accent
          ? "border-l-2 border-l-[#8C3A2A] border-y-stone-200 border-r-stone-200"
          : "border-stone-200"
      }`}
    >
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
