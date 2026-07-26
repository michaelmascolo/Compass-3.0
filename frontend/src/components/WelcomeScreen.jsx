import { motion } from "framer-motion";
import { ArrowRight, Compass } from "lucide-react";

// Chapter 3 — the first surface of Experience Compass. It prepares the educator
// to temporarily become the learner: they will experience Compass directly, not
// watch a demonstration. One calm centered content area; a single Begin action
// that advances to the existing seed screen. No account, pricing, marketing,
// feature lists, tour, or extra onboarding.
export default function WelcomeScreen({ onBegin }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.55, ease: "easeOut" }}
      className="flex-1 flex flex-col justify-center max-w-xl mx-auto w-full py-12"
      data-testid="welcome-screen"
    >
      <div className="flex items-center gap-2 font-mono-panel text-[11px] uppercase tracking-[0.2em] text-stone-500 mb-8">
        <Compass className="h-4 w-4 text-[#8C3A2A]" />
        Experience Compass
      </div>

      <h1 className="font-serif-display text-3xl sm:text-4xl leading-snug text-stone-900">
        Welcome to Experience Compass
      </h1>

      <div className="mt-6 space-y-4 text-stone-700 text-[16px] leading-relaxed">
        <p>
          For the next few minutes, you'll experience Compass as one of your students would.
        </p>
        <p>
          You'll create a brief assignment, write a one-paragraph response, and work with Compass to
          strengthen it.
        </p>
        <p>
          Compass will not simply correct your writing or do the work for you. It will try to teach by
          helping you examine and develop your own thinking and writing.
        </p>
      </div>

      <button
        onClick={onBegin}
        data-testid="welcome-begin-button"
        className="mt-9 self-start group inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-8 py-3 rounded-sm font-medium tracking-wide hover:bg-[#6B2C20] hover:-translate-y-px transition-[background-color,transform]"
      >
        Begin
        <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
      </button>
    </motion.div>
  );
}
