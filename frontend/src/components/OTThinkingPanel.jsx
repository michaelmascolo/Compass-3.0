import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";

// Persistent OT thinking area — keeps the Original Assignment and the active OT
// object readily visible; every other object is COLLAPSED by default (title +
// short status + a one-line preview) and expands on demand without navigating.
// Presentation only; reads already-persisted OT state. Uses the exact
// student-visible labels. Never shows JSON, status codes, canonical ids,
// sufficiency internals, or AI reasoning.
const ITEMS = [
  ["the_assignment", "The Assignment"],
  ["questions", "Questions I Need to Answer"],
  ["my_ideas", "My Ideas"],
  ["my_current_answer", "My Current Answer"],
  ["my_plan", "My Plan"],
];

function statusLabel(ot, key, flagged) {
  if (flagged) return "Needs review";
  const s = ot.status && ot.status[key];
  const has = (ot.objects || {})[key] && (ot.objects || {})[key].trim();
  if (s === "sufficient") return "Ready";
  if (has) return "In progress";
  return "Not started";
}

function preview(text) {
  const t = (text || "").trim().replace(/\s+/g, " ");
  if (!t) return "";
  return t.length > 70 ? t.slice(0, 70) + "…" : t;
}

export default function OTThinkingPanel({ ot, active, onRevisit, only, title = "Your thinking so far" }) {
  const [open, setOpen] = useState({});
  if (!ot) return null;
  const objects = ot.objects || {};
  const review = ot.needs_review || [];
  let rows = [
    { key: "__original", label: "Original Assignment", content: ot.seed_assignment || "", original: true },
    ...ITEMS.map(([key, label]) => ({ key, label, content: objects[key] || "", flagged: review.includes(key) })),
  ];
  if (only) rows = rows.filter((r) => only.includes(r.key));

  return (
    <aside
      data-testid="ot-thinking-panel"
      className="lg:sticky lg:top-6 self-start bg-stone-50/70 border border-stone-200 rounded-md p-4 space-y-2"
    >
      <p className="font-mono-panel text-[10px] uppercase tracking-[0.18em] text-stone-400">{title}</p>
      {rows.map((r) => {
        const isActive = r.key === active;
        const has = r.content && r.content.trim();
        // Always-expanded: the Original Assignment and the active object.
        // Everything else is collapsed unless the student opens it.
        const forcedOpen = r.original || isActive;
        const isOpen = forcedOpen || !!open[r.key];
        const label = r.original ? null : statusLabel(ot, r.key, r.flagged);
        return (
          <div
            key={r.key}
            data-testid={r.original ? "ot-panel-original" : `ot-panel-item-${r.key}`}
            className={`rounded-sm border ${isActive ? "border-[#8C3A2A] bg-white" : "border-stone-200 bg-white/70"}`}
          >
            <div className="flex items-center justify-between gap-2 px-3 pt-2.5 pb-1.5">
              <button
                type="button"
                onClick={() => !forcedOpen && setOpen((o) => ({ ...o, [r.key]: !o[r.key] }))}
                disabled={forcedOpen}
                data-testid={r.original ? undefined : `ot-panel-toggle-${r.key}`}
                aria-expanded={isOpen}
                className="flex items-center gap-1.5 min-w-0 text-left disabled:cursor-default"
              >
                {!forcedOpen &&
                  (isOpen ? (
                    <ChevronDown className="h-3.5 w-3.5 shrink-0 text-stone-400" />
                  ) : (
                    <ChevronRight className="h-3.5 w-3.5 shrink-0 text-stone-400" />
                  ))}
                <span className="font-mono-panel text-[10px] uppercase tracking-[0.14em] text-stone-500 truncate">
                  {r.label}
                  {r.original && <span className="text-stone-300"> · read-only</span>}
                </span>
              </button>
              <div className="flex items-center gap-2 shrink-0">
                {label && (
                  <span
                    data-testid={`ot-panel-status-${r.key}`}
                    className={`font-mono-panel text-[9px] uppercase tracking-[0.1em] ${
                      r.flagged ? "text-amber-700" : "text-stone-400"
                    }`}
                  >
                    {label}
                  </span>
                )}
                {onRevisit && !r.original && (has || isActive) && (
                  <button
                    onClick={() => onRevisit(r.key)}
                    data-testid={`ot-panel-revisit-${r.key}`}
                    className="text-[10px] font-mono-panel uppercase tracking-[0.12em] text-[#8C3A2A] hover:underline"
                  >
                    {isActive ? "Editing" : "Revisit"}
                  </button>
                )}
              </div>
            </div>
            {isOpen ? (
              <div className="px-3 pb-3">
                {has ? (
                  <p className="text-[13px] leading-relaxed text-stone-800 whitespace-pre-wrap max-h-32 overflow-y-auto font-serif-display">
                    {r.content}
                  </p>
                ) : (
                  <p className="text-[13px] italic text-stone-400">Not started yet</p>
                )}
              </div>
            ) : (
              has && (
                <p
                  data-testid={`ot-panel-preview-${r.key}`}
                  className="px-3 pb-2.5 text-[12px] leading-snug text-stone-400 truncate font-serif-display"
                >
                  {preview(r.content)}
                </p>
              )
            )}
          </div>
        );
      })}
    </aside>
  );
}
