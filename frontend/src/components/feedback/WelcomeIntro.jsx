import { motion } from "framer-motion";
import { Sparkles } from "lucide-react";

// Compass developmental-feedback INTRODUCTION. Framed so students understand
// Compass is experimental and that their experience shapes future versions.
export default function WelcomeIntro() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}
      data-testid="compass-welcome-intro"
      className="mb-6 bg-[#faf7f2] border border-stone-200 rounded-md px-5 py-4"
    >
      <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.18em] text-[#8C3A2A] font-mono-panel mb-1.5">
        <Sparkles className="h-3.5 w-3.5" /> Welcome
      </div>
      <p className="text-stone-700 text-[14px] leading-relaxed">
        Compass is an experimental learning system. Its goal is not to do your thinking for you, but
        to help you develop your own thinking. We're continually improving Compass, and your
        experience will directly shape future versions. Thank you for helping us build it.
      </p>
    </motion.div>
  );
}
