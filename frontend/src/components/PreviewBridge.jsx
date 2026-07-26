import { useState } from "react";
import { motion } from "framer-motion";
import { ArrowRight, Loader2 } from "lucide-react";
import { previewContinue } from "@/lib/api";

const ease = [0.22, 1, 0.36, 1];

// RETAINED FOR SLICE 2 — the planned "Bring your own writing" bridge. Intentionally
// NOT imported by PublicPreview (unlinked from the Slice 1 reflection). Do not
// reconnect until the Slice 2 "Bring your own writing" workflow is implemented.
// S3 — the quiet room after the aha. One question: "Could I use this with my students?"
// Grounded ONLY in what the visitor just did; never a fabricated claim about their students.
export default function PreviewBridge({ sessionId, onBack }) {
  const [continuing, setContinuing] = useState(false);

  const handleContinue = async () => {
    if (continuing) return;
    setContinuing(true);
    try {
      if (sessionId) await previewContinue(sessionId);
    } catch (e) {
      /* non-blocking analytics */
    } finally {
      window.location.href = `${window.location.pathname}?app`;
    }
  };

  return (
    <div className="min-h-screen paper-grain flex flex-col items-center justify-center px-6">
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.9, ease }}
        className="max-w-xl w-full text-center py-24"
        data-testid="preview-bridge"
      >
        <span className="font-mono-panel text-xs uppercase tracking-[0.2em] text-stone-500 mb-7 block">
          Before you go
        </span>
        <h1 className="font-serif-display text-4xl md:text-5xl tracking-tight text-stone-900 leading-tight">
          You just taught yourself.
        </h1>
        <p className="text-lg text-stone-700 leading-relaxed mt-6">
          No one handed you the answer, and no one wrote it for you. You were led
          to it — and it became yours. That is the shift a whole class could feel,
          on their own writing, one conversation at a time.
        </p>

        <div className="mt-12 flex flex-col sm:flex-row items-center justify-center gap-4">
          <motion.button
            whileHover={{ scale: 1.02 }}
            transition={{ duration: 0.2 }}
            onClick={handleContinue}
            disabled={continuing}
            data-testid="bridge-continue"
            className="group inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-7 py-3.5 rounded-sm font-medium tracking-wide hover:bg-[#6B2C20] transition-colors disabled:opacity-50 focus:ring-2 focus:ring-[#8C3A2A] focus:outline-none"
          >
            {continuing ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Opening…
              </>
            ) : (
              <>
                Continue with a real assignment
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
              </>
            )}
          </motion.button>
          <button
            onClick={onBack || (() => (window.location.href = window.location.pathname))}
            data-testid="bridge-back"
            className="text-stone-500 hover:text-stone-900 underline underline-offset-4 decoration-stone-300 transition-colors px-4 py-2 text-sm"
          >
            Not now
          </button>
        </div>
      </motion.div>
    </div>
  );
}
