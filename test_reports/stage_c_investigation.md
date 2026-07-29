# Stage C Latency Investigation

Question: why does Stage C take ~16.7 s when it should be a fast render?

## Method
Added fine-grained timers inside `_render_coaching` (server.py): `t_gen1` (first LLM
call), `t_validate` (deterministic validator), `t_gen2` (regeneration call, if any),
`calls`. Ran 3 representative live preview turns.

## Measured results

| Turn | calls | gen1 | validate | gen2 | Stage C total | regenerated |
|------|-------|------|----------|------|---------------|-------------|
| 0 | 1 | 10.22 s | 0.000 s | — | **10.22 s** | no |
| 1 | 1 | 7.67 s | 0.000 s | — | **7.67 s** | no |
| 2 | 2 | 9.50 s | 0.000 s | 7.87 s | **17.37 s** | yes ("appears to supply a ready-made sentence…") |

The 16.7 s figure in the original profile was a **regeneration turn** like Turn 2.

## Answers to the specific questions

- **One LLM call or multiple?** Normally **ONE** Sonnet 4.6 call (~7.7–10.2 s). It becomes **two** only when the deterministic validator rejects the first draft and forces a single regeneration.
- **Is the validator triggering regeneration frequently?** In this sample, **1 of 3 turns (33 %)**. Each regeneration adds a **full second Sonnet call (~7.9 s)**, roughly doubling Stage C. This is the entire explanation for the "~16.7 s" cases; the "fast" cases are ~8 s.
- **Hidden retries?** **No.** Stage C has exactly one optional regeneration. (The 1-retry-on-failure logic lives in Stage B, not Stage C.)
- **Validator cost?** **~0 ms** — it is pure regex/string matching, not an LLM call. The validator is not the cost; the *consequence* of a validator failure (a second LLM call) is.
- **Are Teacher Review and Stage C sharing unnecessary work?** **No.** Teacher Review (`_curate_case`) is 0.14 s, is a pure dict transform of the already-computed Stage B plan, and runs **on demand** (`GET /teacher-reflection`) — it is **not** in the interact/coaching path at all.
- **Serial operations that could run in parallel?** Stage C must run *after* Stage B (it consumes the plan), so it cannot overlap Stage B. Within Stage C, gen1 → validate → (gen2) is necessarily serial. The only removable serial cost is the **regeneration**, and the only inherent cost is **single-call Sonnet latency (~8–10 s)** for a ~1,500-char render.

## Where Stage C time actually goes
```
gen1 (Sonnet render)     ~8–10 s   ← inherent model latency for the render
validate (regex)          ~0 ms
gen2 (regeneration)       ~8 s      ← ONLY when the first draft trips a rule (~33% here)
```

## Optimization levers (for Phase II — not yet implemented)
1. **Faster model for the render.** Stage C is a *constrained rendering* task bound to a fixed plan, not deep reasoning. Trialing **Claude Haiku 4.5** for Stage C could cut gen1 ~8–10 s → ~3–4 s. GATED: Haiku may be more prone to leaks/ready-made phrasing, so it must pass the deterministic validator + a coaching-quality spot check before adoption.
2. **Cut the regeneration rate.** Turn 2 regenerated on "appears to supply a ready-made sentence." If some of these are false positives (the `_READYMADE_RE` / long-quoted-clause heuristic firing on a legitimate illustrative fragment), tightening the check or pre-instructing the renderer against the one rule it most often trips would remove the second ~8 s call on ~1/3 of turns.
3. **Prompt discipline.** A shorter, more prescriptive render prompt reduces both output length (→ faster gen1) and the chance of tripping a rule (→ fewer gen2).

Net: Stage C is not doing hidden work — it is one Sonnet call, occasionally two. The two biggest safe wins are a faster render model and a lower regeneration rate.
