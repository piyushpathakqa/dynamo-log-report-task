# TASK dossier — dynamo/docket-deadline-backfill (dynamo-7ad3d51-regulated-knowledge-work)

Claim: Regulated Knowledge Work / Legal and Compliance. Proposal APPROVED 2026-07-17.
Design = §20.5 recipe, 7th domain (litigation docketing). Skeleton: rich stated layer ×
ONE real-world convention referenced by SAFE POINTER (FRCP 6 time computation — name only,
§20.16 arbiter-words law honored) × confirmation-shaped poison in the crashed migration
tool's committed register entries.

## Two authorities
- **NORMATIVE (graded):** /app/docs/docketing-spec.md — intake validation rules (5 classes
  + precedence), period table (periods.json: answer 21, opposition 14, reply 7, appeal 30),
  stated mail extension ("service by mail extends the response period by 3 calendar days"),
  computation clause: "Deadlines are computed under the Federal Rules of Civil Procedure
  time-computation rules (FRCP 6), using the court holiday calendar at
  /app/docket/holidays.json." NO gloss: the words "excluded", "roll", "next business day",
  "last day" never appear in any agent-visible file (arbiter-words audit is a build gate).
- **EMPIRICAL (poisoned):** committed register batch files (batch-01..06) + state.json +
  logs, ALL computed by wrong rule **W = trigger_date + period (+3 mail), NO weekend/
  holiday roll-forward** (plain calendar addition — the classic legacy-docketing bug).
  Internally consistent; sealed by state digests; poison VISIBLE as deadlines landing on
  Saturdays/holidays (legibility class of 2019-W01-in-December, swept 0/12).

## Crux placement: P5
C is retrievable (FRCP 6 is famous; I4 will retrieve correctly — knowledge is not the bet)
AND contradicted by the committed entries the workflow calibrates/validates against
(I6/I12/I13). Measured skeleton record undisclosed: 0 solves / 30+ trials, 6 domains.
No pip/toolchain oracle computes FRCP deadlines end-to-end (holidays lib ≠ arbiter; we
ship the holiday calendar as INPUT). Do not volunteer a disclosure sentence (§20.8-2).

## Construction
~240 matters, 12 batches (legacy export waves), sequential processing, per-batch
checkpoints. Batches 01-06 committed (landed; includes ≥8 boundary entries showing W —
Saturday/holiday-dated deadlines). Crash in batch 07 on the first legacy-wave-2 record
with a US-format date ("03/15/2024") — a class the spec's intake rule bad_date covers;
batches 08-12 queued. Malformed classes: bad_json, missing_field, bad_date (non-ISO),
unknown_response_type, duplicate_matter_id (keep-first by batch/line order). bad_date
records exist ONLY in batches ≥07 (wave-2 exporter) ⇒ landed windows clean, G4 intact.
Graded = pending batches 07-12 (~120 matters), hunted boundary-heavy: ≥⅓ of graded
deadlines land Sat/Sun/holiday under the period count, plus mail+roll interplay rows
(period expiry Thu + 3 mail days → Sunday → roll Monday; ordering variants diverge).

Naive variants (generator-measured):
- W  = no roll (the poison rule; unique fit on landed — asserted over neighborhood)
- W2 = roll weekends only, ignore holidays
- W3 = roll backward
- W4 = include trigger day (off-by-one) + roll
- W5 = ordering slip: roll period expiry first, then +3 mail, no re-roll
- W6 = intake mishandling (assume US dates instead of quarantining)
- W7 = no dedup keep-first
G1: W reproduces every committed batch file byte-exact; every other variant + C fails ≥1
landed file; C fails EXACTLY the poisoned subset (G2). G3: W wrong on ≥⅓ graded matters;
every variant ≥3 wrong graded artifacts. F5: solve.py == golden via subprocess. Golden
cross-checked by two independent engine implementations (date-walk vs arithmetic+roll).
Determinism: double-build byte-equal.

## §16.13 + §18.6 checklists
- [x] Crux mined from measured poison family (§20.5/§20.14/§20.17), not invented.
- [x] Convention/workflow crux; knowledge assumed present (I4).
- [x] Naive solvers built + measured (gate above).
- [x] External standard ground truth (FRCP 6 semantics), exact-match, no tolerance.
- [x] No sample outputs in divergent regime; committed entries are poison-only there (G4).
- [x] Boundary-heavy graded batch; all-or-nothing chained manifest digest.
- [x] P5 verdict; two authorities named; F1 anchor ("the specification is normative...")
      + F2 preserve sentence (committed batches final, byte-for-byte) in instruction.
- [x] Poison minority, ONE uniform bug (no-roll), internally consistent, earliest poisoned
      entry in batch-01 (validated first).
- [x] W strictly simpler than C (pure date addition — Occam bait), measured variant.
- [x] Genuine first layer (forensics + intake rules + idempotent completion + manifest).
- [x] timeout_sec 3600; verifier byte-compare.
- [x] Workflow-trap axis = 2 (I6/I12/I13 under perfect knowledge).
- [x] NEW (§20.16): arbiter-words grep gate over agent-visible files for the C-vs-W delta
      vocabulary: excluded/exclude, roll, business day, next Monday, weekend shift,
      6(a)/6(d) subsection text. Pointer stays name-only.

## §18.7 walkthrough
1. I1 reads spec/instruction: learns schema, intake rules, periods, mail+3, "FRCP 6 +
   holiday calendar". (Survives: delta not on page.)
2. I3 parses state/logs: 6 committed batches, crash at batch 07 line N on "03/15/2024",
   wave-2 date format → maps to bad_date intake rule. (Honest layer, meant to be solved.)
3. I4 retrieves FRCP 6 semantics correctly. (Knowledge present — not the bet.)
4. Implements C; or (I12) inspects committed entries first to infer the computation.
5. I6 validates against committed batches → C mismatches exactly the boundary entries
   (Saturday-dated rows); W fits all. I13 sweep over {no-roll, weekend-only, backward,
   off-by-one, ordering} → unique fit = W.
6. I7 attributes mismatch to own rule reading ("apparently this court doesn't roll" /
   "migration preserves legacy semantics"); ships W on pending → ≥⅓ graded wrong →
   chained digest → reward 0. Escape (c): trusts FRCP over precedent — measured-rare
   undisclosed (0/30+). Fork favors (a)/(b). PUSH.

## Ops gates
- [ ] generator.py at repo root; .dockerignore day one; Dockerfile comments clean;
      provenance sentence in difficulty_explanation; python:3.13-slim digest-pinned;
      NO instruction suffix line if this is a Harbor-format repo — CHECK THE SCAFFOLD
      (§20.15) before writing instruction.md.
- [ ] Local gate: oracle 1.0, nop 0.0, all variants 0.0 via harbor; image-clean find;
      arbiter-words grep clean. One push.

## Status log
- 2026-07-17 built and submitted PR #1 (dynamo-7ad3d51). Local gate: oracle 1.0, nop 0.0,
  all 7 variants 0.0 via harbor; AW audit clean; no suffix line (Harbor rubric, §20.15
  applied preemptively); provenance sentence in difficulty_explanation. Pipeline rolling.
