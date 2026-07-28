import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2 } from "lucide-react";
import { submitFeedback } from "@/lib/api";

// Early-exit intercept — shown when a student chooses to leave before finishing.
// One sentence of "why" is enough; the student is never trapped ("Leave anyway").
const REASONS = [
  ["finished", "I finished what I needed."],
  ["confused", "I became confused."],
  ["too_long", "It was taking longer than I expected."],
  ["broken", "Something wasn't working."],
  ["later", "I'll come back later."],
  ["other", "Other"],
];

export default function EarlyExitModal({ sessionId, onLeave }) {
  const [reason, setReason] = useState("");
  const [comments, setComments] = useState("");
  const [saving, setSaving] = useState(false);

  const finish = async (send) => {
    if (saving) return;
    if (send && sessionId) {
      setSaving(true);
      try {
        await submitFeedback(sessionId, { kind: "early_exit", exit_reason: reason || "unspecified", comments: comments || null });
      } catch (e) { /* never block leaving */ }
      setSaving(false);
    }
    onLeave();
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/40 backdrop-blur-sm px-4"
        data-testid="early-exit-modal"
      >
        <motion.div
          initial={{ opacity: 0, y: 16, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0 }}
          transition={{ duration: 0.28 }}
          className="w-full max-w-lg bg-[#fdfcfa] border border-stone-200 rounded-lg shadow-xl p-7"
        >
          <h2 className="font-serif-display text-2xl text-stone-900">Before you go…</h2>
          <p className="text-stone-600 text-[14px] leading-relaxed mt-2">
            Can we ask one small favor? We're still building Compass, and we're still learning what
            works best. If you have a moment, we'd really appreciate knowing why you're leaving.
            Even a sentence or two helps us make Compass better for the next person who uses it.
          </p>
          <div className="mt-5 space-y-1.5">
            {REASONS.map(([val, label]) => (
              <button
                key={val}
                onClick={() => setReason(val)}
                data-testid={`early-exit-reason-${val}`}
                className={`w-full text-left flex items-center gap-2.5 px-3 py-2 rounded-sm border transition-colors ${
                  reason === val ? "border-[#8C3A2A] bg-[#8C3A2A]/[0.05]" : "border-stone-200 hover:border-stone-300"
                }`}
              >
                <span className={`h-3.5 w-3.5 rounded-full border shrink-0 ${reason === val ? "border-[#8C3A2A] bg-[#8C3A2A]" : "border-stone-400"}`} />
                <span className="text-[14px] text-stone-800">{label}</span>
              </button>
            ))}
          </div>
          <textarea
            data-testid="early-exit-comments"
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            rows={2}
            placeholder="Comments (optional)…"
            className="mt-4 w-full bg-white border border-stone-300 rounded-sm p-3 text-[14px] leading-relaxed text-stone-900 placeholder:text-stone-400 outline-none focus:ring-1 focus:ring-stone-900 resize-y font-serif-display"
          />
          <div className="mt-5 flex items-center gap-3">
            <button onClick={() => finish(true)} disabled={saving} data-testid="early-exit-submit"
              className="inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-5 py-2.5 rounded-sm font-medium hover:bg-[#6B2C20] transition-colors disabled:opacity-40">
              {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : null} Send Feedback
            </button>
            <button onClick={() => finish(false)} data-testid="early-exit-leave" className="text-[13px] text-stone-500 hover:text-stone-800 transition-colors">
              Leave Without Feedback
            </button>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
