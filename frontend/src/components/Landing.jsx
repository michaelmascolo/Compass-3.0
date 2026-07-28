import { motion } from "framer-motion";
import { Compass, ArrowRight, BookOpen, PenTool } from "lucide-react";

// Homepage. Tells the story of Compass: an instructional AI that develops
// thinking rather than replacing it. Editorial "paper" aesthetic, terracotta
// accent, serif display. No SaaS marketing hype.

const EASE = [0.22, 1, 0.36, 1];

// The philosophy contrast — the heart of the page.
const CONTRAST = [
  ["Most AI answers the question.", "Compass develops the thinking behind the question."],
  ["Most AI generates the writing.", "Compass builds the thinking that makes writing possible."],
  ["Most AI removes the struggle.", "Compass coaches you through it."],
];

// Three entry points into Compass. Each routes to an existing experience.
const ENTRIES = [
  {
    title: "Try Compass",
    kicker: "Start here",
    description:
      "Experience the instructional philosophy first-hand, and share feedback while Compass is still in early development.",
    href: "?review",
    testid: "btn-try-compass",
    Icon: Compass,
    dominant: true,
  },
  {
    title: "Student Writing Experience",
    kicker: "Composition",
    description: "See how Compass coaches a student through a blank page — teaching, never rewriting.",
    href: "?preview=writing",
    testid: "btn-student-writing",
    Icon: PenTool,
  },
  {
    title: "Organizing Thought Experience",
    kicker: "Pre-writing",
    description: "See how Compass helps a student turn chaotic ideas into a structured argument.",
    href: "?preview=ot",
    testid: "btn-student-ot",
    Icon: BookOpen,
  },
];

// The developmental order in which Compass itself is being built.
const ROADMAP = [
  { label: "Now", title: "Composition", status: "current" },
  { label: "Next", title: "Organizing Ideas", status: "next" },
  { label: "Future", title: "Integrated Compass", status: "future" },
];

// How a single Compass interaction unfolds.
const STEPS = [
  ["Understanding", "Compass first reads the writing as a reader would, to grasp what the student is actually trying to say."],
  ["Recognition", "It names what the student has already done well — the productive move they have begun to make."],
  ["Developmental invitation", "It chooses one instructional focus and invites the student to take the next thinking step themselves."],
  ["Teaching", "It scaffolds that one move — never rewriting the work or supplying the ideas."],
];

export default function Landing() {
  return (
    <div className="min-h-screen paper-grain text-stone-900" data-testid="landing-page">
      {/* Editorial sticky nav */}
      <header className="sticky top-0 z-30 border-b border-stone-200 bg-[#faf9f6]/85 backdrop-blur-md">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 md:px-16 h-16 flex items-center justify-between">
          <a href="/" className="flex items-center gap-3" data-testid="nav-logo">
            <img src="/cgi-logo.png" alt="Common Ground Institute" className="h-7 w-auto" />
            <span className="hidden sm:inline-block h-5 w-px bg-stone-300" />
            <span className="hidden sm:inline font-serif-display text-lg tracking-tight text-stone-800">
              Compass
            </span>
          </a>
          <a
            href="?review"
            data-testid="nav-try-compass"
            className="group inline-flex items-center gap-2 border border-stone-900 px-4 sm:px-5 py-2 font-mono-panel text-[11px] uppercase tracking-[0.18em] text-stone-900 transition-colors duration-200 hover:bg-stone-900 hover:text-stone-50"
          >
            Try Compass
            <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-0.5" />
          </a>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-6 sm:px-8 md:px-16">
        {/* Hero */}
        <section className="pt-24 md:pt-40 pb-16 md:pb-28 grid grid-cols-1 lg:grid-cols-12 gap-10">
          <div className="lg:col-span-9">
            <motion.p
              initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, ease: EASE }}
              className="font-mono-panel text-xs sm:text-sm uppercase tracking-[0.22em] text-[#8C3A2A] font-semibold mb-8"
            >
              The Compass Philosophy
            </motion.p>
            <motion.h1
              initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.06, ease: EASE }}
              className="font-serif-display text-5xl sm:text-6xl lg:text-7xl tracking-tight leading-[1.02] text-stone-900"
            >
              AI that develops thinking.
              <span className="block text-[#8C3A2A]">Not replaces it.</span>
            </motion.h1>
            <motion.p
              initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.7, delay: 0.16, ease: EASE }}
              className="text-lg sm:text-xl text-stone-700 leading-relaxed mt-10 max-w-2xl"
            >
              Compass is an experimental instructional system that coaches students through the messy,
              beautiful process of thought — teaching them to write well rather than writing for them.
            </motion.p>
          </div>
        </section>
      </main>

      {/* Philosophy — bold high-contrast split */}
      <section className="border-y border-stone-200 bg-[#f2f0ed]" data-testid="philosophy-section">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 md:px-16 py-20 md:py-28">
          <p className="font-mono-panel text-xs uppercase tracking-[0.22em] text-stone-500 mb-12">
            What makes Compass different
          </p>
          <div className="space-y-px">
            {CONTRAST.map(([most, compass], i) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true, margin: "-80px" }} transition={{ duration: 0.6, delay: i * 0.08, ease: EASE }}
                className="grid grid-cols-1 md:grid-cols-2 gap-6 md:gap-16 py-8 md:py-10 border-t border-stone-300 first:border-t-0"
                data-testid={`contrast-row-${i}`}
              >
                <p className="font-serif-display text-2xl md:text-3xl leading-snug text-stone-400">
                  {most}
                </p>
                <p className="font-serif-display text-2xl md:text-3xl leading-snug text-[#8C3A2A]">
                  {compass}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Entry points */}
      <section className="max-w-7xl mx-auto px-6 sm:px-8 md:px-16 py-20 md:py-28" data-testid="entry-section">
        <div className="max-w-2xl mb-14">
          <p className="font-mono-panel text-xs uppercase tracking-[0.22em] text-[#8C3A2A] font-semibold mb-5">
            Step inside
          </p>
          <h2 className="font-serif-display text-3xl sm:text-4xl tracking-tight leading-tight text-stone-900">
            Three ways to experience Compass
          </h2>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-5 gap-5 md:gap-6">
          {ENTRIES.map((e) => (
            <EntryCard key={e.testid} {...e} />
          ))}
        </div>
      </section>

      {/* Roadmap */}
      <section className="border-t border-stone-200 bg-[#f2f0ed]" data-testid="roadmap-section">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 md:px-16 py-20 md:py-24">
          <p className="font-mono-panel text-xs uppercase tracking-[0.22em] text-stone-500 mb-14">
            Where Compass is going
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 border-t border-stone-300">
            {ROADMAP.map((r, i) => (
              <motion.div
                key={r.title}
                initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }} transition={{ duration: 0.5, delay: i * 0.08, ease: EASE }}
                className="relative pt-8 pb-2 md:pr-10 border-t border-stone-300 md:border-t-0 first:border-t-0"
                data-testid={`roadmap-${r.status}`}
              >
                <span
                  className={`absolute -top-[6px] left-0 h-[11px] w-[11px] rounded-full border-2 ${
                    r.status === "current" ? "border-[#8C3A2A] bg-[#8C3A2A]" : "border-stone-400 bg-[#f2f0ed]"
                  }`}
                />
                <div className="font-mono-panel text-[11px] uppercase tracking-[0.2em] text-[#8C3A2A]">
                  {r.label}
                </div>
                <p className={`font-serif-display text-2xl md:text-[28px] mt-3 ${r.status === "current" ? "text-stone-900" : "text-stone-500"}`}>
                  {r.title}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* Explainer — how a Compass interaction unfolds */}
      <section className="max-w-7xl mx-auto px-6 sm:px-8 md:px-16 py-20 md:py-28" data-testid="explainer-section">
        <div className="max-w-2xl mb-16">
          <p className="font-mono-panel text-xs uppercase tracking-[0.22em] text-[#8C3A2A] font-semibold mb-5">
            The method
          </p>
          <h2 className="font-serif-display text-3xl sm:text-4xl tracking-tight leading-tight text-stone-900">
            How a single Compass interaction unfolds
          </h2>
          <p className="text-lg text-stone-700 leading-relaxed mt-6">
            Compass supports the relationship between a teacher and a learner. It teaches, rather than
            edits — the student always remains the author of their work.
          </p>
        </div>
        <ol className="max-w-3xl">
          {STEPS.map(([title, body], i) => (
            <motion.li
              key={title}
              initial={{ opacity: 0, y: 12 }} whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }} transition={{ duration: 0.5, delay: i * 0.06, ease: EASE }}
              className="flex gap-6 md:gap-10 py-8 border-b border-stone-200"
              data-testid={`explainer-step-${i}`}
            >
              <span className="font-serif-display text-4xl md:text-5xl text-stone-300 leading-none w-12 shrink-0">
                {String(i + 1).padStart(2, "0")}
              </span>
              <div>
                <h3 className="font-serif-display text-xl md:text-2xl text-stone-900">{title}</h3>
                <p className="text-stone-700 leading-relaxed mt-2">{body}</p>
              </div>
            </motion.li>
          ))}
        </ol>
      </section>

      {/* Closing CTA */}
      <section className="border-t border-stone-200 bg-stone-900 text-stone-50" data-testid="closing-cta">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 md:px-16 py-20 md:py-28">
          <h2 className="font-serif-display text-3xl sm:text-5xl tracking-tight leading-[1.05] max-w-3xl">
            See what it feels like to be taught, not corrected.
          </h2>
          <a
            href="?review"
            data-testid="cta-try-compass"
            className="group mt-10 inline-flex items-center gap-3 bg-[#8C3A2A] text-stone-50 px-7 py-4 font-mono-panel text-xs uppercase tracking-[0.2em] transition-colors duration-200 hover:bg-[#a34635]"
          >
            Try Compass
            <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-stone-200 bg-[#faf9f6]">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 md:px-16 py-14 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
          <img src="/cgi-logo.png" alt="Common Ground Institute" className="h-8 w-auto" />
          <p className="font-mono-panel text-[11px] uppercase tracking-[0.16em] text-stone-400">
            A nonprofit project of the Common Ground Institute
          </p>
        </div>
      </footer>
    </div>
  );
}

function EntryCard({ title, kicker, description, href, testid, Icon, dominant }) {
  if (dominant) {
    return (
      <a
        href={href}
        data-testid={testid}
        className="group lg:col-span-3 flex flex-col justify-between bg-[#8C3A2A] text-stone-50 p-8 md:p-10 min-h-[240px]
                   transition-colors duration-200 hover:bg-[#7a3123]
                   focus:outline-none focus:ring-2 focus:ring-[#8C3A2A] focus:ring-offset-2"
      >
        <div>
          <div className="flex items-center gap-2 font-mono-panel text-[11px] uppercase tracking-[0.2em] text-stone-50/70">
            <Icon className="h-4 w-4" strokeWidth={1.5} />
            {kicker}
          </div>
          <h3 className="font-serif-display text-3xl md:text-4xl mt-6 leading-tight">{title}</h3>
          <p className="text-stone-50/85 leading-relaxed mt-4 max-w-md">{description}</p>
        </div>
        <span className="mt-8 inline-flex items-center gap-2 font-mono-panel text-xs uppercase tracking-[0.18em]">
          Begin
          <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
        </span>
      </a>
    );
  }
  return (
    <a
      href={href}
      data-testid={testid}
      className="group lg:col-span-1 flex flex-col justify-between border border-stone-300 bg-white p-6 md:p-7 min-h-[240px]
                 transition-colors duration-200 hover:border-stone-900
                 focus:outline-none focus:ring-2 focus:ring-[#8C3A2A] focus:ring-offset-2"
    >
      <div>
        <div className="flex items-center gap-2 font-mono-panel text-[11px] uppercase tracking-[0.2em] text-[#8C3A2A]">
          <Icon className="h-4 w-4" strokeWidth={1.5} />
          {kicker}
        </div>
        <h3 className="font-serif-display text-xl md:text-2xl mt-6 leading-snug text-stone-900">{title}</h3>
        <p className="text-[14px] text-stone-600 leading-relaxed mt-3">{description}</p>
      </div>
      <span className="mt-6 inline-flex items-center gap-2 font-mono-panel text-[11px] uppercase tracking-[0.18em] text-stone-900">
        Begin
        <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-1" />
      </span>
    </a>
  );
}
