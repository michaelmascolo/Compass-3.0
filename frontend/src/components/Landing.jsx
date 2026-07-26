import { motion } from "framer-motion";
import { Compass, ArrowRight, Check, Clock, Sparkle } from "lucide-react";

// Teacher-facing homepage. Compass is ONE evolving instructional experience.
// Teachers first EXPERIENCE Compass as a student would; only afterward does
// Compass explain itself (the teacher reflection lives at the end of the
// experience, never before it). Editorial "paper" aesthetic; no marketing hype.
const STEPS = [
  ["Understanding", "Compass first reads the writing as a reader would, to grasp what the student is actually trying to say."],
  ["Recognition", "It names what the student has already done well — the productive move they have begun to make."],
  ["Developmental invitation", "It chooses one instructional focus and invites the student to take the next thinking step themselves."],
  ["Teaching", "It scaffolds that one move — never rewriting the work or supplying the ideas."],
];

// The developmental order in which Compass itself is introduced.
const STAGES = [
  { status: "current", label: "Current experience", title: "Composition" },
  { status: "next", label: "Coming next", title: "Organizing Ideas" },
  { status: "future", label: "Future", title: "Integrated Compass" },
];

export default function Landing() {
  return (
    <div className="min-h-screen paper-grain text-stone-900">
      <div className="max-w-7xl mx-auto px-8 md:px-16">
        {/* Header */}
        <header className="flex items-center gap-2 pt-10">
          <Compass className="h-5 w-5 text-[#8C3A2A]" />
          <span className="font-mono-panel text-xs uppercase tracking-[0.2em] text-stone-500">
            Compass · Common Ground Institute
          </span>
        </header>

        {/* Hero */}
        <section className="pt-20 md:pt-28 max-w-3xl">
          <motion.p
            initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
            className="font-mono-panel text-xs md:text-sm uppercase tracking-[0.2em] text-stone-500 mb-6"
          >
            An instructional system — not an essay generator
          </motion.p>
          <motion.h1
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.05 }}
            className="text-5xl md:text-6xl font-serif-display tracking-tight leading-[1.05] text-stone-900"
          >
            Experience Compass exactly as one of your students would.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.12 }}
            className="text-lg md:text-xl text-stone-700 leading-relaxed mt-8"
          >
            Compass reads a student's writing, decides what would most help them grow, and teaches
            them to develop it themselves. Step into the experience first. Afterward, Compass will
            explain exactly what it did — and why.
          </motion.p>
        </section>

        {/* Experience Compass — one evolving experience, introduced in order */}
        <section className="py-16 md:py-24">
          <motion.div
            initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55, delay: 0.05 }}
            className="bg-white border border-stone-200 rounded-md shadow-sm p-8 md:p-12"
            data-testid="experience-compass-panel"
          >
            <div className="flex items-center gap-2 font-mono-panel text-xs uppercase tracking-[0.2em] text-stone-500 mb-8">
              <Compass className="h-4 w-4 text-[#8C3A2A]" />
              Experience Compass
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8 md:gap-10">
              {STAGES.map((s) => (
                <Stage key={s.title} {...s} />
              ))}
            </div>

            <div className="mt-10 md:mt-12 pt-8 border-t border-stone-200 flex flex-col sm:flex-row sm:items-center gap-4">
              <a
                href="?preview"
                data-testid="btn-experience-compass"
                className="group inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-7 py-3.5 rounded-sm font-medium tracking-wide
                           hover:bg-[#6B2C20] hover:-translate-y-px transition-[background-color,transform] duration-200
                           focus:ring-2 focus:ring-[#8C3A2A] focus:ring-offset-2 focus:outline-none"
              >
                Experience Compass
                <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
              </a>
              <p className="text-[14px] text-stone-500">
                Begin the Composition experience. It takes a few minutes and asks nothing to set up.
              </p>
            </div>
          </motion.div>
        </section>

        {/* How Compass teaches */}
        <section className="pb-24 md:pb-32 border-t border-stone-200 pt-16 md:pt-20">
          <h2 className="text-3xl md:text-4xl font-serif-display tracking-tight text-stone-900 max-w-2xl">
            How a single Compass interaction unfolds
          </h2>
          <p className="text-lg text-stone-700 leading-relaxed mt-5 max-w-2xl">
            Compass supports the relationship between a teacher and a learner. It teaches, rather than
            edits — the student always remains the author of their work.
          </p>
          <ol className="mt-14 space-y-10 max-w-3xl">
            {STEPS.map(([title, body], i) => (
              <motion.li
                key={title}
                initial={{ opacity: 0, y: 10 }} whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }} transition={{ duration: 0.5, delay: i * 0.05 }}
                className="flex gap-6"
              >
                <span className="font-mono-panel text-sm text-[#8C3A2A] pt-1 w-8 shrink-0">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <h3 className="text-xl md:text-2xl font-serif-display text-stone-800">{title}</h3>
                  <p className="text-stone-700 leading-relaxed mt-1.5">{body}</p>
                </div>
              </motion.li>
            ))}
          </ol>
        </section>
      </div>

      {/* Footer */}
      <footer className="border-t border-stone-200">
        <div className="max-w-7xl mx-auto px-8 md:px-16 py-16 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div className="flex items-center gap-2 text-stone-600">
            <Compass className="h-4 w-4 text-[#8C3A2A]" />
            <span className="font-serif-display text-lg">Compass</span>
          </div>
          <p className="font-mono-panel text-xs uppercase tracking-[0.16em] text-stone-400">
            A nonprofit project of the Common Ground Institute
          </p>
        </div>
      </footer>
    </div>
  );
}

const STAGE_META = {
  current: { Icon: Check, tone: "text-[#8C3A2A]", ring: "border-[#8C3A2A]/40 bg-[#8C3A2A]/[0.03]" },
  next: { Icon: Clock, tone: "text-stone-500", ring: "border-stone-200" },
  future: { Icon: Sparkle, tone: "text-stone-400", ring: "border-stone-200" },
};

function Stage({ status, label, title }) {
  const { Icon, tone, ring } = STAGE_META[status];
  const dim = status !== "current";
  return (
    <div
      data-testid={`stage-${status}`}
      className={`rounded-md border p-5 ${ring}`}
    >
      <div className={`flex items-center gap-1.5 font-mono-panel text-[11px] uppercase tracking-[0.18em] ${tone}`}>
        <Icon className="h-3.5 w-3.5" />
        {label}
      </div>
      <p className={`font-serif-display text-2xl md:text-[26px] mt-3 ${dim ? "text-stone-500" : "text-stone-900"}`}>
        {title}
      </p>
    </div>
  );
}
