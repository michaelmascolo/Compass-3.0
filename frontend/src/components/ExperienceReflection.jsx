import { motion } from "framer-motion";
import { Compass, Target, PencilLine, Users, ArrowUpRight, RotateCcw, Eye } from "lucide-react";

// Experience Compass — the deliberate stop at the end of ONE developmental cycle.
// Four fixed sections, driven entirely by session.experience_control.reflection.
// The learner's passage stays visible (read-only). No revision controls, no
// PreviewBridge. The only action is starting a completely fresh passage.
const SECTIONS = [
  { key: "objective", label: "The one thing you worked on", Icon: Target },
  { key: "how_your_writing_changed", label: "How your writing changed", Icon: PencilLine },
  { key: "why_it_helps_your_reader", label: "Why it helps your reader", Icon: Users },
  { key: "carry_it_forward", label: "Carry it forward", Icon: ArrowUpRight },
];

export default function ExperienceReflection({ reflection, draft, onRestart, onReviewAsTeacher }) {
  const r = reflection || {};
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className="flex-1 flex flex-col py-4"
      data-testid="experience-reflection"
    >
      <p className="font-mono-panel text-[10px] uppercase tracking-[0.18em] text-stone-400 mb-3">
        Reflection
      </p>
      <h2 className="font-serif-display text-2xl sm:text-3xl leading-snug text-stone-900">
        You developed one idea in your writing.
      </h2>

      {/* The learner's passage stays visible — read-only. */}
      {draft && draft.trim() && (
        <div
          data-testid="reflection-passage"
          className="mt-5 bg-white border border-stone-300 rounded-sm px-7 sm:px-10 py-6 text-[16px] leading-8 text-stone-800 whitespace-pre-wrap font-serif-display"
        >
          {draft.trim()}
        </div>
      )}

      {/* Four fixed reflection sections. */}
      <div className="mt-6 space-y-4">
        {SECTIONS.map(({ key, label, Icon }, i) => (
          <motion.div
            key={key}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.35, delay: 0.08 * i }}
            data-testid={`reflection-section-${key}`}
            className="bg-white border-l-2 border-[#8C3A2A] border-y border-r border-stone-200 rounded-sm p-5"
          >
            <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.18em] text-[#8C3A2A] font-mono-panel mb-2">
              <Icon className="h-3.5 w-3.5" />
              {label}
            </div>
            <p
              data-testid={`reflection-value-${key}`}
              className="text-stone-800 leading-relaxed text-[16px] font-serif-display whitespace-pre-wrap"
            >
              {r[key] || "—"}
            </p>
          </motion.div>
        ))}
      </div>

      {/* The only action: start a completely fresh passage. */}
      <div className="mt-8 flex items-center justify-center">
        <button
          onClick={onRestart}
          data-testid="reflection-try-another"
          className="group inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-7 py-3 rounded-sm font-medium tracking-wide hover:bg-[#6B2C20] hover:-translate-y-px transition-[background-color,transform]"
        >
          <RotateCcw className="h-4 w-4 transition-transform group-hover:-rotate-45" />
          Try another paragraph
        </button>
      </div>

      {/* Experience first, explanation second: offer to review as a teacher. */}
      {onReviewAsTeacher && (
        <div
          className="mt-8 border-t border-stone-200 pt-7 flex flex-col items-center text-center"
          data-testid="reflection-review-offer"
        >
          <p className="font-serif-display text-lg text-stone-800">
            Would you like to review this experience as a teacher?
          </p>
          <p className="text-[14px] text-stone-500 mt-1.5 max-w-md">
            See what Compass understood, the one instructional focus it chose, and why.
          </p>
          <button
            onClick={onReviewAsTeacher}
            data-testid="reflection-review-as-teacher"
            className="group mt-4 inline-flex items-center gap-2 border border-stone-300 text-stone-800 px-6 py-2.5 rounded-sm font-medium tracking-wide hover:border-[#8C3A2A] hover:text-[#8C3A2A] transition-colors"
          >
            <Eye className="h-4 w-4" />
            Review this experience as a teacher
          </button>
        </div>
      )}

      <div className="mt-6 flex items-center justify-center gap-2 text-stone-400 font-mono-panel text-[10px] uppercase tracking-[0.16em]">
        <Compass className="h-3.5 w-3.5" />
        Experience Compass
      </div>
    </motion.div>
  );
}
