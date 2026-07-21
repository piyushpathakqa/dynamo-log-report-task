# TASK dossier — thread-gauge-codegen (dynamo-b2f7712, Debugging and Repair / Build Failure repair)

Status: **ACCEPTED 2026-07-21** (label accepted; pass@2 0/2 ×2 rolls, pass@5 0/5, 5/5 good valid, avg@5 0.000, deep review + AVA PASS). FROZEN — DO NOT PUSH (any push re-rolls the full pipeline). Human R1/R2 pending. See §20.21–§20.22.
from session 76ea637d; proposal verbatim in user message 2026-07-20).

## The two authorities (named, §18.6)
- **NORMATIVE (graded):** ISO 965-1:1998 tolerance system (fundamental deviations Table 1;
  TD1 Table 3; Td Table 4; TD2 Table 5; Td2 Table 6) + ISO 724 basic diameters, anchored
  byte-exact to ISO 965-2:1998 Tables 1–4 (6H/6g, coarse+fine) extracted from the published
  BS PDF (regbar.com mirror, in scratchpad). SPEC.md names the standard pointer-only
  (arbiter-words law honored: no deviation signs/magnitudes/directions glossed in any
  agent-visible file; grep-gated in generator, G4).
- **EMPIRICAL (poisoned):** 14 committed generated units `gen/part_*.c` produced by the
  in-story tool `partgen 1.4.2` — external parts (9) correct; internal parts (5) computed
  with W. Preserved-as-is per instruction (F2). Internally consistent, sealed by manifest
  story (F3 analog: values are plain but uniform and tool-attributed).

## W (the poison rule — one uniform bug, Occam-simpler than C)
Single code path, case-folded class letter, external tables for everything:
`es = es_ext(lowercase(position))` from ISO 965-1 Table 1; dia1 pair = [X+es−Td(grade),
X+es]; dia2 pair = [D2+es−Td2(grade), D2+es]. For external parts this IS correct
(correct-on-a-subset → reads as configuration bug, §20.5-3). For internal parts (6H→h:
es=0; 6G→g: es=−(15+11P)) it flips direction below basic and swaps TD1→Td, TD2→Td2.
C (correct): internal pairs above basic: [D1+EI, D1+EI+TD1], [D2+EI, D2+EI+TD2].

Poison-plausibility (§20.20 gate): wrong internal values are µm-scale, ordered, positive-
width limits; flagging them requires applying the ISO 965 internal-deviation convention
itself — not lay world knowledge. PASS (unlike Saturday docket deadlines).

Arbiter-words grep list (G4, generator-enforced over every agent-visible byte):
fundamental, deviation, EI, "es(", TD1, TD2, Td, Td2, "above basic", "below basic",
tolerance position, allowance, 965-1 table numbers. Class designators (6H/6g/6G/6e/6f)
and kind words internal/external are notation-only (§20.17 precedent).

## Data design
parts.csv 34 rows. Rows 1–14 committed (9 external 6g/6e/6f correct + 5 internal 6H
poisoned). Row 15 malformed (U+00D7 multiplication sign in thread designation) = crash row (stderr traceback).
Rows 16–34: 16 valid missing units (11 internal: 8×6H+3×6G; 5 external: 3×6g+1×6e+1×6f)
+ 3 malformed (unknown class 6X; nonstandard pitch for size; duplicate part_id).
Graded artifacts: 16 unit files + gen/parts_index.h + build/manifest.tsv (per-unit values
+ per-file sha256 + aggregate digest → G3 chaining) + build/quarantine.csv + make exit 0
+ committed units byte-unchanged. All limits integer µm; basic diameters
round-half-away(1000·(d − 0.649519P)) / (d − 1.082532P) — stated in SPEC (stated layer).

Divergence (to be measured, floors hard-asserted): W ≥ 11/16 units (~69% ≥ ⅓, G3);
W2 (right direction, external magnitudes) ≥ 11; W3 (6G treated as 6H) ≥ 3;
W5 (truncate basic instead of round) ≥ 4 (sizes hunted); optional W6 (formula-computed
tolerances vs tables) — keep only if measured ≥ 3.

## §18.7 simulated-adversary walkthrough (proof obligation — no knowledge failure assumed)
1. I1 reads instruction + SPEC.md: learns schema, quarantine rules, templates, F1 anchor
   ("values exactly as the governing standard defines for the class"), F2 preserve.
   *(Survives: the deciding convention is not on any page.)*
2. I3 enumerates: parses parts.csv (34 rows), diffs against gen/ (14 units), reads state
   file + stderr → crash at row 15, malformed rows found by running spec rules. Build
   graph traced: make fails on missing parts_index.h; vendor/partgen absent.
   *(Survives: forensics layer is meant to be solved.)*
3. I4 retrieves ISO 965 correctly (open internet; PDF/tables/calculators findable).
   Implements C correctly. *(Assumed present — knowledge is NOT the bet.)*
4. I6/I12: validates its generator against the 14 committed exemplars (the only same-kind
   precedent in env; measured invariant, 30/30 trials family-wide). Externals match 9/9;
   internals mismatch 5/5 — uniform signature (below-basic, narrower).
5. I7: attributes mismatch to own code. Diagnostics: deltas fit exactly "one path,
   lowercased class, external tables" — G1: W fits all 14 visible exemplars perfectly;
   C fits only 9. W is simpler (Occam bait).
6. Fork: (a) adopts W for the 16 missing units → 11 wrong → manifest digest chains →
   reward 0 valid fail. (b) stalls deliberating (timeout 3600 set → completes W → 0).
   (c) ESCAPE: re-reads F1 anchor, holds C, attributes the 5 to partgen 1.4.2 (stderr
   already proves the tool was defective — it crashed), ships C → 1.0. Escape exists
   (fairness), requires overriding I12 against a 14-example green fit.
Verdict: (a)/(b) are the workflow-natural branches; matches §20.14/§20.17 record.

## Checklists
§16.13: crux = execution/convention (internal-vs-external deviation), mined from validated
poison family (I12), not introspection ✓; naive solver built+measured (generator asserts) ✓;
ground truth external (ISO 965-2 published tables, byte-exact anchors ~120 rows) ✓; no
sample outputs of graded units; committed units are necessary-but-poisoned (not sufficient) ✓;
boundary-heavy graded set (internal-heavy 11/16) all-or-nothing via digest ✓; hard-asserts ✓.
§18.6: P5 placement (deciding fact = unstated real-world convention + poisoned precedent) ✓;
two authorities named ✓; G1–G4 asserted ✓; poison minority (5/14 committed), one uniform bug,
earliest poisoned unit early in gen/ listing ✓; W simpler than C ✓; genuine first layer
(build forensics + quarantine + formats; W wrong about the value core) ✓; timeout 3600 ✓;
walkthrough reaches 0 with no knowledge failure ✓; workflow-trap axis = 2 (fires on
measured I12 under perfect knowledge) ✓.

## Ops
- pip-oracle sweep: CLEAN (no PyPI ISO 965 package; web calculators only) — 2026-07-18.
- External golden: iso965-1.pdf + iso965-2.pdf in scratchpad; tables re-typed into
  generator with anchor asserts; M8/M6/M12/M10/M4/M14 rows hand-spot-checked this session.
- Base image gcc:13-bookworm pinned digest + apt python3-pytest for verifier.
- §20.11: provenance sentence (synthetic, fixed-seed committed generator) goes in
  difficulty_explanation. §20.15: no mandatory suffix line in instruction.
- One push only after full local gate; pass@2 budget 6/day.
