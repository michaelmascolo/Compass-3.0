import { useEffect, useState } from "react";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Sprint 1 — read-only diagnostic trace for AUTHORIZED teacher/admin use.
// Not a numeric score; not shown to the student in this sprint. Deliberately minimal.
export default function DiagnosticTrace() {
  const params = new URLSearchParams(window.location.search);
  const stateId = params.get("trace");
  const role = params.get("role") || "teacher";
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let alive = true;
    (async () => {
      try {
        const res = await fetch(
          `${API}/instructional-state/${stateId}/trace?viewer_role=${encodeURIComponent(role)}`
        );
        const body = await res.json().catch(() => null);
        if (!alive) return;
        if (!res.ok) {
          setError(res.status === 403 ? "Restricted to teacher/admin." : "Unable to load trace.");
        } else {
          setData(body);
        }
      } catch {
        if (alive) setError("Unable to load trace.");
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => {
      alive = false;
    };
  }, [stateId, role]);

  const Row = ({ label, children, testid }) => (
    <div className="dt-row" data-testid={testid} style={styles.row}>
      <div style={styles.label}>{label}</div>
      <div style={styles.value}>{children}</div>
    </div>
  );

  const List = ({ items, empty }) =>
    items && items.length ? (
      <ul style={styles.ul}>
        {items.map((x, i) => (
          <li key={i} style={styles.li}>
            {typeof x === "string" ? x : JSON.stringify(x)}
          </li>
        ))}
      </ul>
    ) : (
      <span style={styles.muted}>{empty || "—"}</span>
    );

  if (!stateId) return <div style={styles.wrap} data-testid="trace-missing-id">Provide ?trace=&lt;state_id&gt;.</div>;
  if (loading) return <div style={styles.wrap} data-testid="trace-loading">Loading diagnostic trace…</div>;
  if (error) return <div style={styles.wrap} data-testid="trace-error">{error}</div>;

  return (
    <div style={styles.wrap} data-testid="diagnostic-trace">
      <div style={styles.header}>
        <span style={styles.kicker}>Compass · Diagnostic Trace</span>
        <span style={styles.badge} data-testid="trace-authorized-badge">teacher / admin · read-only</span>
      </div>
      <p style={styles.note}>
        This is an interpretive trace, not a score. Observations, interpretations, and unknowns are kept
        strictly separate.
      </p>

      {data.diagnostic_notice ? (
        <div style={styles.notice} data-testid="trace-diagnostic-notice">{data.diagnostic_notice}</div>
      ) : null}

      <Row label="Current target" testid="trace-current-target">
        {data.current_target || <span style={styles.muted}>none selected</span>}
      </Row>
      <Row label="Observed strength" testid="trace-observed-strength">
        <List items={data.observed_strength} empty="none observed yet" />
      </Row>
      <Row label="Evidence used (OBSERVED)" testid="trace-evidence-used">
        <List items={data.evidence_used} empty="none" />
      </Row>
      <Row label="Provisional interpretation (HYPOTHESIZED)" testid="trace-interpretation">
        <List items={data.provisional_interpretation} empty="none" />
      </Row>
      <Row label="Uncertainty (UNKNOWN)" testid="trace-uncertainty">
        <List items={data.uncertainty} empty="none flagged" />
      </Row>
      <Row label="Current support level" testid="trace-support-level">{data.current_support_level}</Row>
      <Row label="Exit criterion status" testid="trace-exit-status">{data.exit_criterion_status}</Row>
      <Row label="Most recent advancement decision" testid="trace-advancement">
        {data.most_recent_advancement_decision}
      </Row>
      <Row label="Teacher overrides" testid="trace-overrides">
        <List
          items={(data.teacher_overrides || []).map(
            (o) => `${o.field}: ${JSON.stringify(o.from_value)} → ${JSON.stringify(o.to_value)}${o.reason ? ` (${o.reason})` : ""}`
          )}
          empty="none"
        />
      </Row>
      <Row label="Applicable requirement IDs" testid="trace-requirement-ids">
        <List items={data.applicable_requirement_ids} empty="none" />
      </Row>

      <div style={styles.sectionHead} data-testid="trace-decision-section">Instructional Decision (Sprint 3)</div>
      <Row label="Decision status" testid="trace-decision-status">
        {data.decision_status || <span style={styles.muted}>—</span>}
        {data.instructional_need ? <span style={styles.badge}> · {data.instructional_need}</span> : null}
        {data.decision_confidence ? <span style={styles.badge}> · confidence {data.decision_confidence}</span> : null}
      </Row>
      <Row label="Coaching path (RP4)" testid="trace-coaching-path">
        {data.coaching_path ? (
          <span><strong>{data.coaching_path}</strong>
          {data.dialogue_consistent_with_decision === false ? <span style={styles.badge}> · INCONSISTENT</span> : null}</span>
        ) : (<span style={styles.muted}>no coaching turn yet</span>)}
      </Row>
      <Row label="Demonstrated strength" testid="trace-demonstrated-strength">
        <List items={data.demonstrated_strength} empty={`none (${data.strength_status || "UNKNOWN"})`} />
      </Row>
      <Row label="Candidate targets" testid="trace-candidate-targets">
        <List items={data.candidate_targets} empty="none" />
      </Row>
      <Row label="Selected target" testid="trace-selected-target">
        {data.selected_target ? (
          <span><strong>{data.selected_target}</strong>{data.selected_object_definition ? <span style={styles.muted}> — {data.selected_object_definition}</span> : null}</span>
        ) : (
          <span style={styles.muted}>no active target</span>
        )}
      </Row>
      <Row label="Observed evidence (selection)" testid="trace-selection-evidence">
        <List items={data.observed_selection_evidence} empty="none" />
      </Row>
      <Row label="Prerequisite status" testid="trace-prereq-status">
        structural: {data.structural_prerequisite_status} · conceptual: {data.conceptual_prerequisite_status}
      </Row>
      <Row label="Priority rationale" testid="trace-priority-rationale">
        {data.priority_rationale || <span style={styles.muted}>—</span>}
      </Row>
      <Row label="Deferred targets" testid="trace-deferred-targets">
        <List items={data.deferred_targets} empty="none" />
      </Row>
      <Row label="Uncertainty (decision)" testid="trace-decision-uncertainty">
        <List items={data.decision_uncertainty} empty="none" />
      </Row>
      {data.engine_recommendation ? (
        <Row label="Engine recommendation (pre-override)" testid="trace-engine-recommendation">
          {data.engine_recommendation}
        </Row>
      ) : null}
      <Row label="Decision requirement IDs" testid="trace-decision-req-ids">
        <List items={data.decision_requirement_ids} empty="none" />
      </Row>
      <div style={styles.footer} data-testid="trace-version">
        state version {data.version}{data.decision_timestamp ? ` · decided ${data.decision_timestamp}` : ""}
      </div>
    </div>
  );
}

const styles = {
  wrap: { maxWidth: 720, margin: "40px auto", padding: 24, fontFamily: "Georgia, 'Times New Roman', serif", color: "#1d1a17", background: "#fbf9f5", border: "1px solid #e6e0d4", borderRadius: 10 },
  header: { display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 6 },
  kicker: { fontSize: 18, fontWeight: 700, letterSpacing: "0.01em" },
  badge: { fontSize: 11, fontFamily: "ui-monospace, monospace", color: "#6b5f4b", background: "#efe9dd", padding: "3px 8px", borderRadius: 999 },
  note: { fontSize: 13, color: "#6b5f4b", marginTop: 0, marginBottom: 18 },
  sectionHead: { marginTop: 26, marginBottom: 4, fontSize: 13, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "#8a5a2b", borderTop: "2px solid #e0c9a6", paddingTop: 12 },
  notice: { fontSize: 13, color: "#7a2e12", background: "#fdeee6", border: "1px solid #f0c9b6", padding: "10px 12px", borderRadius: 8, marginBottom: 16 },
  row: { display: "grid", gridTemplateColumns: "230px 1fr", gap: 16, padding: "10px 0", borderTop: "1px solid #ece5d8" },
  label: { fontSize: 12, textTransform: "uppercase", letterSpacing: "0.06em", color: "#8a7d67", paddingTop: 2 },
  value: { fontSize: 15, lineHeight: 1.5 },
  ul: { margin: 0, paddingLeft: 18 },
  li: { marginBottom: 3 },
  muted: { color: "#a99e88", fontStyle: "italic" },
  footer: { marginTop: 16, fontSize: 11, fontFamily: "ui-monospace, monospace", color: "#a99e88", textAlign: "right" },
};
