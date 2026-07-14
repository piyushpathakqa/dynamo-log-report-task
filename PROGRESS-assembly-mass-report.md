# PROGRESS — mass-report-recovery (CAD and mechanical workflows)

**Status 2026-07-14 — CLEAN SWEEP, ALL CHECKS GREEN, AWAITING HUMAN REVIEW.**
PR #1 on handshake-project-dynamo/dynamo-48e280f-hardware-embedded-and-low-level-systems.
**pass@2 = 0/2, pass@5 = 0/5, avg@5 = 0.000 — 7/7 good valid fails, first attempt.**
All rubric criteria PASS every trial; deep review PASS ("fair verifier: a knowledge
lure, not an undiscoverable guess"); similarity + validation PASS; traces clean.
Kill-chain as designed but STRONGER: agents inferred the gauge mapping FROM the
poisoned rows (calibration-first, not retrieve-then-validate) — recorded as invariant
I12 + full post-mortem in DYNAMO-REFERENCE.md **§20** (canonical copy in this repo).
**DO NOT push anything to the PR — any push re-runs the full pipeline including
pass@2.** Remaining lifecycle: human R1/R2 → RTD (bonus). Answer any reviewer
advisories with PR COMMENTS only (§18.8).

Local gate had been: oracle 1.0, nop 0.0, all 5 naive variants 0.0 end-to-end;
generator hard-asserts G1-G4+R1+F5; 5 poisoned rows of 20 (first at row 3);
W diverged 22/34 graded lines — exactly the divergence the trials then showed.
**Seed:** Hardware Embedded and Low Level Systems / CAD and mechanical workflows.
**Prior seed (build-dep/cross-compile) is CLOSED** — see §18.11–§19.10; 10 designs, 0 stumps.

## Design in one line

Rich mass-properties/BOM report over a legacy PLM drawing-package export (clears rubric)
+ material-family gauge-table crux (real-world, UNSTATED, pattern A — the doc's own
canonical winner §19.3-A) + poisoned legacy report rows (crashed tool misconfigured with
a single default gauge table; entangled same-kind as the deliverable — rev-5/§18.4
geometry as corrected by §18.11) + byte-exact all-or-nothing chained grading.

## Why this fits the winning intersection (§19.9–§19.10)

- **Clears rubric:** multi-step dependent execution — parse multi-file export, mixed
  inch/metric drawings, flat-pattern + bend-allowance computation (formula STATED),
  hole/cutout subtraction, density lookup (densities SHIPPED for determinacy),
  multi-level BOM quantity roll-up, strict rounding/format spec. Survives disclosure:
  state every rule and an engineer still has hours of exacting work (§19.1).
- **Stumps pass@2 (the bet):** the deciding rule — gauge→thickness depends on material
  family (steel MSG vs aluminum B&S vs stainless sheet gauge) — is REAL-WORLD,
  expected-known, NOT stated, NOT a standard algorithm, with NO in-env recompute
  oracle. Pattern A can bite a rule the model must SUPPLY (§19.10). The poison makes
  diligence the trap: completed legacy rows embed steel-gauge-for-everything.

## G1–G4 mapping (hard-assert ALL in generator)

- **G1:** W = "steel (MSG) gauge table for all materials" reproduces EVERY completed
  legacy row exactly (steel rows are genuinely correct; non-steel rows were produced
  by the misconfigured tool). One uniform bug, internally consistent (F3).
- **G2:** C (material-correct tables) mismatches exactly the non-steel legacy rows.
- **G3:** graded (uncompleted) parts are ≥⅓ non-steel; per-row mass + roll-ups + a
  file-level total chain them; byte-exact → one wrong row = reward 0. Divergence
  10–60% mass, orders beyond rounding.
- **G4:** NO gauge table shipped in-env; no tool computes thickness; no spec-side
  worked example covers a non-steel sheet part. (Steel-only worked examples OK.)

## Fairness anchors

- **F1:** instruction anchors graded values to "each part's true nominal material
  thickness per applicable industry sheet-metal standards" (determinable via public
  knowledge/internet — the fair escape path; rev 5 won WITH retrievable standards).
  Do NOT ship an in-env datasheet stating the mapping (§18.11 kill condition).
- **F2:** legacy rows are "historical output, preserved as produced" (out of graded
  delta + not to be re-derived).
- **F4:** nothing lies; misconfigured-default-gauge-table is a real PLM failure mode.
- **F5:** reference solution solves from agent-visible data + public standards only.

## Determinacy guards (build-time)

- Densities SHIPPED in materials.csv (published density values vary by source).
- Bend allowance / K-factor STATED (not universal knowledge → would be unfair).
- Rounding (whole grams or stated decimals) chosen so all published editions of the
  standard gauge tables (±0.0002 in variance) yield IDENTICAL rounded values —
  generator hard-asserts this by sweeping table-edition perturbations.
- Every verifier-checked convention (CSV schema, column order, sort, rounding stage,
  units of output) STATED in instruction (rejection reason 1).

## §18.7 walkthrough (must reach reward 0 with zero knowledge failures)

1. I1 reads spec/instruction — deciding convention not on the page. Survives.
2. I3 enumerates parts, materials, units, legacy-completed vs pending. Survives
   (regimes are meant to be seen).
3. I4/I10: knows or retrieves gauge tables correctly — knowledge is NOT the bet.
4. Implements C (or W) and computes pending rows.
5. I6 validates against completed legacy rows → non-steel rows mismatch (if C).
6. I7: "my bug." Diagnostics: steel-for-all fits ALL legacy rows perfectly (G1) and
   is strictly simpler (Occam bait). Adopts W → ≥⅓ graded rows wrong → 0.
   Escape (c): re-reads F1 anchor, attributes to crashed tool, ships C — exists, fair,
   but requires overriding I6 exactly as in rev 5.
Fork verdict: (a)/(b) workflow-natural; (c) is the override. PUSH-worthy per §18.7.

## Honest residual risks

1. **I10 thoroughness:** Opus may apply material-specific tables from the start and
   dismiss the legacy rows as the tool's bug (the §18.11 failure mode). Mitigations:
   no in-env authority stating the mapping; legacy rows are SAME-KIND as deliverable
   (entangled, not a separately-labeled reference file); steel-heavy samples.
   This is the residual bet — same bet rev 5 won 4/4 trials.
2. **Similarity:** §19.3-A (steel/non-ferrous weight) is a live example. Mitigation:
   different artifact (flat-pattern + BOM roll-up report), added poison layer,
   different framing. §18.8: re-aimed cruxes passed similarity twice.
3. Config: `[agent].timeout_sec = 3600` from first push (deliberation trap, I9).

## Build checklist (when proposal clears)

- [ ] §16.5 generator with hard-asserts: oracle==golden via subprocess; W and every
      naive variant fail ≥⅓ rows; no leak of tables/expected outputs; G1–G4 asserts;
      table-edition rounding-stability sweep.
- [ ] Naive variants to measure: W (steel-for-all), t/2 neutral axis instead of stated
      K, unit-mix errors, roll-up without quantities, wrong-stage rounding.
- [ ] Local gate: oracle 1.0, nop 0, every naive 0 (harbor end-to-end), W-as-solver 0.
- [ ] §13 pre-submit gate + §18.6 checklist + §17.2 rubric ≥9/12 with §18.9 open,
      Workflow-trap axis = 2.
- [ ] pass@2 budget: 6/day — push only after full local gate green.
