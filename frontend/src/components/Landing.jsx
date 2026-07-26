import { motion } from "framer-motion";
import { Compass, ArrowRight, Eye, PenLine } from "lucide-react";

// Teacher-facing homepage. Two equally-prominent first-class entry points:
// Teacher Review (?review) and Student Experience (?preview). Editorial "paper"
// aesthetic; no pricing, testimonials, marketing hype, or account gates.
const STEPS = [
  ["Understanding", "Compass first reads the writing as a reader would, to grasp what the student is actually trying to say."],
  ["Recognition", "It names what the student has already done well — the productive move they have begun to make."],
  ["Developmental invitation", "It chooses one instructional focus and invites the student to take the next thinking step themselves."],
  ["Teaching", "It scaffolds that one move — never rewriting the work or supplying the ideas."],
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
            AI that teaches students to think—not AI that thinks for them.
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, delay: 0.12 }}
            className="text-lg md:text-xl text-stone-700 leading-relaxed mt-8"
          >
            Compass reads a student's writing, decides what would most help them grow, and teaches
            them to develop it themselves. See the instructional reasoning for yourself, or step into
            the experience as one of your students would.
          </motion.p>
        </section>

        {/* Two equally-prominent entry points */}
        <section className="py-20 md:py-28 grid grid-cols-1 md:grid-cols-2 gap-8 md:gap-12">
          <EntryCard
            testid="btn-teacher-review"
            href="?review"
            icon={Eye}
            label="For educators"
            title="Teacher Review"
            description="See exactly how Compass analyzes student writing, selects an instructional focus, and scaffolds revision."
            cta="Open Teacher Review"
            delay={0.04}
          />
          <EntryCard
            testid="btn-student-experience"
            href="?preview"
            icon={PenLine}
            label="Experience it"
            title="Student Experience"
            description="Experience Compass from the student's point of view."
            cta="Launch Student Experience"
            delay={0.1}
          />
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

function EntryCard({ testid, href, icon: Icon, label, title, description, cta, delay }) {
  return (
    <motion.a
      href={href}
      data-testid={testid}
      initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55, delay }}
      className="group block bg-white border border-stone-200 rounded-md shadow-sm p-8 md:p-10
                 hover:border-stone-400 hover:-translate-y-1 transition-[transform,border-color] duration-200
                 focus:ring-2 focus:ring-[#8C3A2A] focus:outline-none"
    >
      <div className="flex items-center gap-2 font-mono-panel text-xs uppercase tracking-[0.2em] text-stone-500 mb-6">
        <Icon className="h-4 w-4 text-[#8C3A2A]" />
        {label}
      </div>
      <h3 className="text-3xl md:text-4xl font-serif-display tracking-tight text-stone-900">{title}</h3>
      <p className="text-stone-700 leading-relaxed mt-4 min-h-[3.5rem]">{description}</p>
      <span className="mt-8 inline-flex items-center gap-2 text-[#8C3A2A] font-medium">
        {cta}
        <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
      </span>
    </motion.a>
  );
}
