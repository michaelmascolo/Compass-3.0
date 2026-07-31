# Phase II — CIO #5: PARAGRAPH UNITY (Paragraph Main Point) — calibrated + verified
Additive calibration. Architecture / Decision flow / Instructional Decision layer / One Thing Rule /
DB / audit / UI unchanged.

## What changed (additive, KEPT)
- `MINIMAL_OBJECTS["Paragraph Main Point"]`: essence reframed to "does the paragraph develop ONE
  controlling idea"; indicators separate present / drift-or-poorly-coordinated (partial) / no-controlling
  idea (missing) / competing-or-unrelated-topic (misleading). Variations expanded to eight: no controlling
  idea, multiple competing ideas, drift, tangential/unrelated, two-ideas-to-split, needed-info-omitted,
  poorly-coordinated support, one clear well-developed idea. Teaching strategy: name the controlling idea,
  test each sentence against it, decide keep/cut/move/split — never reorganize or rewrite for the writer.
- `_SEL_SYS`: Paragraph Unity is the focus only when a controlling idea/claim EXISTS but sentences do not
  cohere around it (drift/tangent/competing topic/poor coordination) and that coherence is higher leverage
  than evidence/explanation/definition; never when no claim exists yet (that is Central Claim).

## Verification (clear claim + support present, but unity broken; + regression anchors)
| Sample | Selected | Verdict |
|---|---|---|
| U1 drift ("my favorite subject is art…") | Paragraph Main Point (competing/drift) | ✓ |
| U2 unrelated topic ("cafeteria food…") | Paragraph Main Point (competing/drift) | ✓ |
| U3 two ideas to split (recycling + solar grid) | Paragraph Main Point (two separate claims) | ✓ |
| U4 tangential ("I love biking with family…") | Paragraph Main Point (shift/tangent) | ✓ |
| REG no claim | Central Claim | ✓ One Thing Rule |
| REG explanation | Explanation | ✓ |
| REG evidence (E1) | Evidence (3/4) / Central Claim (1/4) | ✓ modal Evidence; the flip is documented borderline noise |

## The 10 required distinctions
Object encodes: clear controlling idea, multiple competing ideas, sentences that drift, relevant vs
tangential, unrelated topic introduced, ideas that should be separated, omitted developing info, support
present but poorly coordinated, organization weakening unity, and not-highest-leverage (deferred via One
Thing Rule). U1–U4 exercised drift / unrelated / split / tangential; variations named the exact sub-type.

## Ownership (verified)
Dialogue scaffolds recognition, never reorganizes: U2 -> "finish: 'This paragraph is about ___'";
U3 -> "state your one point — does your second sentence actually help answer that?" Writer evaluates
and decides keep/cut/split; Compass never rewrites. action=ask_question.

## Stability note
E1 oscillates Evidence(3)/Central Claim(1) across identical runs — a pre-existing borderline perturbation
(claim is solid-but-sharpenable), NOT caused by this change. Modal behavior = Evidence, matching baseline.

## Backward compatibility
Content-only edits (Paragraph Main Point object + selector guidance). No DB/audit/flow/UI change.
CIO#1–#4 baselines hold at modal level; consolidated_v2 default path healthy.
