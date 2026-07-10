# PROGRESS — dynamo/repair-capture-digest (Revision 2)

**Last updated:** 2026-07-10 (session after pass@2 2/2 failure)
**PR:** https://github.com/handshake-project-dynamo/dynamo-4ad62d4-file-and-media-operations/pull/2
**Local repo:** `~/Work/dynamo-4ad62d4-file-and-media-operations` (branch `submission`, task in `task/`)
**Reference:** `~/Work/dynamo-log-report-task/DYNAMO-REFERENCE.md` (read §16.13 → §17.7 → §17.8 first)

## Where things stand (hard facts)

- Category **File and Media Operations / Recovery and repair**, model Opus-4.8, agent Terminus-2, `allow_internet = true`.
- **Attempt 1 (repair-capture-crc):** disclosed CRC-32/BZIP2 params → R1 FAIL on `essential_difficulty` ("fully-specified, 30–60 min; crcmod one-liner"). → §17.7 Disclosure Test written.
- **Revision 1 (repair-capture-digest):** custom firmware digest, C source + all four integer conventions itemized in-spec, all digests zeroed (total silence). Rubric PASSED, similarity UNIQUE, validation OK — **pass@2 = 2/2 SOLVED** (2026-07-10 ~10:30Z). Both agents read format_spec.md first, wrote flawless wrap32/trunc_div/c_mod helpers, self-validated, finished in 101–163s of 900s. → §17.8 written: *in-spec disclosure of a small custom routine hands the solver a checklist; total silence made the agents MORE careful, not less.*
- **PR state:** labels `in-progress`, `needs-revision`; gate FAILURE (pass2). **Next push = Revision 2 = LAST revision before Holding-Rejection** (max 2 revisions; bonus $80–120 rides on this).
- **pass@2 budget:** capped 6/day/repo; 1 used today (2026-07-10). Never push until local naive-variant gate is green.

## The decided Revision 2 design (mined from the observed-failure library, not invented)

**Failure-library basis:** §11.2's common thread — *"the model stopped checking after the first green result"* (bytecode-vm-debug 77–137s quit; gnss-log-decode 8/8: GPS rules applied to all constellations; tokenizer-recovery; accrued-interest). Both of OUR failed attempts gave the model **zero feedback**, which paradoxically triggered maximum-paranoia careful mode. The delivered stumps all **lull** the model with a green signal that the naive answer satisfies.

**Design: latent-generation digest domains + a confirming-but-insufficient oracle** (§11.4 strategies 2+3, §16.10 split-invariant rule, gnss pattern re-instantiated in file/media):

1. Multi-generation capture container (CAPX v2): records carry a generation/profile byte. Fleet of device generations wrote one file.
2. **Intact records (digest present, correct) exist ONLY for the dominant generation A** — they are the lulling oracle. The agent derives/validates its digest routine against them, sees perfect green, ships.
3. **Graded records (digest zeroed) concentrate in latent generations B/C** whose digest rules differ in spec-determined but never-exemplified ways (digest domain: which fields included; init seeding from header serial; stored vs logical payload byte order; padding exclusion...). The datasheet defines ALL generations fully (unambiguous, fair) — but no worked example beyond gen A, and the instruction never names the crux.
4. Digest routine itself is bland/standard (e.g. zlib CRC-32) — NO porting checklist to hand over (that's what killed Rev 1); all difficulty lives in per-generation domain/parameter rules + composition.
5. Optional agentic substance: a few damaged length fields → boundary reconstruction using intact digests as constraints (feedback covers the OBVIOUS work; graded crux stays silent — §16.10 resolution).
6. All-or-nothing byte-exact grading over the whole repaired file.

**Generator hard-asserts (§17.4 DDD — the falsification test):**
- oracle output == external golden (subprocess), byte-exact.
- EVERY naive variant reproduces ALL intact (sample) records exactly → the lull is real (assert per §11.5 corollary: "all plausible-wrong variants agree with golden on every sample row").
- EVERY naive variant fails ≥N graded records (build ≥4 variants: gen-A-rules-everywhere; missed serial-seed init; stored-not-logical payload domain; padding included; wrong field subset).
- No ground truth / expected file reachable in the agent image.

**§17.2 pre-push score target ≥9/12; §17.5 red-team before push.**

## Why NOT the alternatives (so a relaunch doesn't re-litigate)

- Porting/disclosed-custom-C crux: **exhausted** (§17.8 trilemma: custom→disclosed→executable; real→library/tool→shortcut). Don't retry.
- Familiar-external-standard retrieval-misapplication (the only 0/5-proven lever): needs a standard with NO tool — in file/media with open internet, real formats all have tools (Pillow/zlib/ffmpeg/mutagen/sqlite3/crcmod...). Surveyed and dead.
- Reverse-engineering unknown params (hatch 1): dead both ways (§17.8 #3).
- Custom-ISA emulation breadth: considered; rejected as kitchen-sink + still "implement-the-spec" (essential_difficulty risk, same as CRC fail) + careful agents proven in this family.

## Build checklist (resume here)

- [x] Read §16.13, §17.7, §17.8, §16.10–16.12, §11.2/11.4/11.5, §17.1–17.5
- [x] PR state + pass@2 budget checked
- [x] Design decided (above)
- [ ] Write `generator.py` with golden + ≥4 naive variants + hard-asserts (in task repo, NOT shipped to agent image)
- [ ] Hunt record mix so each naive fails ≥1/3 of graded records AND matches all intact ones
- [ ] Rewrite `task/environment/` (data + Dockerfile), `format_spec.md`/datasheet, `instruction.md` (no crux naming, no checklist), `solution/`, `tests/`
- [ ] task.toml: update description/difficulty_explanation/solution_explanation/verification_explanation
- [ ] Local gate: oracle 1.0, nop 0, EVERY naive variant 0, leak grep
- [ ] §17.2 score ≥9/12 + §17.5 red-team ritual
- [ ] Commit as user (no AI trailers), push `submission` → watch pass@2
- [ ] Update this file + DYNAMO-REFERENCE.md with the outcome (win → new §; loss → escalate via war room per §16.8, evidence trail is clean)

## Build results (2026-07-10)

Generator: `~/Work/dynamo-4ad62d4-file-and-media-operations/generator.py` (seed 0x51C2A7).
File: 60 records (20 sealed gen-1, 40 unsealed graded: 12 gen-1 / 16 gen-2 / 12 gen-3), 6-device table, 6660 bytes.
Rules: gen1 CRC32(type||len||payload) BE; gen2 CRC32(...||pad) stored LITTLE-endian; gen3 CRC32(serial||...) BE; device idx = type>>13; trailer CRC32 over stored digest fields BE.

Naive divergence (each ALSO reproduces all 20 sealed records — lull asserted):
- N1 uniform gen-1 rule: 28/40 wrong  - N2 BE storage everywhere: 16/40
- N3 gen-2 without pad: 12/40         - N4 gen-3 without serial: 12/40
- N5 device idx from low 3 bits: 40/40 (all + trailer in every case)

Local gate: oracle 1.0 ✓, nop 0.0 ✓, N1-as-solver via harbor 0.0 ✓, no leaks ✓.
§17.2 score: 10/12 (execution 2, reasoning-path 1, silence 2, divergence 2, all-or-nothing 2, duplicate-distance 1). §17.5 red-team done — deciding lines nameable (`devices[type>>13]`, per-gen domain/storage), natural validation (sealed records) passes all naives.

**Honest residual risk:** last pass@2's agents read format_spec.md first and implemented every stated rule. If they do that flawlessly again (5 independent slip points this time, no itemized checklist, misleading-green validation), it solves. This is the best library-backed play left in this repo (§17.8 survivors).

## OUTCOME: Revision 2 pass@2 = 2/2 SOLVED (2026-07-10, second run of the day)

Both agents read format_spec.md FIRST and implemented all five rules from the normative
text in ~3-3.5 min (~20% budget). The lull never engaged — one agent used the sealed
records only as a post-hoc assertion. Full analysis in the PR's sticky pass@2 comment.
Lesson recorded as DYNAMO-REFERENCE.md §17.9: the lull only works when green feedback
substitutes for a rule the agent would otherwise have to FIND; it does nothing when the
rule is printed on the page. Three-strike rule: this seed (file/media recovery + open
internet + spec-complete fairness) forces every deciding rule onto the page → every
design is a spec-implementation task → Opus executes it. No §17.2 ≥9/12 design exists.

**User chose the 4th design (algebra-recovery crux). Revision 3 built and pushed
2026-07-10 (commit 766ca3a); pass@2 pending (3rd run of 6 today).**

## Revision 3 design (calibration-constant recovery) — as built

- CAPX v3. Seal mixer STRUCTURE disclosed: `seal = c ⊕ ⊕ᵢ rotl32(S[bᵢ], 11·i mod 32)`
  over type||length||payload. Constants S (256×32b) + c = 8224 unknown bits: unpublished,
  fictional, beyond brute force, outside crcmod/reveng/zlib models.
- Intended path (= reference solution's actual code): mixer is affine over GF(2) →
  recover (S,c) from the 257 sealed records = exactly 8224 equations. Generator
  ADAPTIVELY selects sealed records so the system is square and NONSINGULAR:
  unique determination, ZERO redundancy → no held-out validation possible.
- Key discoveries during build (recorded for future designs):
  1. **Gauge forgiveness:** constant anchor/rotation-offset misreads are absorbed into
     the recovered table (measured 0/40 wrong) — NOT traps. Only family-changing
     misreads (rotation direction, stride value, domain contents) diverge.
  2. **Consistency is a weak oracle:** domain-content misreads (payload-only, pad-included)
     make the square system INCONSISTENT → self-reveal. Rotation-family misreads stay
     full-rank → solve cleanly → silently wrong 40/40 (measured). Square-exactness is
     what keeps them silent (any redundancy would expose them).
- Local gate: oracle 1.0 (recovery-based solver, no knowledge of constants), nop 0.0.
- Honest odds: the bet is (a) recognition — does the agent see the affine-recovery path
  at all (legacy-formatter-clone's GPT-5.4 5/5 fail = tried checksum catalogs instead);
  (b) execution — 8224-unknown bit-level GF(2) pipeline with index bookkeeping, no oracle
  for any intermediate. Opus is strong at both; §17.2 honest score ~8/12. This was pushed
  eyes-open as the user's chosen last design; alternative was war-room escalation.

## Draft war-room escalation (user must post; edit freely)

> Asking for a difficulty-bar / reseed call on my file-and-media-operations task
> (repo dynamo-4ad62d4, PR #2, subcategory "Recovery and repair"). Three consecutive
> designs — all rubric-clean (essential_difficulty PASS on the last two), similarity
> UNIQUE, validation green, five measured naive/near-miss solvers failing 12-40/40
> graded outputs each — were each solved 2/2 at pass@2, with the agents using ≤25% of
> the time budget. The pass@2 analyses (in the PR) show why: in this subcategory,
> fairness/unambiguity forces every deciding rule into the shipped spec, and the
> benchmarked model implements disclosed specs flawlessly regardless of rule count —
> the two levers that have produced 0/5 stumps elsewhere (retrieval-misapplication of
> a familiar real standard; silent latent regimes NOT documented in-repo) structurally
> don't exist in file/media with open internet, because real formats all ship with
> tools/libraries that act as oracles. Is there an accepted path here — e.g., a reseed
> to a convention/porting-friendly subcategory, or guidance on what difficulty shape
> is considered achievable for this seed? I'd rather not burn the remaining revision
> on a fourth design the evidence says will also be solved.

## Session log

- **2026-07-10 (this session):** Post-mortem of pass@2 2/2 done; §17.8 already committed (be73ce7). Decided Revision 2 design (lull + latent generations). Built generator + all task files, local gate green, pushed Revision 2, updated PR body. **Next: watch PR #2 checks (pass@2 re-run; budget was 1/6 used today).** If solved again → escalate via war room per §16.8 with the clean evidence trail; do NOT redesign inside the same crux space.
