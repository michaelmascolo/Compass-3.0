import { motion } from "framer-motion";
import { Compass, ArrowRight, BookOpen, PenTool } from "lucide-react";

// Homepage. Tells the story of Compass: an instructional AI that develops
// thinking rather than replacing it. Editorial "paper" aesthetic, terracotta
// accent, serif display. No SaaS marketing hype.

const EASE = [0.22, 1, 0.36, 1];

// The philosophy contrast — short, slogan-like.
const CONTRAST = [
  ["Most AI gives answers.", "Compass develops thinkers."],
  ["Most AI writes for students.", "Compass teaches students to write."],
  ["Most AI removes productive struggle.", "Compass turns it into learning."],
];

// Primary experience — for educators / reviewers evaluating Compass itself.
const PRIMARY_ENTRY = {
  title: "Experience Compass as an Educator",
  kicker: "Start here · for educators & reviewers",
  description:
    "This experience is designed for teachers, administrators, researchers, and reviewers who want to understand Compass and help us improve it.",
  href: "?preview=teacher",
  testid: "btn-educator-experience",
  Icon: Compass,
};

// Secondary experiences — individual student demonstrations of single components.
const STUDENT_ENTRIES = [
  {
    title: "Student Writing Experience",
    kicker: "Composition",
    description: "A demonstration of how Compass coaches a student through a blank page — teaching, never rewriting.",
    href: "?preview=writing",
    testid: "btn-student-writing",
    Icon: PenTool,
  },
  {
    title: "Organizing Thought Experience",
    kicker: "Pre-writing",
    description: "A demonstration of how Compass helps a student turn chaotic ideas into a structured argument.",
    href: "?preview=ot",
    testid: "btn-student-ot",
    Icon: BookOpen,
  },
];

// Roadmap + 4-step method content was removed from the homepage during the IA
// refinement (2026-06). Preserved for a future About/How-Compass-Works page in
// /app/memory/homepage_removed_content_for_about_page.md

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
            href="?preview=teacher"
            data-testid="nav-try-compass"
            className="group inline-flex items-center gap-2 border border-stone-900 px-4 sm:px-5 py-2 font-mono-panel text-[11px] uppercase tracking-[0.18em] text-stone-900 transition-colors duration-200 hover:bg-stone-900 hover:text-stone-50"
          >
            Experience Compass
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
              AI for developing thinking.
              <span className="block text-[#8C3A2A]">Not replacing it.</span>
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

      {/* Primary experience — the educator / reviewer pathway (obvious starting point) */}
      <section className="max-w-7xl mx-auto px-6 sm:px-8 md:px-16 pb-16 md:pb-20" data-testid="entry-section">
        <div className="max-w-2xl mb-12">
          <p className="font-mono-panel text-xs uppercase tracking-[0.22em] text-[#8C3A2A] font-semibold mb-5">
            The main experience
          </p>
          <h2 className="font-serif-display text-3xl sm:text-4xl tracking-tight leading-tight text-stone-900">
            Experience Compass as an educator
          </h2>
        </div>

        <PrimaryCard {...PRIMARY_ENTRY} />
      </section>

      {/* Secondary experiences — individual student demonstrations */}
      <section className="max-w-7xl mx-auto px-6 sm:px-8 md:px-16 pb-20 md:pb-28" data-testid="student-entry-section">
        <div className="max-w-2xl mb-8 pt-4 border-t border-stone-200">
          <h3 className="font-serif-display text-2xl sm:text-3xl tracking-tight leading-tight text-stone-900 mt-8">
            Explore individual student experiences
          </h3>
          <p className="text-base text-stone-600 leading-relaxed mt-4">
            Optional. These are focused demonstrations of two individual parts of Compass — not the
            complete educator experience above.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-5 md:gap-6">
          {STUDENT_ENTRIES.map((e) => (
            <StudentCard key={e.testid} {...e} />
          ))}
        </div>
      </section>

      {/* Philosophy — What makes Compass different */}
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

      {/* Human statement — why Compass exists */}
      <section className="max-w-7xl mx-auto px-6 sm:px-8 md:px-16 py-20 md:py-28" data-testid="human-statement-section">
        <motion.div
          initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true, margin: "-80px" }} transition={{ duration: 0.6, ease: EASE }}
          className="max-w-3xl"
        >
          <p className="font-mono-panel text-xs uppercase tracking-[0.22em] text-[#8C3A2A] font-semibold mb-6">
            Why we built this
          </p>
          <p className="font-serif-display text-2xl sm:text-3xl leading-snug text-stone-800">
            We built Compass because we believe AI should strengthen learning, not replace the
            thinking that makes it real. This is early, experimental work — and it isn't finished.
            If you try it, we'd love your honest reactions. Your feedback helps shape what Compass
            becomes.
          </p>
        </motion.div>
      </section>

      {/* Closing CTA */}
      <section className="border-t border-stone-200 bg-stone-900 text-stone-50" data-testid="closing-cta">
        <div className="max-w-7xl mx-auto px-6 sm:px-8 md:px-16 py-20 md:py-28">
          <h2 className="font-serif-display text-3xl sm:text-5xl tracking-tight leading-[1.05] max-w-3xl">
            See what it feels like to be taught, not corrected.
          </h2>
          <a
            href="?preview=teacher"
            data-testid="cta-try-compass"
            className="group mt-10 inline-flex items-center gap-3 bg-[#8C3A2A] text-stone-50 px-7 py-4 font-mono-panel text-xs uppercase tracking-[0.2em] transition-colors duration-200 hover:bg-[#a34635]"
          >
            Experience Compass
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

function PrimaryCard({ title, kicker, description, href, testid, Icon }) {
  return (
    <a
      href={href}
      data-testid={testid}
      className="group flex flex-col justify-between bg-[#8C3A2A] text-stone-50 p-8 md:p-12 min-h-[240px]
                 transition-colors duration-200 hover:bg-[#7a3123]
                 focus:outline-none focus:ring-2 focus:ring-[#8C3A2A] focus:ring-offset-2"
    >
      <div>
        <div className="flex items-center gap-2 font-mono-panel text-[11px] uppercase tracking-[0.2em] text-stone-50/70">
          <Icon className="h-4 w-4" strokeWidth={1.5} />
          {kicker}
        </div>
        <h3 className="font-serif-display text-3xl md:text-4xl mt-6 leading-tight max-w-2xl">{title}</h3>
        <p className="text-stone-50/85 leading-relaxed mt-4 max-w-2xl text-lg">{description}</p>
      </div>
      <span className="mt-8 inline-flex items-center gap-2 font-mono-panel text-xs uppercase tracking-[0.18em]">
        Begin the educator experience
        <ArrowRight className="h-4 w-4 transition-transform duration-200 group-hover:translate-x-1" />
      </span>
    </a>
  );
}

function StudentCard({ title, kicker, description, href, testid, Icon }) {
  return (
    <a
      href={href}
      data-testid={testid}
      className="group flex flex-col justify-between border border-stone-300 bg-white p-6 md:p-7 min-h-[220px]
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
        View demonstration
        <ArrowRight className="h-3.5 w-3.5 transition-transform duration-200 group-hover:translate-x-1" />
      </span>
    </a>
  );
}
