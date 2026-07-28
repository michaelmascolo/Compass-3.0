import { useState } from "react";
import { motion } from "framer-motion";
import { Compass, ArrowRight, ArrowLeft } from "lucide-react";

// Genuine STUDENT entry — the learner has been given an assignment and is
// completing it. No teacher-simulation framing ("Experience Compass",
// "experience as one of your students", "create an assignment", "Help me
// create one"). For OT mode, a brief student-facing OT introduction precedes
// the assignment-entry screen.
export default function StudentEntry({ mode, initialAssignment = "", onSubmit, submitting }) {
  const isOT = mode === "ot";
  const [step, setStep] = useState(isOT ? "intro" : "assignment");
  const [assignment, setAssignment] = useState(initialAssignment);
  const canContinue = assignment.trim().length > 0;

  if (step === "intro") {
    return (
      <motion.div
        initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
        className="flex-1 flex flex-col justify-center py-10 max-w-xl"
        data-testid="student-ot-intro"
      >
        <p className="font-mono-panel text-[10px] uppercase tracking-[0.18em] text-stone-400 mb-3">
          Organizing your thinking
        </p>
        <h1 className="font-serif-display text-4xl sm:text-5xl leading-tight text-stone-900">
          Organize Your Thinking
        </h1>
        <p className="text-stone-700 mt-6 text-[16px] leading-relaxed">
          Compass will help you understand your assignment, identify the questions you need to
          answer, develop your ideas, form a current answer, and make a plan before you begin
          writing.
        </p>
        <p className="text-stone-700 mt-4 text-[16px] leading-relaxed">
          Compass will guide your thinking, but it will not do the work for you.
        </p>
        <button
          onClick={() => setStep("assignment")}
          data-testid="student-ot-intro-begin"
          className="group mt-8 self-start inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-7 py-3.5 rounded-sm font-medium tracking-wide hover:bg-[#6B2C20] hover:-translate-y-px transition-[background-color,transform]"
        >
          Begin
          <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
        </button>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}
      className="flex-1 flex flex-col py-6 max-w-xl"
      data-testid="student-entry"
    >
      {isOT && (
        <button
          onClick={() => setStep("intro")}
          data-testid="student-entry-back"
          className="self-start inline-flex items-center gap-1.5 text-[12px] font-mono-panel uppercase tracking-[0.14em] text-stone-400 hover:text-stone-700 transition-colors mb-6"
        >
          <ArrowLeft className="h-3.5 w-3.5" /> Back
        </button>
      )}
      <h1 className="font-serif-display text-4xl sm:text-5xl leading-tight text-stone-900">
        Your Assignment
      </h1>
      <p className="text-stone-700 mt-5 text-[16px] leading-relaxed">
        Paste or type the assignment you are working on.
      </p>
      <p className="text-stone-500 mt-1.5 text-[14px] leading-relaxed">
        Include the complete instructions your teacher gave you.
      </p>

      <textarea
        data-testid="student-assignment-input"
        value={assignment}
        onChange={(e) => setAssignment(e.target.value)}
        rows={7}
        placeholder="Paste or type your assignment here…"
        className="mt-5 w-full bg-white border border-stone-300 rounded-sm p-5 text-[16px] leading-8 text-stone-900 placeholder:text-stone-400 outline-none focus:ring-1 focus:ring-stone-900 focus:border-stone-900 transition-colors resize-y min-h-[180px] font-serif-display"
      />

      <button
        onClick={() => canContinue && onSubmit(assignment.trim())}
        disabled={!canContinue || submitting}
        data-testid="student-assignment-continue"
        className="group mt-6 self-start inline-flex items-center gap-2 bg-[#8C3A2A] text-white px-7 py-3.5 rounded-sm font-medium tracking-wide hover:bg-[#6B2C20] enabled:hover:-translate-y-px transition-[background-color,transform] disabled:opacity-40 disabled:cursor-not-allowed"
      >
        {isOT ? "Continue" : "Continue to Writing"}
        <ArrowRight className="h-4 w-4 transition-transform group-enabled:group-hover:translate-x-1" />
      </button>

      <div className="mt-10 flex items-center gap-2 text-stone-400 font-mono-panel text-[10px] uppercase tracking-[0.16em]">
        <Compass className="h-3.5 w-3.5" />
        Compass
      </div>
    </motion.div>
  );
}
