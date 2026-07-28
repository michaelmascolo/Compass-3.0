import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Loader2, Check, MessageSquareHeart } from "lucide-react";
import { submitFeedback } from "@/lib/api";

// End-of-experience developmental feedback. Collects BOTH instructional signal
// (did Compass help thinking? too much / too little scaffolding? the "aha"
// moment?) and usability signal — treated as equally important.
const QUESTIONS = [
  ["helped_most", "What helped you most?"],
  ["confusing", "What was confusing, frustrating, or unhelpful?"],
  ["improve_one", "If you could change one thing about Compass, what would it be?"],
];
const USE_AGAIN = ["Definitely", "Probably", "Probably not", "No"];

export default function FeedbackModal({ sessionId, onClose }) {
  const [responses, setResponses] = useState({});
  const [useAgain, setUseAgain] = useState("");
  const [comments, setComments] = useState("");
  const [saving, setSaving] = useState(false);
  const [done, setDone] = useState(false);

  const setField = (k, v) => setResponses((r) => ({ ...r, [k]: v }));

  const submit = async () => {
    if (saving || !sessionId) return;
    setSaving(true);
    try {
      await submitFeedback(sessionId, {
        kind: "end",
        responses,
        would_use_again: useAgain || null,
        comments: comments || null,
      });
      setDone(true);
    } catch (e) {
      setDone(true); // never trap the student; acknowledge regardless
    } finally {
      setSaving(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        className="fixed inset-0 z-50 flex items-center justify-center bg-stone-900/40 backdrop-blur-sm px-4 py-8"
        data-testid="feedback-modal"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, y: 16, scale: 0.98 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: 8 }}
          transition={{ duration: 0.3 }}
          onClick={(e) => e.stopPropagation()}
          className="w-full max-w-2xl max-h-[85vh] overflow-y-auto bg-[#fdfcfa] border border-stone-200 rounded-lg shadow-xl p-7"
        >
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.18em] text-[#8C3A2A] font-mono-panel mb-2">
                <MessageSquareHeart className="h-3.5 w-3.5" /> Can we ask a favor?
              </div>
              <h2 className="font-serif-display text-2xl text-stone-900">Can We Ask a Favor?</h2>
              <p className="text-stone-600 text-[14px] leading-relaxed mt-2">
                We're building Compass—and we'd love your help. Compass is still evolving, and we're
                still learning, too. Your experience can help shape what Compass becomes.
              </p>
              <p className="text-stone-600 text-[14px] leading-relaxed mt-2">
                We'd really like to hear what worked, what didn't, and what you think we should
                change. Every suggestion, criticism, and new idea helps us build a better Compass for
                future learners. Even a few words can make a real difference.
              </p>
              <p className="text-stone-600 text-[14px] leading-relaxed mt-2">
                Thank you for helping us build Compass.
              </p>
            </div>
            <button onClick={onClose} data-testid="feedback-close" className="shrink-0 text-stone-400 hover:text-stone-700 transition-colors">
              <X className="h-5 w-5" />
            </button>
          </div>

          {done ? (
            <div className="py-10 text-center" data-testid="feedback-thanks">
              <Check className="h-8 w-8 text-[#8C3A2A] mx-auto mb-3" />
              <p className="font-serif-display text-xl text-stone-800">Thank you — this genuinely helps.</p>
              <button onClick={onClose} data-testid="feedback-done-close" className="mt-5 bg-[#8C3A2A] text-white px-5 py-2.5 rounded-sm font-medium hover:bg-[#6B2C20] transition-colors">
                Close
              </button>
            </div>
          ) : (
            <div className="mt-6 space-y-5">
              {QUESTIONS.map(([key, label], i) => (
                <div key={key}>
                  <label className="block text-[14px] text-stone-800 font-medium mb-1.5">{i + 1}. {label}</label>
                  <textarea
                    data-testid={`feedback-${key}`}
                    value={responses[key] || ""}
                    onChange={(e) => setField(key, e.target.value)}
                    rows={2}
                    className="w-full bg-white border border-stone-300 rounded-sm p-3 text-[14px] leading-relaxed text-stone-900 outline-none focus:ring-1 focus:ring-stone-900 resize-y font-serif-display"
                  />
                </div>
              ))}
              <div>
                <label className="block text-[14px] text-stone-800 font-medium mb-2">4. Would you use Compass again?</label>
                <div className="flex flex-wrap gap-2">
                  {USE_AGAIN.map((opt) => (
                    <button
                      key={opt}
                      onClick={() => setUseAgain(opt)}
                      data-testid={`feedback-useagain-${opt.replace(/\s+/g, "-").toLowerCase()}`}
                      className={`text-[13px] px-3.5 py-1.5 rounded-sm border transition-colors ${
                        useAgain === opt ? "border-[#8C3A2A] bg-[#8C3A2A]/[0.06] text-[#8C3A2A]" : "border-stone-200 text-stone-600 hover:border-stone-400"
                      }`}
                    >
                      {opt}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="block text-[14px] text-stone-800 font-medium mb-1.5">Anything else you'd like to tell us? <span className="text-stone-400 font-normal">(optional)</span></label>
                <textarea
                  data-testid="feedback-comments"
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  rows={2}
                  className="w-full bg-white border border-stone-300 rounded-sm p-3 text-[14px] leading-relaxed text-stone-900 outline-none focus:ring-1 focus:ring-stone-900 resize-y font-serif-display"
                />
              </div>
              <div className="flex items-center gap-3 pt-1">
                <button onClick={submit} disabled={saving} data-testid="feedback-submit"
                  className="inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-6 py-2.5 rounded-sm font-medium hover:bg-[#6B2C20] transition-colors disabled:opacity-40">
                  {saving ? <Loader2 className="h-4 w-4 animate-spin" /> : <Check className="h-4 w-4" />} Send Feedback
                </button>
                <button onClick={onClose} className="text-[13px] text-stone-400 hover:text-stone-700 transition-colors">
                  Maybe Later
                </button>
              </div>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
