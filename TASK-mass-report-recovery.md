# TASK DOSSIER — dynamo/mass-report-recovery

One-page record of the task, the design reasoning, the implementation, the results,
and where it stands. Written 2026-07-14, the day of the clean sweep.

- **PR:** https://github.com/handshake-project-dynamo/dynamo-48e280f-hardware-embedded-and-low-level-systems/pull/1
- **Repo (local):** `~/Work/dynamo-48e280f-hardware-embedded-and-low-level-systems` (fork `piyushpathakqa`, branch `submission`)
- **Category:** Hardware Embedded and Low Level Systems / CAD and mechanical workflows
- **Result:** pass@2 = 0/2, pass@5 = 0/5, avg@5 = 0.000 — 7/7 good valid fails, first attempt, all checks green
- **Status:** automated pipeline fully passed → **waiting for human reviewer** (R1/R2 → RTD pays the bonus)

---

## 1. The task (what the agent faces)

A PLM reporting tool ("MPROP") crashed partway through generating the mass-properties
report for a 48-part mechanical assembly (AS-4400 hoist carriage). The agent gets the
drawing package and must finish the report:

- `bom.csv` — multi-level BOM (root, 5 subassemblies, 48 parts, quantities 1–6)
- `parts.jsonl` — per-part geometry: sheet parts (gauge callout, flange dims, 90° bends
  with inside radii, holes, cutouts) and machined parts (rect/round bar, mixed inch/mm)
- `materials.csv` — densities (shipped, so results are exactly determinate)
- `format_spec.md` — the controlling spec: every computation rule stated (K=0.44 bend
  allowance, area subtraction, conversion constants, rounding to whole grams, report
  schema and ordering)
- `mass_report.csv` — the partial report: header + the 20 PART rows the tool completed
  before it died

Deliverable: `/app/mass_report_complete.csv` — the 20 existing rows preserved verbatim,
correct PART rows for the remaining 28 parts, ASSY roll-ups, and the TOTAL. Byte-exact,
all-or-nothing.

## 2. The crux (why the model fails)

The **one** rule the spec does not tabulate is real-world domain knowledge, not an
invented convention: resolving a sheet-gauge callout to a decimal thickness is
**material-family-specific** in standard U.S. practice — Manufacturers' Standard Gauge
for carbon steel, Brown & Sharpe for aluminum, the stainless sheet gauge for 304
(e.g. 16 ga = 0.0598" steel / 0.0508" aluminum / 0.0625" stainless).

The crashed tool was misconfigured with the **steel table for every material**. So its
20 completed rows are internally consistent, correct on its 14 steel + 1 machined
parts, and silently wrong on its 5 non-steel parts (first poisoned row is row 3).
The instruction requires those rows preserved "as produced" — they're out of the
graded delta but sit there as the only worked precedent. The remaining 28 graded
parts are non-steel-heavy, so applying the steel table to everything fails 22 of 34
graded lines (aluminum +12–30% mass, stainless −4–5%).

**What actually happened in all 7 trials:** the agents did not look up gauge practice.
They inspected the 20 existing rows, *inferred* the steel table from them (they know it
from memory), validated against all 20 rows, got **zero mismatches** — because the tool
had made the identical error — treated that as confirmation, applied it to all
materials, and shipped in 3.5–8 minutes. The poison wasn't a contradiction to argue
them out of the right answer; it was the *primary source* for the missing constant.
Diligence itself was the trap.

## 3. Thought process (how the design was chosen)

1. **Claim-time seed gate** (the lesson bought by 10 lost hours in cross-abi): before
   building, the seed had to offer (a) a real-world *expected-known-but-unstated*
   convention applied over many records, (b) *no recompute oracle* — no tool, library,
   or compiler that prints the deciding values, and (c) a poisonable empirical surface
   of the *same kind as the deliverable*. CAD/mechanical had all three: gauge tables /
   no tool computes them / report rows. (Cross-compilation had none — every fair fact
   there is stated, tool-printable, or sweepable; see DYNAMO-REFERENCE.md §18.11–§19.10.)
2. **Two-layer composition** (§19.8/§19.9 lesson): a rubric-proof body of rich,
   fully-stated multi-step computation (flat patterns, mixed units, roll-ups,
   rounding discipline) × exactly ONE unstated real-world discriminator. Stated rules
   are implemented flawlessly by the model — they buy fairness and expert-hours, not
   difficulty. The difficulty lives in the single rule the model must supply itself.
3. **Poison as confirmation** (refining the rev-5/repair-capture-times geometry after
   §18.11 showed poison dies against a cleanly stated authority): here the correct rule
   is stated *nowhere* in-env, so the natural way to get it is from the precedent rows —
   which fit the simpler wrong rule perfectly (G1). The tool being *right on steel*
   makes the bug read as a plausible configuration default, not corruption.
4. **Paper walkthrough before building** (§18.7): every step of the adversary's known
   workflow was written down and reaches reward 0 *without assuming any knowledge
   failure* — the agents may know every gauge table on earth; the trap fires on how
   they choose which one applies. The trials then matched the walkthrough step-for-step.

## 4. Implementation (how it was built)

Build order was **generator first, prose last** — no instruction text until the trap
geometry was proven by asserts:

- `generator.py` (repo root — never enters the agent image; it is the difficulty proof
  for reviewers). Synthesizes the package from a seed and hard-asserts:
  - **G1** — the wrong rule W (steel-for-all) reproduces every completed row byte-for-byte
  - **G2** — the correct rule C mismatches exactly the 5 poisoned rows, nothing else
  - **G3** — W diverges on ≥⅓ of graded lines (measured: 22/34)
  - **G4** — leak scan: no agent-visible file contains any non-steel thickness value or
    gauge-table name
  - **R1** — every mass clears the 0.5 g rounding boundary by ≥0.02 g under BOTH rule
    sets (per-part dimension *nudging*, not global reseed — a global seed search does
    not converge over 48 parts); table-edition determinacy is handled in the spec by
    pinning "standard four-decimal-place decimal equivalents"
  - **F5** — `solution/solve.py`, an independent implementation run as a subprocess
    against a sandbox copy of agent-visible data only, reproduces ground truth exactly
  - Five naive solvers measured: steel-for-all (22/34 lines wrong), no bend deduction
    (21), K=0.5 (12), aluminum table for stainless (12), roll-up without quantities (6)
- `task/environment/` — pinned Ubuntu 24.04 base + pytest baked; `COPY data /app/data`;
  `.dockerignore` (a static check requires one when the context has subdirectories)
- `task/instruction.md` — ~370 tokens; carries the two fairness anchors: computed rows
  must hold "the values the specification defines for the part's true nominal geometry
  and material" (F1), and existing rows are "the tool's output of record … carry them
  over unchanged, exactly as produced" (F2)
- `task/tests/test_outputs.py` — six docstringed pytest checks: exists/parses, exact
  header, preserved rows verbatim, PART rows exact, roll-ups exact, whole-file equality
- `task.toml` — `artifacts = ["/app/mass_report_complete.csv"]`, agent timeout 3600 s
  from the first push (insurance; unneeded — confirmation-poison produces fast
  confident wrong answers, not deliberation stalls)

**Local gate before the single push:** oracle 1.0, nop 0.0, all five naive variants
swapped in as the solver = 0.0 end-to-end through harbor.

## 5. Results (measured, from the platform's own analyses)

- **pass@2: 0/2** — both valid fails, every rubric criterion PASS, "Rerun Recommended: NO"
- **pass@5: 0/5, avg@5 = 0.000** — 5/5 good valid fails
- **Deep review: PASS**, in its own words: *"This is a fair verifier: the trap is a
  knowledge lure, not an undiscoverable guess."* `decisive_rule_disclosed` and
  `spec_consistency` PASS; trace integrity clean (no reward hacking, no ground-truth
  access)
- Failure signature identical in every trial: steel table calibrated from the poisoned
  rows → zero-mismatch "confirmation" → applied to all materials; first differing row
  P-1023 in every trial; error directions exactly as engineered (AL over, SS under)
- One static-check iteration total (missing `.dockerignore`); zero task/verifier issues

## 6. The recipe (validated; full version in DYNAMO-REFERENCE.md §20.5)

1. Gate the SEED at claim time: unstated real-world convention + no recompute oracle
   + same-kind poisonable surface. Any leg missing → decline/reframe.
2. Rich stated execution body × one unstated real-world discriminator.
3. Poison as *confirmation*: uniform in-story bug, perfect fit on all visible rows
   (G1 — it preempts the search for the correct rule; invariant I12), correct on a
   subset so it reads as configuration, earliest poisoned row early, graded set heavy
   in the misled regime.
4. §18.7 walkthrough on paper must reach reward 0 with zero knowledge failures.
5. Generator with hard-asserts before any prose; margins by per-part nudging;
   determinacy pinned in-spec, not by shipping values.
6. Full local gate (oracle/nop/every naive), timeout 3600, ONE push.
7. After any loss: extract intelligence first; after 2 losses in a seed: reseed.

## 7. Where it stands + rules of engagement

- All automated checks green (static, rubric, similarity, validation, pass@2, deep
  review, pass@5). The task now **waits for the human reviewer** (R1, possibly R2);
  acceptance → RTD, which pays the bonus. Human reviewers are stricter than the
  automated checks — expect possible questions on the unstated-gauge fairness; the
  quote-proof answers are the deep review's own fairness verdict (§5 above) and the
  platform's canonical pattern-A example (§19.3-A, the steel/non-ferrous gauge task).
- **DO NOT push anything to the PR.** Any push re-runs the entire pipeline including
  pass@2 and can flip the sweep. Recipe/doc updates live in THIS repo. Answer reviewer
  advisories with PR *comments* only.
- Ops notes: repo access = accept the GitHub invite, then clone/push over **HTTPS with
  the `gh` credential helper** (SSH fails for these repos). `generator.py` at repo
  root is safe (image builds only from `task/environment/`). Optional nicety if a
  reviewer asks about provenance: `task/instruction.md` may be hand-rephrased — if
  edited, remember the push re-runs pass@2, so only do it if a reviewer requires it.
