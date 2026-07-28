import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Terminal,
  X,
  Pencil,
  Save,
  RotateCcw,
  ChevronRight,
  Target,
  Link2,
  Clock,
  Circle,
  MinusCircle,
  Loader2,
  GraduationCap,
  Microscope,
  Download,
  GitBranch,
  Layers,
  ClipboardList,
} from "lucide-react";

const API_BASE = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SectionLabel = ({ children }) => (
  <div className="text-[10px] uppercase tracking-[0.2em] text-amber-500 mb-1.5">
    {children}
  </div>
);

const Block = ({ label, children }) => (
  <div className="border-t border-stone-800 pt-3 mt-3 first:border-t-0 first:pt-0 first:mt-0">
    <SectionLabel>{label}</SectionLabel>
    <div className="text-stone-300 leading-relaxed text-[13px]">{children}</div>
  </div>
);

const List = ({ items }) => {
  if (!items || items.length === 0)
    return <span className="text-stone-600">—</span>;
  return (
    <ul className="space-y-1.5">
      {items.map((it, i) => (
        <li key={i} className="flex gap-2">
          <span className="text-stone-600 select-none">›</span>
          <span>{it}</span>
        </li>
      ))}
    </ul>
  );
};

const Text = ({ value }) =>
  value ? <span>{value}</span> : <span className="text-stone-600">—</span>;

// key/value row used throughout the reasoning blocks
const KV = ({ k, accent, children }) => (
  <div>
    <span className="text-stone-500">{k}:</span>{" "}
    {accent ? <span className={accent}>{children}</span> : children}
  </div>
);

const GroupHeader = ({ children }) => (
  <div className="text-[10px] uppercase tracking-[0.22em] text-stone-500 mt-5 mb-2 flex items-center gap-2">
    <span className="h-px flex-1 bg-stone-800" />
    {children}
    <span className="h-px flex-1 bg-stone-800" />
  </div>
);

// Status is communicated with an icon + a text label (never color alone).
const STATUS_META = {
  primary: { label: "Primary", tlabel: "Focus", Icon: Target, cls: "text-amber-300 border-amber-500/40 bg-amber-500/10" },
  supporting: { label: "Supporting", tlabel: "Supporting", Icon: Link2, cls: "text-sky-300 border-sky-500/40 bg-sky-500/10" },
  postponed: { label: "Postponed", tlabel: "Postponed", Icon: Clock, cls: "text-stone-400 border-stone-600 bg-stone-800/50" },
  applicable: { label: "Applicable", tlabel: "In view", Icon: Circle, cls: "text-emerald-300 border-emerald-500/40 bg-emerald-500/10" },
  not_applicable: { label: "Not applicable", tlabel: "Not now", Icon: MinusCircle, cls: "text-stone-500 border-stone-700 bg-stone-900" },
};

const Badge = ({ status, research }) => {
  const m = STATUS_META[status];
  if (!m) return null;
  const I = m.Icon;
  return (
    <span
      data-testid={`framework-status-${status}`}
      className={`shrink-0 inline-flex items-center gap-1 text-[9px] uppercase tracking-[0.12em] px-1.5 py-0.5 rounded-sm border ${m.cls}`}
    >
      <I className="h-3 w-3" />
      {research ? m.label : m.tlabel}
    </span>
  );
};

// Teacher-facing labels. Internal theory names appear only in Research/Developer view.
const FW_TEACHER = {
  communicative_purpose: "What the Writing Is Trying to Do",
  paragraph_function: "How This Paragraph Works",
  evidence_function: "How Evidence Is Working",
  coherence_function: "How Ideas Connect",
  conclusion_function: "How the Ending Works",
  reader_construction: "Reader Understanding",
  revision_development: "Student Growth",
};

function Accordion({ id, title, badge, open, onToggle, accent, children }) {
  return (
    <div className={`border border-stone-800 rounded-sm mb-2 bg-stone-950/30 ${accent || ""}`}>
      <button
        type="button"
        data-testid={`accordion-toggle-${id}`}
        onClick={onToggle}
        aria-expanded={open}
        aria-controls={`accordion-panel-${id}`}
        className="w-full flex items-center justify-between gap-2 px-3 py-2.5 text-left hover:bg-stone-800/40 transition-colors focus:outline-none focus-visible:ring-1 focus-visible:ring-amber-500 rounded-sm"
      >
        <span className="flex items-center gap-2 min-w-0">
          <ChevronRight
            className={`h-3.5 w-3.5 shrink-0 text-stone-500 transition-transform ${open ? "rotate-90" : ""}`}
          />
          <span className="text-[11px] uppercase tracking-[0.14em] text-stone-200 truncate">
            {title}
          </span>
        </span>
        {badge}
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            id={`accordion-panel-${id}`}
            role="region"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="px-3.5 pb-3 pt-1 text-stone-300 leading-relaxed text-[13px]">
              {children}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

// --- Framework definitions (data + testids preserved exactly) --------------
const FRAMEWORKS = [
  {
    id: "communicative_purpose",
    label: "Communicative Purpose (M6)",
    keywords: ["communicative purpose", "whole essay", "essay purpose", "central claim", "thesis", "claim", "purpose"],
    applies: () => true, // no applies field — always an active lens
    content: (t) => (
      <div className="space-y-1.5" data-testid="communicative-purpose-block">
        <KV k="primary" accent="text-amber-300">
          <Text value={t.communicative_purpose?.primary} />
        </KV>
        <KV k="secondary">
          <List items={t.communicative_purpose?.secondary} />
        </KV>
        <KV k="inferred from">
          <Text value={t.communicative_purpose?.inferred_from} />
        </KV>
        {t.communicative_purpose?.uncertainty ? (
          <KV k="uncertainty">
            <Text value={t.communicative_purpose?.uncertainty} />
          </KV>
        ) : null}
      </div>
    ),
  },
  {
    id: "paragraph_function",
    label: "Paragraph Function (M7)",
    keywords: ["paragraph"],
    applies: (t) => !!t.paragraph_function?.applies,
    content: (t) => (
      <div className="space-y-1.5" data-testid="paragraph-function-block">
        <KV k="purpose" accent="text-amber-300">
          <Text value={t.paragraph_function?.purpose} />
        </KV>
        <KV k="contribution to whole">
          <Text value={t.paragraph_function?.contribution_to_whole} />
        </KV>
        <KV k="coherence">
          <Text value={t.paragraph_function?.coherence} />
        </KV>
        <KV k="development">
          <Text value={t.paragraph_function?.development} />
        </KV>
        <KV k="placement">
          <Text value={t.paragraph_function?.placement} />
        </KV>
      </div>
    ),
  },
  {
    id: "evidence_function",
    label: "Evidence Function (M8)",
    keywords: ["evidence", "support"],
    applies: (t) => !!t.evidence_function?.applies,
    content: (t) => (
      <div className="space-y-1.5" data-testid="evidence-function-block">
        <KV k="forms">
          <List items={t.evidence_function?.forms} />
        </KV>
        <KV k="function" accent="text-amber-300">
          <Text value={t.evidence_function?.function} />
        </KV>
        <KV k="interpretation gap">
          <Text value={t.evidence_function?.interpretation_gap} />
        </KV>
        <KV k="quality (functional)">
          <Text value={t.evidence_function?.quality} />
        </KV>
      </div>
    ),
  },
  {
    id: "coherence_function",
    label: "Transitions & Coherence (M9)",
    keywords: ["coherence", "transition", "flow"],
    applies: (t) => !!t.coherence_function?.applies,
    content: (t) => (
      <div className="space-y-1.5" data-testid="coherence-function-block">
        <KV k="intended relationship" accent="text-amber-300">
          <Text value={t.coherence_function?.intended_relationship} />
        </KV>
        <KV k="level">
          <Text value={t.coherence_function?.level} />
        </KV>
        <KV k="resources in use">
          <List items={t.coherence_function?.resources_in_use} />
        </KV>
        <KV k="reader can follow">
          <Text value={t.coherence_function?.reader_can_follow} />
        </KV>
      </div>
    ),
  },
  {
    id: "conclusion_function",
    label: "Conclusion / Completion (M10)",
    keywords: ["conclusion", "completion", "ending"],
    applies: (t) => !!t.conclusion_function?.applies,
    content: (t) => (
      <div className="space-y-1.5" data-testid="conclusion-function-block">
        <KV k="functions in play">
          <List items={t.conclusion_function?.functions_in_play} />
        </KV>
        <KV k="completes purpose" accent="text-amber-300">
          <Text value={t.conclusion_function?.completes_purpose} />
        </KV>
        <KV k="relationship to opening">
          <Text value={t.conclusion_function?.relationship_to_opening} />
        </KV>
        <KV k="final understanding">
          <Text value={t.conclusion_function?.final_understanding} />
        </KV>
      </div>
    ),
  },
  {
    id: "reader_construction",
    label: "Reader Construction (M12)",
    keywords: ["reader"],
    applies: (t) => !!t.reader_construction?.applies,
    content: (t) => (
      <div className="space-y-1.5" data-testid="reader-construction-block">
        <KV k="reader understands" accent="text-amber-300">
          <Text value={t.reader_construction?.reader_understanding} />
        </KV>
        <KV k="likely questions">
          <List items={t.reader_construction?.likely_reader_questions} />
        </KV>
        <KV k="assumed knowledge">
          <Text value={t.reader_construction?.assumed_knowledge} />
        </KV>
        <KV k="clarification needed">
          <Text value={t.reader_construction?.clarification_needed} />
        </KV>
        <KV k="elaboration needed">
          <Text value={t.reader_construction?.elaboration_needed} />
        </KV>
        <KV k="precision risk">
          <Text value={t.reader_construction?.precision_risk} />
        </KV>
        <KV k="next reader need" accent="text-sky-300">
          <Text value={t.reader_construction?.next_reader_need} />
        </KV>
      </div>
    ),
  },
  {
    id: "revision_development",
    label: "Revision as Development (M13)",
    keywords: ["revision", "revise", "growth"],
    applies: (t) => !!t.revision_development?.applies,
    content: (t) => (
      <div className="space-y-1.5" data-testid="revision-development-block">
        <KV k="development detected" accent="text-amber-300">
          <Text value={t.revision_development?.development_detected} />
        </KV>
        <KV k="primary growth">
          <Text value={t.revision_development?.primary_growth} />
        </KV>
        <KV k="communication change">
          <Text value={t.revision_development?.communication_change} />
        </KV>
        <KV k="reader change">
          <Text value={t.revision_development?.reader_change} />
        </KV>
        <KV k="remaining opportunity">
          <Text value={t.revision_development?.remaining_opportunity} />
        </KV>
        <KV k="transfer message" accent="text-emerald-300">
          <Text value={t.revision_development?.transfer_message} />
        </KV>
      </div>
    ),
  },
];

function pickPrimary(theory, appliesMap) {
  const pf = (theory.integration_calibration?.primary_framework || "").toLowerCase();
  let best = null;
  let bestIdx = Infinity;
  for (const fw of FRAMEWORKS) {
    if (!appliesMap[fw.id]) continue;
    for (const k of fw.keywords) {
      const i = pf.indexOf(k);
      if (i >= 0 && i < bestIdx) {
        bestIdx = i;
        best = fw.id;
      }
    }
  }
  return best;
}

function frameworkStatuses(theory) {
  const supp = (theory.integration_calibration?.supporting_frameworks || []).join(" ").toLowerCase();
  const postponed = (theory.scaffolding_control?.postponed || []).join(" ").toLowerCase();
  const appliesMap = {};
  for (const fw of FRAMEWORKS) appliesMap[fw.id] = fw.applies(theory);
  const primaryId = pickPrimary(theory, appliesMap);
  const out = { __primary: primaryId };
  for (const fw of FRAMEWORKS) {
    let status;
    if (!appliesMap[fw.id]) status = "not_applicable";
    else if (fw.id === primaryId) status = "primary";
    else if (fw.keywords.some((k) => postponed.includes(k))) status = "postponed";
    else if (fw.keywords.some((k) => supp.includes(k))) status = "supporting";
    else status = "applicable";
    out[fw.id] = { applies: appliesMap[fw.id], status };
  }
  return out;
}

// Teacher view only: strip internal theory names / Milestone tags from the
// LLM-emitted data strings so no internal terminology leaks into teacher labels.
// Data/reasoning is untouched; research view shows the raw values.
function humanizeFramework(s) {
  if (!s) return s;
  return s
    .replace(/\s*\(\s*M\d+[^)]*\)/gi, "")
    .replace(/\bM\d+\b/gi, "")
    .replace(/reader construction/gi, "reader understanding")
    .replace(/communicative purpose/gi, "purpose")
    .replace(/revision development/gi, "growth across drafts")
    .replace(/scaffolding controller?/gi, "developmental focus")
    .replace(/integration (?:and|&) calibration/gi, "overall calibration")
    .replace(/\bframework\b/gi, "focus")
    .replace(/\s{2,}/g, " ")
    .replace(/\s+([—–-])\s*$/, "")
    .trim()
    .replace(/^([a-z])/, (m) => m.toUpperCase());
}

function computeDefaults(theory) {
  const st = frameworkStatuses(theory);
  const map = {
    scaffolding_control: true,
    integration_calibration: true,
    instructional_reasoning: true,
    developmental_memory: true,
    intervention: true,
    detail: false,
  };
  for (const fw of FRAMEWORKS) {
    const s = st[fw.id].status;
    // expand primary + supporting; collapse not-applicable, postponed, plain-applicable
    map[fw.id] = s === "primary" || s === "supporting";
  }
  return map;
}

function TelosEditor({ session, onSave, saving }) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    assignment: session.assignment,
    pedagogical_purpose: session.pedagogical_purpose,
    current_writing_task: session.current_writing_task,
  });

  useEffect(() => {
    setForm({
      assignment: session.assignment,
      pedagogical_purpose: session.pedagogical_purpose,
      current_writing_task: session.current_writing_task,
    });
  }, [session.assignment, session.pedagogical_purpose, session.current_writing_task]);

  const field = (key, label) => (
    <div>
      <SectionLabel>{label}</SectionLabel>
      <textarea
        data-testid={`telos-edit-${key}`}
        value={form[key]}
        onChange={(e) => setForm({ ...form, [key]: e.target.value })}
        rows={2}
        className="w-full bg-stone-950 border border-stone-700 rounded-sm p-2 text-[12px] text-stone-200 outline-none focus:border-amber-500 transition-colors resize-none"
      />
    </div>
  );

  return (
    <div className="border-b border-stone-800">
      <button
        data-testid="toggle-telos-editor"
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-2.5 text-stone-400 hover:text-stone-100 transition-colors"
      >
        <span className="flex items-center gap-2 text-[11px] uppercase tracking-[0.18em]">
          <Pencil className="h-3 w-3" /> Teacher · edit assignment & purpose
        </span>
        <RotateCcw className={`h-3 w-3 transition-transform ${open ? "rotate-180" : ""}`} />
      </button>
      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25 }}
            className="overflow-hidden"
          >
            <div className="px-5 pb-4 space-y-3">
              {field("assignment", "Assignment")}
              {field("pedagogical_purpose", "Pedagogical Purpose")}
              {field("current_writing_task", "Current Writing Task")}
              <button
                data-testid="save-telos-button"
                onClick={() => onSave(form)}
                disabled={saving}
                className="inline-flex items-center gap-1.5 bg-amber-500 text-stone-900 px-3 py-1.5 rounded-sm text-[11px] uppercase tracking-[0.15em] font-medium hover:bg-amber-400 transition-colors disabled:opacity-40"
              >
                <Save className="h-3 w-3" />
                {saving ? "Saving…" : "Save telos"}
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default function DevelopmentPanel({
  open,
  onClose,
  session,
  onEditTelos,
  savingTelos,
}) {
  const theory = session?.theory || {};
  const telos = session?.telos || {};
  const interactions = session?.interactions || [];
  const last = interactions[interactions.length - 1];
  const processing = (session?.turns || []).some((t) => t.status === "processing");
  const profile = session?.developmental_profile || [];

  // Accordion open-state. Recomputed to defaults ONLY when a new completed turn
  // arrives (interactions.length changes) — never on every poll — so manual
  // open/close is preserved while viewing the same turn.
  const turnKey = interactions.length;
  const [openMap, setOpenMap] = useState(() => computeDefaults(theory));
  const [researchView, setResearchView] = useState(false);
  // teacher label by default; internal/research label when the toggle is on
  const t = (teacher, research) => (researchView ? research : teacher);

  useEffect(() => {
    setOpenMap(computeDefaults(theory));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [turnKey, session?.id]);

  const toggle = useCallback((id) => {
    setOpenMap((prev) => ({ ...prev, [id]: !prev[id] }));
  }, []);

  if (!session) return null;

  const statuses = frameworkStatuses(theory);
  const primaryFw = FRAMEWORKS.find((f) => statuses[f.id].status === "primary");
  const otherApplicable = FRAMEWORKS.filter((f) =>
    ["supporting", "applicable", "postponed"].includes(statuses[f.id].status)
  );
  const inactive = FRAMEWORKS.filter((f) => statuses[f.id].status === "not_applicable");

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            onClick={onClose}
            className="fixed inset-0 z-40 bg-stone-950/30"
          />
          <motion.aside
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            data-testid="development-panel"
            className="fixed right-0 top-0 z-50 h-full w-full max-w-md bg-stone-900 border-l border-stone-800 flex flex-col font-mono-panel"
          >
            <div className="flex items-center justify-between px-5 py-4 border-b border-stone-800 shrink-0">
              <div className="flex items-center gap-2 text-stone-200">
                {researchView ? (
                  <Terminal className="h-4 w-4 text-amber-500" />
                ) : (
                  <GraduationCap className="h-4 w-4 text-amber-500" />
                )}
                <span className="text-xs uppercase tracking-[0.2em]">
                  {t("Teaching Insight", "Developmental Guide Engine")}
                </span>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-1" title="Export this session for audit">
                  <Download className="h-3 w-3 text-stone-500" />
                  <a
                    href={`${API_BASE}/sessions/${session.id}/export?format=json`}
                    data-testid="export-session-json"
                    className="text-[9px] uppercase tracking-[0.14em] px-1.5 py-1 rounded-sm border border-stone-700 text-stone-400 hover:text-stone-100 hover:border-stone-500 transition-colors"
                  >
                    JSON
                  </a>
                  <a
                    href={`${API_BASE}/sessions/${session.id}/export?format=markdown`}
                    data-testid="export-session-md"
                    className="text-[9px] uppercase tracking-[0.14em] px-1.5 py-1 rounded-sm border border-stone-700 text-stone-400 hover:text-stone-100 hover:border-stone-500 transition-colors"
                  >
                    MD
                  </a>
                </div>
                <button
                  type="button"
                  data-testid="toggle-research-view"
                  onClick={() => setResearchView((v) => !v)}
                  aria-pressed={researchView}
                  className="inline-flex items-center gap-1.5 text-[9px] uppercase tracking-[0.14em] px-2 py-1 rounded-sm border border-stone-700 text-stone-400 hover:text-stone-100 hover:border-stone-500 transition-colors focus:outline-none focus-visible:ring-1 focus-visible:ring-amber-500"
                  title="Toggle teacher / research view"
                >
                  <Microscope className="h-3 w-3" />
                  {researchView ? "Research view" : "Teacher view"}
                </button>
                <button
                  onClick={onClose}
                  data-testid="close-dev-panel-button"
                  className="text-stone-500 hover:text-stone-200 transition-colors"
                  aria-label="Close development panel"
                >
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>

            <TelosEditor session={session} onSave={onEditTelos} saving={savingTelos} />

            <div className="px-5 py-2.5 border-b border-stone-800 shrink-0 flex items-center justify-between gap-2">
              <p className="text-[10px] text-stone-500 leading-relaxed">
                {researchView
                  ? "Provisional working theory of the developing system. Revised (not appended) each turn."
                  : "The coach's reasoning for this turn. Updates as the student writes and revises."}
                {session.theory_history?.length
                  ? ` v${session.theory_history.length + 1}`
                  : " v1"}
              </p>
              {processing ? (
                <span
                  data-testid="panel-processing-indicator"
                  className="shrink-0 inline-flex items-center gap-1 text-[9px] uppercase tracking-[0.12em] text-amber-300 border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 rounded-sm"
                >
                  <Loader2 className="h-3 w-3 animate-spin" />
                  Reasoning
                </span>
              ) : null}
            </div>

            <div className="flex-1 overflow-y-auto custom-scroll px-5 py-5">
              {/* Instructional Rationale — concise professional teacher summary */}
              {(theory.scaffolding_control?.primary_target || "").trim() ? (() => {
                const sc = theory.scaffolding_control || {};
                const ir = theory.instructional_reasoning || {};
                const sr = theory.structural_reasoning || {};
                const depActive =
                  (ir.required_dependency || "").trim() &&
                  ["identified", "being_taught"].includes((ir.dependency_status || "").trim().toLowerCase());
                const focus = depActive
                  ? `Developing ${ir.required_dependency} — the prerequisite for ${sc.primary_target}`
                  : sc.primary_target;
                const evidenceParts = [
                  ...(sr.elements_emerging || []),
                  ...(sr.elements_present || []),
                ].filter(Boolean).slice(0, 3);
                const suff = (ir.sufficiency_for_next_step || "").trim().toLowerCase();
                const judgment =
                  suff === "sufficient"
                    ? "Sufficiently developed to proceed."
                    : suff === "not_yet"
                    ? "Not yet sufficient to carry the next step."
                    : "";
                const judgmentWhy = ir.dependency_rationale || sr.hierarchical_triage_rationale || "";
                const decMap = {
                  shift_to_prerequisite: `Teach the prerequisite first, then return to the ${sc.primary_target}.`,
                  release: "The element is sufficient — advance to the next step.",
                  consolidate: "Consolidate this gain as a reusable principle.",
                  continue: `Continue developing the ${sc.primary_target}.`,
                };
                const decision = decMap[(ir.continue_consolidate_release_or_shift || "").trim()] || "";
                return (
                  <div
                    data-testid="instructional-rationale-block"
                    className="mb-5 rounded-md border border-stone-700 bg-stone-900/40 p-4"
                  >
                    <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.14em] text-stone-300 font-medium mb-3">
                      <ClipboardList className="h-3.5 w-3.5" />
                      Instructional Rationale
                    </div>
                    <div className="space-y-2.5">
                      <KV k="Instructional focus" accent="text-[#e8a87c]"><Text value={focus} /></KV>
                      {evidenceParts.length ? (
                        <KV k="Evidence in the writing"><List items={evidenceParts} /></KV>
                      ) : null}
                      {judgment ? (
                        <KV k="Developmental judgment">
                          <Text value={judgmentWhy ? `${judgment} ${judgmentWhy}` : judgment} />
                        </KV>
                      ) : null}
                      {decision ? (
                        <KV k="Instructional decision" accent="text-sky-300"><Text value={decision} /></KV>
                      ) : null}
                      {(sr.active_exit_criterion || "").trim() ? (
                        <KV k="Exit criterion" accent="text-emerald-300">
                          <Text value={sr.active_exit_criterion} />
                        </KV>
                      ) : null}
                      {(ir.next_developmental_step || "").trim() ? (
                        <KV k="Next developmental step"><Text value={ir.next_developmental_step} /></KV>
                      ) : null}
                    </div>
                  </div>
                );
              })() : null}


              {/* Where this fits — Unified Structural Reasoning (teacher-language) */}
              {theory.structural_reasoning?.applies !== false &&
              (theory.structural_reasoning?.structure_identified || "").trim() ? (
                <div
                  data-testid="structural-reasoning-block"
                  className="mb-5 rounded-md border border-l-2 border-stone-800 border-l-indigo-400 bg-indigo-400/[0.06] p-4"
                >
                  <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.14em] text-indigo-300 font-medium mb-3">
                    <Layers className="h-3.5 w-3.5" />
                    {t("Where this fits in the writing", "Structural Reasoning")}
                  </div>
                  <div className="space-y-2.5">
                    <KV k="What Compass is reading" accent="text-indigo-300">
                      <Text value={theory.structural_reasoning?.structure_identified} />
                    </KV>
                    {(theory.structural_reasoning?.elements_present || []).length ? (
                      <KV k="Already in place">
                        <List items={theory.structural_reasoning?.elements_present} />
                      </KV>
                    ) : null}
                    {(theory.structural_reasoning?.elements_emerging || []).length ? (
                      <KV k="Beginning to emerge" accent="text-emerald-300">
                        <List items={theory.structural_reasoning?.elements_emerging} />
                      </KV>
                    ) : null}
                    {(theory.structural_reasoning?.elements_absent || []).length ? (
                      <KV k="Not yet present" accent="text-amber-300">
                        <List items={theory.structural_reasoning?.elements_absent} />
                      </KV>
                    ) : null}
                    {(theory.structural_reasoning?.element_relationships || []).length ? (
                      <KV k="How the parts relate">
                        <List items={theory.structural_reasoning?.element_relationships} />
                      </KV>
                    ) : null}
                    <KV k="Why start here" accent="text-sky-300">
                      <Text value={theory.structural_reasoning?.hierarchical_triage_rationale} />
                    </KV>
                    {(theory.structural_reasoning?.active_exit_criterion || "").trim() ? (
                      <KV k="Ready to move on when" accent="text-emerald-300">
                        <Text value={theory.structural_reasoning?.active_exit_criterion} />
                        {(theory.instructional_reasoning?.sufficiency_for_next_step || "")
                          .trim()
                          .toLowerCase() === "sufficient" ? (
                          <span className="ml-2 text-[10px] uppercase tracking-[0.12em] text-emerald-400 font-mono-panel">
                            ✓ achieved — moving on
                          </span>
                        ) : null}
                      </KV>
                    ) : null}
                  </div>
                </div>
              ) : null}

              {/* Dependency-First Instruction — teacher-language, shown only when a dependency is active */}
              {["identified", "being_taught", "addressed"].includes(
                (theory.instructional_reasoning?.dependency_status || "").trim().toLowerCase()
              ) && (theory.instructional_reasoning?.required_dependency || "").trim() ? (
                <div
                  data-testid="dependency-first-block"
                  className="mb-5 rounded-md border border-l-2 border-stone-800 border-l-amber-500 bg-amber-500/[0.06] p-4"
                >
                  <div className="flex items-center gap-1.5 text-[10px] uppercase tracking-[0.14em] text-amber-300 font-medium mb-3">
                    <GitBranch className="h-3.5 w-3.5" />
                    {t("Dependency-First Instruction", "Dependency-First Instruction (W-E)")}
                  </div>
                  <div className="space-y-2.5">
                    <KV k="Current instructional focus" accent="text-amber-300">
                      <Text value={theory.instructional_reasoning?.active_instructional_element} />
                    </KV>
                    <KV k="Dependency currently being developed" accent="text-sky-300">
                      <Text value={theory.instructional_reasoning?.required_dependency} />
                    </KV>
                    <KV k="Why this comes first">
                      <Text value={theory.instructional_reasoning?.dependency_rationale} />
                    </KV>
                  </div>
                </div>
              ) : null}

              {/* 0 — Governed Canonical Instruction (Instructional-Object layer) */}
              {theory.instructional_reasoning?.applies !== false ? (
                <Accordion
                  id="instructional_reasoning"
                  title={t("Instructional Reasoning", "Instructional Reasoning (Instructional Objects)")}
                  accent="border-l-2 border-l-emerald-500"
                  open={openMap.instructional_reasoning}
                  onToggle={() => toggle("instructional_reasoning")}
                >
                  <div className="space-y-1.5" data-testid="instructional-reasoning-block">
                    <KV k="Current unit of writing" accent="text-emerald-300">
                      <Text value={theory.instructional_reasoning?.current_unit_of_writing} />
                    </KV>
                    <KV k="Active writing element" accent="text-amber-300">
                      <Text value={theory.instructional_reasoning?.active_instructional_element} />
                    </KV>
                    <KV k="What that element does">
                      <Text value={theory.instructional_reasoning?.element_communicative_purpose} />
                    </KV>
                    <KV k="Student's current organization">
                      <Text value={theory.instructional_reasoning?.student_current_organization} />
                    </KV>
                    <KV k="How this element is built">
                      <Text value={theory.instructional_reasoning?.canonical_performance_structure} />
                    </KV>
                    <KV k="Primary developmental tension" accent="text-amber-300">
                      <Text value={theory.instructional_reasoning?.primary_developmental_tension} />
                    </KV>
                    <KV k="Next student act" accent="text-sky-300">
                      <Text value={theory.instructional_reasoning?.next_student_act} />
                    </KV>
                    <KV k="Selected teaching resources">
                      <List items={theory.instructional_reasoning?.selected_developmental_resources} />
                    </KV>
                    <KV k="Why these resources">
                      <Text value={theory.instructional_reasoning?.resource_selection_rationale} />
                    </KV>
                    <KV k="Evidence of movement">
                      <Text value={theory.instructional_reasoning?.evidence_of_developmental_movement} />
                    </KV>
                    <KV k="Degree of student control" accent="text-emerald-300">
                      <Text value={theory.instructional_reasoning?.degree_of_student_control} />
                    </KV>
                    <KV k="Continue / consolidate / release / shift" accent="text-sky-300">
                      <Text value={theory.instructional_reasoning?.continue_consolidate_release_or_shift} />
                    </KV>
                  </div>
                </Accordion>
              ) : null}

              {/* Developmental Memory — accumulated student control across episodes */}
              <Accordion
                id="developmental_memory"
                title={t("Developmental Memory", "Developmental Memory (profile)")}
                accent="border-l-2 border-l-purple-500"
                open={openMap.developmental_memory}
                onToggle={() => toggle("developmental_memory")}
              >
                <div className="space-y-2" data-testid="developmental-memory-block">
                  <p className="text-[10px] text-stone-500 leading-relaxed">
                    What the student can do over time (not chat history). Future turns scaffold from here.
                  </p>
                  {profile.length === 0 ? (
                    <span className="text-stone-600 text-[13px]">
                      No developmental evidence yet — builds as the student writes.
                    </span>
                  ) : (
                    <ul className="space-y-1.5">
                      {profile.map((o, i) => (
                        <li
                          key={i}
                          data-testid={`dev-memory-item-${i}`}
                          className="border border-stone-800 rounded-sm px-2.5 py-2 bg-stone-950/40"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="text-amber-300 text-[12px]">{o.element}</span>
                            <span className="text-[9px] uppercase tracking-[0.12em] text-emerald-300 border border-emerald-500/40 bg-emerald-500/10 px-1.5 py-0.5 rounded-sm">
                              {o.trend}{o.episodes > 1 ? ` · ${o.episodes}` : ""}
                            </span>
                          </div>
                          <div className="text-stone-300 text-[12px] mt-1">{o.control_statement}</div>
                          {o.evidence ? (
                            <div className="text-stone-500 text-[11px] mt-0.5">basis: {o.evidence}</div>
                          ) : null}
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </Accordion>

              {/* 1 — Scaffolding Controller (the one decision that matters) */}
              <Accordion
                id="scaffolding_control"
                title={t("Current Developmental Focus", "Scaffolding Controller (M11)")}
                accent="border-l-2 border-l-amber-500"
                open={openMap.scaffolding_control}
                onToggle={() => toggle("scaffolding_control")}
              >
                <div className="space-y-1.5" data-testid="scaffolding-control-block">
                  <KV k={t("What we're looking at", "unit")}>
                    <Text value={theory.scaffolding_control?.current_unit} />
                  </KV>
                  <KV k={t("Opportunities noticed", "diagnosed opportunities")}>
                    <List
                      items={
                        researchView
                          ? theory.scaffolding_control?.diagnosed_opportunities
                          : (theory.scaffolding_control?.diagnosed_opportunities || []).map(humanizeFramework)
                      }
                    />
                  </KV>
                  <KV k={t("Focus this turn", "primary target")} accent="text-amber-300">
                    <Text
                      value={
                        researchView
                          ? theory.scaffolding_control?.primary_target
                          : humanizeFramework(theory.scaffolding_control?.primary_target)
                      }
                    />
                  </KV>
                  <KV k={t("Why this focus?", "why (priority)")}>
                    <Text value={theory.scaffolding_control?.prioritization_rationale} />
                  </KV>
                  <KV k={t("How the coach is helping", "mode")} accent="text-emerald-300">
                    <Text value={theory.scaffolding_control?.instructional_mode} />
                  </KV>
                  <KV k={t("Postponed opportunities", "postponed")}>
                    <List
                      items={
                        researchView
                          ? theory.scaffolding_control?.postponed
                          : (theory.scaffolding_control?.postponed || []).map(humanizeFramework)
                      }
                    />
                  </KV>
                  <KV k={t("Where the coaching stands", "cycle status")} accent="text-sky-300">
                    <Text value={theory.scaffolding_control?.cycle_status} />
                  </KV>
                  {theory.scaffolding_control?.stopping_reason ? (
                    <KV k={t("Why the coach paused", "stopping reason")}>
                      <Text value={theory.scaffolding_control?.stopping_reason} />
                    </KV>
                  ) : null}
                  {theory.scaffolding_control?.future_opportunity ? (
                    <KV k={t("For a later session", "future opportunity")}>
                      <Text value={theory.scaffolding_control?.future_opportunity} />
                    </KV>
                  ) : null}
                </div>
              </Accordion>

              {/* 2 — Integration & Calibration */}
              {theory.integration_calibration?.applies ? (
                <Accordion
                  id="integration_calibration"
                  title={t("Why This Focus", "Integration & Calibration (M14)")}
                  accent="border-l-2 border-l-sky-500"
                  open={openMap.integration_calibration}
                  onToggle={() => toggle("integration_calibration")}
                >
                  <div className="space-y-1.5" data-testid="integration-calibration-block">
                    <KV k={t("Main lens", "primary framework")} accent="text-amber-300">
                      <Text
                        value={
                          researchView
                            ? theory.integration_calibration?.primary_framework
                            : humanizeFramework(theory.integration_calibration?.primary_framework)
                        }
                      />
                    </KV>
                    <KV k={t("Also considered", "supporting frameworks")}>
                      <List
                        items={
                          researchView
                            ? theory.integration_calibration?.supporting_frameworks
                            : (theory.integration_calibration?.supporting_frameworks || []).map(humanizeFramework)
                        }
                      />
                    </KV>
                    <KV k={t("Is this the right amount?", "calibration check")}>
                      <Text value={theory.integration_calibration?.calibration_check} />
                    </KV>
                    <KV k={t("Would apply the same elsewhere?", "consistency check")}>
                      <Text value={theory.integration_calibration?.consistency_check} />
                    </KV>
                    <KV k={t("How it fits together", "integration notes")}>
                      <Text value={theory.integration_calibration?.integration_notes} />
                    </KV>
                  </div>
                </Accordion>
              ) : null}

              {/* 3 — Primary Active Framework */}
              {primaryFw ? (
                <>
                  <GroupHeader>{t("Current Focus Area", "Primary Active Framework")}</GroupHeader>
                  <Accordion
                    id={primaryFw.id}
                    title={researchView ? primaryFw.label : FW_TEACHER[primaryFw.id]}
                    badge={<Badge status="primary" research={researchView} />}
                    open={openMap[primaryFw.id]}
                    onToggle={() => toggle(primaryFw.id)}
                  >
                    {primaryFw.content(theory)}
                  </Accordion>
                </>
              ) : null}

              {/* 4 — Other Applicable Frameworks */}
              {otherApplicable.length > 0 ? (
                <>
                  <GroupHeader>{t("Also In View", "Other Applicable Frameworks")}</GroupHeader>
                  {otherApplicable.map((fw) => (
                    <Accordion
                      key={fw.id}
                      id={fw.id}
                      title={researchView ? fw.label : FW_TEACHER[fw.id]}
                      badge={<Badge status={statuses[fw.id].status} research={researchView} />}
                      open={openMap[fw.id]}
                      onToggle={() => toggle(fw.id)}
                    >
                      {fw.content(theory)}
                    </Accordion>
                  ))}
                </>
              ) : null}

              {/* 5 — Inactive Frameworks */}
              {inactive.length > 0 ? (
                <>
                  <GroupHeader>{t("Not Relevant Right Now", "Inactive Frameworks")}</GroupHeader>
                  {inactive.map((fw) => (
                    <Accordion
                      key={fw.id}
                      id={fw.id}
                      title={researchView ? fw.label : FW_TEACHER[fw.id]}
                      badge={<Badge status="not_applicable" research={researchView} />}
                      open={openMap[fw.id]}
                      onToggle={() => toggle(fw.id)}
                    >
                      {fw.content(theory)}
                    </Accordion>
                  ))}
                </>
              ) : null}

              {/* 6 — Intervention / Instructional Output */}
              <GroupHeader>{t("What the Coach Said", "Instructional Output")}</GroupHeader>
              <Accordion
                id="intervention"
                title={t("The Invitation & Coaching Move", "Intervention & Selected Invitation")}
                open={openMap.intervention}
                onToggle={() => toggle("intervention")}
              >
                <div className="space-y-3">
                  <div>
                    <SectionLabel>{t("The invitation this turn", "Selected Invitation")}</SectionLabel>
                    <div className="text-amber-200" data-testid="selected-invitation">
                      <Text value={last?.selected_invitation?.invitation} />
                    </div>
                  </div>
                  <div className="space-y-1.5" data-testid="intervention-block">
                    <KV k={t("Kind of move", "type")} accent="text-amber-300">
                      <Text value={last?.intervention?.type} />
                    </KV>
                    <KV k={t("Concept in play", "cultural resource")}>
                      <Text value={last?.intervention?.cultural_resource} />
                    </KV>
                    <KV k={t("What the coach noticed", "interpretation")}>
                      <Text value={last?.intervention?.interpretation} />
                    </KV>
                    <KV k={t("What the coach taught", "instruction")}>
                      <Text value={last?.intervention?.instruction} />
                    </KV>
                    <KV k={t("What was reinforced", "consolidation")}>
                      <Text value={last?.intervention?.consolidation} />
                    </KV>
                    <KV k={t("Why now", "timing")}>
                      <Text value={last?.intervention?.timing_rationale} />
                    </KV>
                    <KV
                      k={t("Writing vs. content", "focus")}
                      accent={last?.intervention?.focus === "content" ? "text-orange-300" : "text-emerald-300"}
                    >
                      <Text value={last?.intervention?.focus} />
                    </KV>
                    <KV k={t("Ownership check", "writing-not-content check")}>
                      <Text value={last?.intervention?.writing_not_content_check} />
                    </KV>
                  </div>
                  <div>
                    <SectionLabel>{t("Why this invitation", "Rationale (coherence, not optimality)")}</SectionLabel>
                    <div className="text-stone-300">
                      <Text value={last?.selected_invitation?.selection_basis} />
                    </div>
                  </div>
                </div>
              </Accordion>

              {/* Full engine internals — research/developer view only */}
              {researchView ? (
                <>
                  <GroupHeader>Working Theory Detail</GroupHeader>
                  <Accordion
                    id="detail"
                    title="Full engine internals"
                    open={openMap.detail}
                    onToggle={() => toggle("detail")}
                  >
                <Block label="Current Telos">
                  <Text value={theory.current_telos || telos.governing_pedagogical_purpose} />
                </Block>
                <Block label="Current Organization (relative to telos)">
                  <Text value={theory.current_organization} />
                </Block>
                <Block label="Observed Developmental Movement">
                  <div className="space-y-2">
                    <KV k="differentiation">
                      <List items={theory.observed_differentiations} />
                    </KV>
                    <KV k="integration">
                      <List items={theory.observed_integrations} />
                    </KV>
                    <KV k="coordination">
                      <List items={theory.observed_coordinations} />
                    </KV>
                    <KV k="intentional control">
                      <Text value={theory.emerging_intentional_control} />
                    </KV>
                  </div>
                </Block>
                <Block label="Currently Relevant Canonical Domains">
                  <List items={theory.currently_relevant_domains} />
                </Block>
                <Block label="Active Tension(s)">
                  <span className="text-amber-300">
                    <List items={theory.unresolved_tensions} />
                  </span>
                </Block>
                <Block label="Cultural Resources (in use / potential)">
                  <div className="space-y-1.5">
                    <KV k="in use">
                      <List items={theory.cultural_resources_in_use} />
                    </KV>
                    <KV k="potential">
                      <List items={theory.potential_cultural_resources} />
                    </KV>
                  </div>
                </Block>
                <Block label="Evidence — Supporting">
                  <List items={theory.supporting_evidence} />
                </Block>
                <Block label="Evidence — Complicating / Contradicting">
                  <List items={theory.complicating_evidence} />
                </Block>
                <Block label="Alternative Interpretations (preserved)">
                  <List items={theory.alternative_interpretations} />
                </Block>
                <Block label="Current Uncertainty">
                  <List items={theory.current_uncertainty} />
                </Block>
                <Block label="Possible Reorganizations">
                  <List items={theory.possible_reorganizations} />
                </Block>
                <Block label="Candidate Invitations (internal)">
                  {last?.candidate_invitations?.length ? (
                    <div className="space-y-3">
                      {last.candidate_invitations.map((c, i) => (
                        <div
                          key={i}
                          data-testid={`candidate-invitation-${i}`}
                          className="border border-stone-800 rounded-sm p-2.5 bg-stone-950/50"
                        >
                          <div className="text-stone-200">
                            {i + 1}. {c.invitation}
                          </div>
                          <div className="text-[11px] text-stone-500 mt-1">
                            addresses: {c.developmental_possibility || "—"}
                          </div>
                          <div className="text-[11px] text-stone-500">
                            could learn: {c.what_ai_could_learn || "—"}
                          </div>
                          <div className="text-[11px] text-stone-500">
                            risk: {c.uncertainty_or_risk || "—"}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <span className="text-stone-600">—</span>
                  )}
                </Block>
                <Block label="Change From Previous Interaction">
                  <Text value={theory.changes_since_previous} />
                </Block>
                <Block label="Observed Reorganization (this turn)">
                  <Text value={last?.observed_reorganization} />
                </Block>
              </Accordion>
                </>
              ) : null}
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}
