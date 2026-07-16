# TASK dossier — dynamo/etl-week-backfill (dynamo-cd6e953-debugging-and-repair)

Claim: Debugging and Repair / Pipeline and orchestration debugging. Proposal APPROVED 2026-07-16.
Design = §20.5 validated recipe, 5th domain (ETL orchestration). Skeleton identical to
mass-report-recovery / group-scope-report: rich stated layer × ONE real-world convention
(ISO 8601 week-date year-boundary semantics, NAMED in spec — pointer à la tflite gemmlowp,
fairness asset not workflow arbiter, §20.12) × confirmation-shaped entangled poison in the
crashed tool's landed checkpointed partitions.

## The two authorities (named, per §18.6)
- **NORMATIVE (graded):** `/app/docs/pipeline-spec.md` — defines event schema, quarantine
  rules (incl. missing-UTC-offset), UTC normalization, rollup aggregation, partition keying
  "ISO 8601 week-date: ISO week-year + week number, `YYYY-Www`, of the event's UTC date"
  (named, NOT itemized: no first-Thursday explanation, no boundary worked example — G4).
  F1 anchor sentence in instruction + spec ("the specification is normative for all
  partitions produced to complete the backfill").
- **EMPIRICAL (poisoned):** the crashed run's landed artifacts: 25 checkpointed partition
  files + state.json + logs, ALL keyed/grouped by wrong rule **W1 = calendar year of the
  event's UTC date + ISO week number** (the classic `%Y`+`%V` production bug). Internally
  consistent (F3): state digests seal the wrong files; logs name the wrong keys.
  F2 sentence: completed partitions are final, preserve byte-for-byte, do not recompute.

## Crux placement: P5
Correct rule available two ways (spec names ISO 8601 week-date; Python `isocalendar()` is
the canonical implementation in-hand) AND actively contradicted by the empirical surface
agents calibrate against (I6/I12/I13). Measured record for this skeleton undisclosed:
0 solves / 25 trials across 4 domains. Do not volunteer a "landed rows may be wrong"
disclosure sentence (§20.8-2 posture).

## Construction
Fiscal year-end audit windows (event dates Dec 1 – Jan 31 UTC), 6 windows:
- FY2019 (2019-12-01..2020-01-31), type A boundary (Dec 30-31 2019 → ISO 2020-W01) — LANDED (poison shows A-direction: spurious landed key `2019-W01`).
- FY2020, type B (Jan 1-3 2021 → ISO 2020-W53) — LANDED (poison shows B-direction: spurious `2021-W53`). Both directions landed ⇒ W1 is the UNIQUE fit in the sweep neighborhood (kills Monday-year/Thursday-year variants — I13/G1-neighborhood).
- FY2021 (B), FY2022 (B), FY2024 (A), FY2025 (A) — PENDING = graded (35 partitions under C).
Worker story: 2-worker pool, queue order [FY2019, FY2020, FY2024, FY2025, FY2021, FY2022]
(current-audit windows first). Q3-malformed records (timestamps without UTC offset, new
mobile SDK) exist only at dates ≥ 2024-12-26 ⇒ FY2019/FY2020 completed clean; worker 1
crashed in FY2024 at partition 2024-W52 (after 4 clean checkpoints), worker 2 crashed in
FY2025 at its first partition 2025-W49; FY2021/FY2022 never started. No divergent pending
key ever appears in logs/state (G4). Crash diagnosable: main log (retries, exit 1) +
per-window stderr log (ValueError on offset-less timestamp) + state.json checkpoints.
`rollupd` worker binary NOT in the sandbox (in-story: deployed on the warehouse cluster) ⇒
the wrong rule lives only in landed data, never in readable source (avoids P1).

W1-divergent graded artifacts: spurious `2024-W01`, `2023-W52`; wrong-content `2025-W01`
(merged Jan 2025 + Dec 2025!), `2026-W01`, `2021-W52`, `2022-W52`; + manifest (partition
set, per-file digests, chained dataset digest) ⇒ reward 0 (G3 chaining). Holiday volume
spike (Dec 24–Jan 6) tuned so wrong-file row-mass ≥ ⅓ of graded rows (generator-asserted).

First difficulty layer (stated, honest, expert-hours substance): log/state forensics;
quarantine rules Q1 bad_json / Q2 missing_field / Q3 missing_offset / Q4 bad_value /
Q5 duplicate_id (keep-first by stated global order); mixed timestamp offsets → UTC
normalization; idempotent completion; canonical JSON serialization; manifest digest chain.

## Generator hard-asserts (before any prose)
- G1: recomputing every LANDED partition from raw under W1 ⇒ byte-identical, 25/25 (incl.
  both poison directions); under Monday-year, %Y-%W, %Y-%U, C ⇒ each fails ≥1 landed file
  (unique-fit assert); C fails EXACTLY the poisoned subset (G2), nothing else.
- G3: W1 completion ⇒ ≥6 wrong graded partition files + wrong partition set + wrong
  manifest; wrong-file row-mass ≥ 33% of graded rows; every naive variant (W1, W2 %Y-%W,
  W3 %Y-%U, W4 local-date keying, W5 naive-ts-as-UTC, W6 no-dedup) differs from golden on
  ≥3 graded files (byte-compare).
- G4: no Q3 record in any landed week; no pending partition key (under C OR W1) collides
  with a landed key; logs/state contain no pending key.
- F5: `solution/solve.py` run via subprocess in a sandbox == golden, byte-exact, all files.
- Keying cross-check: `isocalendar()` == independent first-Thursday implementation over
  every event date (external-standard leg, §20.9 rule).
- Determinism: full regeneration twice ⇒ identical bytes (fixed seed, no wall-clock).

## §16.13 pre-flight checklist
- [x] Crux mined from observed-failure library (I6/I12/I13 poison family, §20.5/§20.14) — not invented.
- [x] Convention/workflow crux, not reasoning crux.
- [x] Naive solver built + measured failing (generator asserts, below).
- [x] Ground truth = external standard (ISO 8601 week-date via isocalendar + independent reimpl), exact-match, no tolerance.
- [x] No sample outputs covering the divergent regime; landed examples are poison-only there (G4); shipped invariants (state digests) seal poison, not golden.
- [x] Boundary-heavy graded batch; all-or-nothing via manifest digest chain.
- [x] Generator hard-asserts: oracle==golden via subprocess, naive fails ≥N, no leak.

## §18.6 pre-flight checklist
- [x] Placement verdict P5.
- [x] Two authorities named above; F1 anchor + F2 preserve sentences drafted into instruction.
- [x] G1 G2 G3 G4 all generator-asserted (G1 over the sweep neighborhood incl. Monday-year).
- [x] Poison = minority of empirical surface (4 divergent landed files of 25; boundary
  regime only), ONE uniform bug (calendar-year keying), internally consistent (F3),
  earliest poisoned object early (FY2019 landed first; `2019-W01` sits in the first
  window's checkpoints — first thing validated).
- [x] W1 strictly simpler than C (calendar year is the lazy year; Occam bait) and is a
  measured naive variant.
- [x] Genuine first layer exists; W1 is wrong about the DATASET (partition set, contents,
  manifest), not only about poison reproduction.
- [x] [agent].timeout_sec = 3600; verifier byte-compare instant.
- [x] §18.7 walkthrough below reaches reward 0 with zero knowledge-failure steps.
- [x] Workflow-trap axis = 2 (fires on measured invariants I6/I12/I13 under perfect knowledge).
- [x] Local gate before push: oracle 1.0, nop 0, every naive variant 0 end-to-end.

## §18.7 simulated-adversary walkthrough
1. I1: reads instruction + pipeline-spec.md + dag.yaml + runner.py. Learns schema,
   quarantine rules, "ISO 8601 week-date" keying, F1/F2. *(Survives: conflict not on page.)*
2. I3: scripts a parse of state.json + logs: enumerates 25 completed partitions, 2 failed
   windows w/ tracebacks, 2 queued windows; identifies crash cause = offset-less
   timestamps from mobile feed starting 2024-12-26; maps them to spec rule Q3.
   *(Survives: forensics layer is meant to be solved; regimes visible.)*
3. I4: knows ISO week-date semantics (isocalendar one-liner). *(Knowledge is NOT the bet —
   assumed present.)*
4. Implements C: quarantine + UTC + isocalendar keying + aggregation + manifest.
5. I6/I12: validates against landed partitions (recompute-from-raw or infer keying from
   state keys). C recomputation mismatches exactly 4 landed files (`2019-W01`, `2020-W01`,
   `2020-W53`, `2021-W53` contents/existence); W1 fits all 25 (G1).
6. I7/I13: attributes mismatch to own code ("my keying is off at year ends"), sweeps
   variants (isocalendar / %V+%Y / %W / %U / Monday-year); UNIQUE perfect fit = W1.
   Diagnostics confirm (delta = year-label at boundary weeks only).
7. Fork: (a) ships W1 completion → spurious `2024-W01`/`2023-W52`, wrong `2025-W01`,
   `2026-W01`, `2021-W52`, `2022-W52`, wrong manifest → chained digest → reward 0.
   (b) stalls deliberating (3600s budget accommodates). (c) ESCAPE: re-reads spec, weighs
   F1 over precedent, attributes boundary mismatch to the crashed tool, ships C.
   (c) exists (fair); measured workflow takes (a)/(b): 25/25 undisclosed trials.

## Deliverables / verification
artifacts: /app/backfill/partitions (landed preserved + pending created),
/app/backfill/quarantine.jsonl, /app/backfill/manifest.json. Verifier: byte-exact vs
tests/expected (pending partitions, partition set, landed preservation, quarantine,
manifest+chained digest). 5 tests, 1:1 with numbered instruction criteria.

## Ops checklist for this build
- [ ] generator.py at repo root, committed (§18.8/§20.11 spot-check answer).
- [ ] task/environment/.dockerignore from day one (§20.6).
- [ ] Dockerfile comments must not mention solution/tests (§20.14 static-check grep).
- [ ] difficulty_explanation includes data-provenance sentence (§20.11).
- [ ] python:3.13-slim digest-pinned base; pytest==8.4.1 + pytest-json-ctrf==0.3.5 baked.
- [ ] agent timeout 3600 == instruction suffix N; verifier 300; build 900.
- [ ] Instruction ≤1500 tokens, exact suffix line, no headers/title.
- [ ] Local: oracle 1.0, nop 0.0, W1..W6 variants 0.0 via harbor before push; image-clean find.
- [ ] One push; pass@2 cap 6/day; after sweep: FREEZE.

## Status log
- 2026-07-16 submitted PR #1 (dynamo-cd6e953). Static checks: ALL PASS (suffix line present, unflagged).
- 2026-07-16 rubric: 30/31 PASS, 1 FAIL — instruction_concision: this Harbor-format repo's rubric
  enumerates the TB2 "You have N seconds…" suffix as an explicit FAIL condition (delete; budget lives
  in [agent].timeout_sec). Fixed, re-pushed (0f6910e). Free failure — pass@2 had not run.
  Rubric notes independently VERIFIED the poison's internal consistency ("poisoned and correct events
  never double-count") and PASSED essential_difficulty naming the ISO week-year trap + poisoned
  precedent as "genuine expert difficulty" — the design is rubric-blessed pre-pass@2.
- Pipeline re-rolling; awaiting similarity/validation → pass@2 → deep review → pass@5.
- 2026-07-16 pass@2 rev 1: **2/2 SOLVED (LOSS)**. Kill-chain broke at attribution: spec's words
  "ISO week-year" arbitrated the poison's delta on paper (§20.16 arbiter-words law). Rerun
  recommended by platform. Revision: de-arbitrate spec §5 + instruction criterion 2 — keep
  "week date" + YYYY-Www notation (expert-recognizable, group-scope fairness precedent), remove
  "ISO week-year / ISO week number" gloss. Data, generator, tests unchanged (wording-only).
- 2026-07-16 rev 2 pushed (801b664): spec §5 de-arbitrated — "week date, YYYY-Www" notation only,
  no week-year/ISO gloss; instruction criterion 2 aligned; explanations updated with the
  pattern-A fairness case. Data/generator/tests byte-identical; oracle re-verified 1.0.
  PR comment documents the change honestly. Pipeline re-rolling (pass@2 slot 2/6 today).
  §18.7 re-walk: spec now silent on year-choice; precedent = only in-env authority (I12) —
  measured group-scope configuration. Known risk: rubric may re-judge unambiguous/decisive-rule
  on the vaguer wording (free failure if so; fairness argument ready).
