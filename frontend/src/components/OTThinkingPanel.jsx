// Persistent OT thinking area — keeps the Original Assignment and every OT object
// visible so the student never has to rely on memory. Presentation only; reads
// already-persisted OT state. Uses the exact student-visible labels. Never shows
// JSON, status codes, canonical ids, sufficiency, or AI reasoning.
const ITEMS = [
  ["the_assignment", "The Assignment"],
  ["questions", "Questions I Need to Answer"],
  ["my_ideas", "My Ideas"],
  ["my_current_answer", "My Current Answer"],
  ["my_plan", "My Plan"],
];

export default function OTThinkingPanel({ ot, active, onRevisit, only, title = "Your thinking so far" }) {
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
      className="lg:sticky lg:top-6 self-start bg-stone-50/70 border border-stone-200 rounded-md p-4 space-y-2.5"
    >
      <p className="font-mono-panel text-[10px] uppercase tracking-[0.18em] text-stone-400">{title}</p>
      {rows.map((r) => {
        const isActive = r.key === active;
        const has = r.content && r.content.trim();
        return (
          <div
            key={r.key}
            data-testid={r.original ? "ot-panel-original" : `ot-panel-item-${r.key}`}
            className={`rounded-sm border p-3 ${isActive ? "border-[#8C3A2A] bg-white" : "border-stone-200 bg-white/70"}`}
          >
            <div className="flex items-center justify-between gap-2">
              <span className="font-mono-panel text-[10px] uppercase tracking-[0.14em] text-stone-500">
                {r.label}
                {r.original && <span className="text-stone-300"> · read-only</span>}
              </span>
              {onRevisit && !r.original && (has || isActive) && (
                <button
                  onClick={() => onRevisit(r.key)}
                  data-testid={`ot-panel-revisit-${r.key}`}
                  className="shrink-0 text-[10px] font-mono-panel uppercase tracking-[0.12em] text-[#8C3A2A] hover:underline"
                >
                  {isActive ? "Editing" : "Revisit"}
                </button>
              )}
            </div>
            {r.flagged && (
              <span
                data-testid={`ot-panel-flag-${r.key}`}
                className="mt-1 inline-block text-[10px] font-mono-panel uppercase tracking-[0.1em] text-amber-700"
              >
                Needs review · updated since this was developed
              </span>
            )}
            {has ? (
              <p className="mt-1.5 text-[13px] leading-relaxed text-stone-800 whitespace-pre-wrap max-h-32 overflow-y-auto font-serif-display">
                {r.content}
              </p>
            ) : (
              <p className="mt-1.5 text-[13px] italic text-stone-400">Not started yet</p>
            )}
          </div>
        );
      })}
    </aside>
  );
}
