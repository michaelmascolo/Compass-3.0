// Canonical library of writer metacognition — reusable across the whole system.
//
// PURPOSE: to model, for a student, how EXPERIENCED WRITERS think while they work.
// These are shown during the brief wait after a student shares writing. They must
// NEVER expose Compass's internal reasoning or Stage B's decision process. The
// progression is:  writer thinking  →  Compass instructional focus  (NOT
// Compass reasoning → Compass decision).
//
// Each line is a short, transferable, student-accessible reflection about the
// habits of good writers — about WRITING OPERATIONS, never disciplinary content.

export const WRITER_METACOGNITION = [
  'Every writer starts by asking: "What am I really trying to help my reader understand?"',
  "Strong essays are built one structural element at a time.",
  "Good writers don't just express ideas — they organize them so a reader can follow their thinking.",
  "Revision isn't only fixing mistakes; it's strengthening the structure of your ideas.",
  "Writers keep asking how one idea connects to the next.",
  "A strong paragraph has a clear purpose within the larger essay.",
  "Evidence becomes powerful when the writer helps the reader understand why it matters.",
  "A thesis lets readers anticipate where an essay is going.",
  "Definitions let a writer and a reader share the same understanding of a key idea.",
  "Strong writing grows through many small improvements rather than one perfect draft.",
  "Before adding more, writers ask whether the reader can already follow what's there.",
  "Experienced writers notice the difference between what a sentence says and what it does.",
  "A claim is only as clear as a reader's ability to restate it.",
  "Writers arrange their ideas in the order a reader will need to meet them.",
  "Good introductions prepare a reader; they don't just begin.",
  "Every part of an essay should earn its place by doing a job.",
  "Writers ask what a reader already knows and what they still need to be told.",
  "Explanation is where a writer helps the reader see the thinking behind an idea.",
  "The strongest revisions change structure, not just wording.",
  "Writers build meaning first, then refine the words that carry it.",
  "A conclusion completes a reader's understanding rather than simply stopping.",
  "Transitions are less about connecting words and more about the relationship between ideas.",
  "Writers keep returning to their main point to check that everything still serves it.",
  "Clear writing comes from clear thinking about how the parts fit together.",
  "A writer's first job is to decide what one idea a paragraph is really about.",
  "Good writers read their own draft as a stranger would, not as its author.",
];

// The bridge FROM general writer thinking TO Compass's instructional focus.
// These name Compass's teaching intent for the student's growth — they do NOT
// describe how Compass analyzes, scores, or decides.
export const FOCUS_TRANSITIONS = [
  "Now I'm looking for the one structural element that will help you make the greatest progress as a writer.",
  "Let me find the single move that will strengthen your writing the most right now.",
  "I'm looking for where a little focused work will help your writing grow the most.",
  "I'm finding the one thing worth working on together this time — the move that will help you most.",
];

function _shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

export function pickFocusTransition() {
  return FOCUS_TRANSITIONS[Math.floor(Math.random() * FOCUS_TRANSITIONS.length)];
}

// Build a paced sequence for the wait period. When `toFocus` is true the sequence
// ends on a focus-transition line (writer thinking → instructional focus). When
// false it returns general reflections meant to cycle.
export function metacognitionSequence({ toFocus = true, general = 3 } = {}) {
  const picks = _shuffle(WRITER_METACOGNITION).slice(0, Math.max(1, general));
  return toFocus ? [...picks, pickFocusTransition()] : picks;
}
