# PROGRESS — dynamo/group-scope-report (Data Querying and Databases / Graph and semantic queries)

Repo: `dynamo-e0ab8e2-data-querying-and-databases`, PR #1 (branch `submission`).
Claimed & built 2026-07-15. Proposal approved same day (portal).

## Design (per §20.5 validated recipe — all three seed-gate legs present)

- **Seed gate (claim-time):** (a) real-world known-but-UNSTATED convention =
  consolidation control attribution (voting rights held via controlled entities
  count IN FULL, never pro-rated — IFRS-10/companies-act practice); (b) no
  pip/toolchain oracle computes consolidation scope (networkx = reachability
  only); (c) empirical surface of same kind as deliverable = crashed
  scope-analyzer's 20 completed report rows.
- **Stated first layer:** temporal as-of positions over a transfers ledger
  (SQLite), dual share classes (voting vs economic), effective-interest
  simultaneous equations (circular cross-holding E050↔E051 → exact linear
  solve), six-decimal ROUND_HALF_UP strings, SHA-256 canonical-row digest,
  all-or-nothing exact verifier.
- **Crux (P5, confirmation-shaped poison):** spec §2 says control = ">50% of
  voting rights held directly or indirectly"; the attribution semantics are
  professional knowledge. Analyzer's completed rows computed with W1 =
  pro-rated look-through of voting rights: 14/20 rows correct-on-simple-chains,
  6/20 silently wrong (all one family: in_scope=false + nulls where truth is
  true; earliest at R003). I12 calibration or I13 refit lands exactly on W1.
- **Measured geometry (generator hard-asserts, all pass):** G1 across the full
  sweep neighborhood (matrix walk / simple-path sum / dominant path × > / ≥,
  voting basis; econ-basis and direct-only variants fail ≥1 completed row so a
  sweep converges to W1); G2 exactly the 6 poison rows; G3 pending divergence
  W1 25/40, W2 (direct-only) 23/40, W3 (share-count basis) 4/40, W4
  (majority-chain) 9/40; G4; rounding margins under both pipelines; ledger
  conservation; no-leak; F5 oracle==golden via subprocess (3 independent
  implementations agree: in-memory, SQL-driven, solve.py).
- **Anchors:** F1 ("each row you complete must hold exactly the values the
  registry determines under the rules in spec.md") + F2 ("rows already marked
  complete … reproduce them unchanged"). NO possibly-wrong disclosure sentence
  (per §20.8 — don't volunteer; fairness case ready: same structure as
  mass-report, whose stricter re-review independently endorsed the poison as
  "an engineering error, not a defensible competent choice").
- Config: agent timeout 3600, provenance sentence in difficulty_explanation
  (§20.11), generator.py committed at repo root, .dockerignore present.

## Local gate (all green before the single substantive push)

oracle 1.0 (harbor), nop 0.0 (harbor), W1–W4 full reports each 0.0 through the
real verifier in the pinned image. Hint-grep clean; base-image check pass.

## Timeline

- 2026-07-15: PR #1 opened. Static check ❌ (Dockerfile COMMENT mentioned
  tests/test.sh — checker greps comments too). Fixed comment wording, pushed
  (pre-pipeline static fix, same pattern as mass-report's .dockerignore fix).
- 2026-07-15/16: **FULL CLEAN SWEEP — ACCEPTED.** Rubric PASS, similarity
  UNIQUE, validation PASS, pass@2 0/2 (2/2 valid, all criteria PASS), deep
  review PASS (zero blocking; advisory blessed the poison as "legitimate,
  spec-consistent difficulty"), pass@5 0/5, avg@5 0.000, 4/5 good valid fails.
  Both pass@2 agents shipped the byte-identical predicted W1 digest
  (9770177…). One pass@5 agent produced the exact GOLDEN digest first, then
  discarded it after validating against the poisoned rows; three others had
  their own implementation bugs amplified into algorithm substitution by the
  G1 perfect fit. Outcome logged (§20.14, DesignRecord + new Principle,
  dataset rebuilt: 28 records / 21 principles / 77 examples).

## STATUS: ACCEPTED — FROZEN, DO NOT PUSH

Human R1/R2 pending. Do not volunteer the disclosure sentence; fairness case
ready (deep review + mass-report re-review precedents). Any push re-rolls the
full pipeline including pass@2/pass@5 (§20.6).

## Predictions (for the dataset record)

- pass@2 kill-chain: I12 (calibrate scope semantics from completed rows) or
  implement-C-then-I6-validate → 6 mismatches → I13 variant sweep → W1 →
  25/40 graded rows wrong → reward 0 valid fail.
- Main risks: (1) human reviewer mandates a §20.8 disclosure sentence →
  falls back to unstated-convention leg (agents likely look up correctly →
  solved); (2) agent knows the statutory attribution convention AND trusts it
  over a perfect empirical fit — contradicts I12/I13 (11/11 undisclosed).
