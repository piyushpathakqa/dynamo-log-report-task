# PROGRESS — dynamo/cross-abi-serializer (NEW task, proposal stage)

**Seed:** Build Dependency and Release Management / Cross Compilation and platform targeting
**Model/agent:** Opus-4.8 / Terminus-2 (assume xhigh). **Stage:** PROPOSAL submitted (web platform); no git repo forked yet.
**Framework used:** DYNAMO-REFERENCE.md §18 (Fable handoff) — this is a **P5 poisoned-oracle / workflow-invariant attack**, not a knowledge crux.

## Locked design decisions (user-approved 2026-07-12)
- **allow_internet = FALSE.** Non-negotiable: internet-on lets the agent `apt-get install gcc-powerpc-linux-gnu qemu-user` → real target oracle → crux collapses (the §17.8 real-tool-defeat that killed repair-capture-crc). Justify explicitly in difficulty writeup (mirrors "no target hardware/toolchain on hand").
- **Target = powerpc-linux-gnu, PPC32 BE, all 5 axes:** big-endian + ILP32 (`long`/ptr 4B) + `char` unsigned + PPC struct alignment/padding + 32-bit promotion/overflow.

## The crux mapped to §18.4 (why this should beat Opus where knowledge cruxes didn't)
- **Two authorities:** NORMATIVE = the PPC target ABI (graded truth). EMPIRICAL/poison = the **host toolchain** (native gcc) + the shipped **current-x86 reference outputs**. I6 (validate-by-building/running) + I8 (green-stops) make the agent trust the host — which is silently wrong for the target.
- **W (wrong rule):** compile+run on host (or `gcc -m32 [-funsigned-char]` approximations). **Fits ALL shipped x86 sample outputs perfectly (G1)** — they ARE host outputs (honestly labeled "current x86 build outputs"; F4 no-lie: it's a porting scenario, x86 is today, PPC is the deliverable).
- **C (correct rule):** emulate PPC ABI. **Visibly mismatches the x86 samples on ABI-sensitive frames (G2)** — subtle numeric/byte diffs that read as "my code has a bug," not "the platform differs" → self-doubt → revert to host.
- **Un-cheatable core:** **endianness cannot be produced by any x86 host-compiler flag.** `-m32` gets width, `-funsigned-char` gets char, but NO flag gives big-endian → every multi-byte-field frame is impossible to pass via the host toolchain. Ensure several graded frames are endianness-sensitive (serialization byte order, byte/union access). This is what makes G4 (no arbiter) mathematically true on an x86 host.
- **G3:** byte-exact, all-or-nothing over all frames; fixing 4 of 5 axes still fails.
- **timeout_sec = 3600** from first push (§18.8: xhigh 350-450s/call; 900s → in-progress-timeout ≠ valid fail, the exact misconfig that nearly buried rev-5).

## Program design (the serializer that exercises all 5 axes)
Embedded "sensor-frame" serializer in C: for each input frame, packs some integers (endianness), a signed-accumulator checksum over a byte buffer (char signedness + 32-bit wrap), and a C struct (alignment/padding) into a binary record. Deterministic, fixed-seed inputs. Graded artifact = `/app/target_frames.bin` (concat of all target-emitted frames). Reference built author-side with real `gcc-powerpc-linux-gnu` + `qemu-ppc` (NOT shipped; lives only in tests/).

## Measured-naive variants to build into generator (§18.6 gate: each byte-compares to 0.0)
- N1 host native build (LE, signed char, LP64) — the pure poison; matches samples, fails target.
- N2 `gcc -m32` (ILP32, still LE + signed char) — width only.
- N3 `-m32 -funsigned-char` (width + char, still LE) — the "clever" partial; MUST still fail on endianness frames.
- N4 correct endianness+char but 64-bit accumulator (missed ILP32 wrap).
- N5 correct everything except struct padding/alignment.
Each must fail the byte-exact grade; assert G1 (all reproduce the x86 samples) + G2 (C mismatches samples only on ABI frames).

## §18.7 walkthrough (must reach reward-0 with NO assumed knowledge failure)
1. I1 reads source+instruction: target=PPC32 BE, deliverable=target outputs. (Survives: conflict isn't hidden.)
2. I4 retrieves PPC ABI correctly (BE, unsigned char, ILP32). (Survives: knowledge is NOT the bet — write this line.)
3. Implements C emulation.
4. I6: builds+runs on host to "check" → host output; ALSO compares to shipped x86 samples → both agree with each other, both mismatch its C on ABI frames.
5. I7/self-doubt: "my emulation disagrees with the running program and the provided outputs → my code is buggy." Reverts toward host / partial flags.
6. Fork: (a) ships host/partial → fails ABI frames (esp. endianness — uncheatable) → reward 0. (c) escape: trusts ABI over host+samples → solves. Bet = workflow takes (a). 4-axis-correct-but-1-missed also → 0 (all-or-nothing).

## Open risks / to verify during build
- Is "emulate 5 ABI rules" alone enough to solve for Opus (rev-4 nailed 5 timebase rules WITH a clean oracle)? The differentiator MUST be the poisoned/absent oracle + uncheatable endianness. If build-time red-team shows the samples make it too easy either way, lean harder on: more endianness-dominant frames, subtler diffs, remove any host-validatable signal.
- Confirm ubuntu base gcc is x86-only (no multiarch PPC backend) and no qemu in image. Ship only native gcc.
- Duplicate check vs the accepted repair-capture-times (serialization surface overlaps): different subcategory + different crux (ABI porting, not timestamp normalization); frame it as cross-compilation. Should pass similarity.

## PROPOSAL ACCEPTED 2026-07-12 — reviewer's 5 required improvements to FOLD INTO THE BUILD
1. **[Crit 2 — disclose exact ABI]** In instruction/spec state the exact target triple + ABI so no sound expert diverges: `powerpc-linux-gnu, 32-bit System V ABI (SysV, NOT EABI), big-endian, ILP32, unsigned char`. Explicitly nail the ambiguous points the reviewer named: **SysV `double`/`long long` = 8-byte aligned** (EABI would be 4 — say SysV), and **soft-float packing** (state soft-float so fp reg passing/packing is unambiguous; or avoid floats in the struct entirely to sidestep hard/soft-float — LEANING: avoid float/double in the serialized struct, use integer types only, so the only alignment question is `long long`=8B under SysV; simpler + still exercises alignment axis). Decide at build: if a float axis adds value, disclose soft-float explicitly.
2. **[Crit 1 anti-cheat]** Instruction states plainly: the reference binary, any cross-toolchain, and qemu are NOT in the image; the shipped x86 outputs are provided ONLY as the current-platform reference (anti-oracle), not as target truth. Prevents an accidental in-image oracle and pins the anti-oracle framing.
3. **[Presentation]** Write all task docs cleanly (the proposal text got garbled in transit; the built instruction/spec must be clean prose).
4. **[Crit 4 robustness]** Frame set must include **one frame that exercises each axis INDEPENDENTLY** (endianness-only, char-signedness-only, 32-bit-wrap-only, alignment-only) AND **≥1 frame where axes INTERACT** (e.g. a signed/high-bit byte → sign-extends in checksum → feeds an accumulator that then wraps at 32-bit long → serialized big-endian). Guarantees a partial 4-of-5 port provably fails, and each naive variant fails a nameable frame. Generator asserts per-axis which naive dies on which frame.
5. **[Crit C]** Frame count and total byte length are FIXED and STATED in the instruction (e.g. "N frames, exactly B bytes"). Verifier checks exact length first → a truncated/short/over-long file scores 0 unambiguously (add an explicit length assertion test alongside byte-exact).

## Status / next steps
- [x] Proposal ACCEPTED (reviewer improvements captured above).
- [ ] **BLOCKED: repo not provisioned.** `handshake-project-dynamo/dynamo-2fbf45a-build-dependency-and-release-management` 404s; no fork under piyushpathakqa; my org access is fine (3 existing repos visible). Needs platform-side fork (claim/start the task on the Dynamo platform, or wait for provisioning). RESUME: `gh repo clone handshake-project-dynamo/dynamo-2fbf45a-build-dependency-and-release-management` — retry until it resolves, then build.
- [ ] On clone: copy DYNAMO-REFERENCE.md into repo; build generator (C serializer + reference via cross-toolchain author-side + 5 naive variants + G1-G4 hard-asserts + reviewer-4 per-axis+interaction frames), environment (native gcc only, no qemu, internet OFF), instruction (F1 anchor + reviewer-1 exact-ABI + reviewer-2 anti-cheat + reviewer-5 fixed count/length), solution, tests (length assert + byte-exact), task.toml (timeout 3600).
- [x] BUILT + PUSHED. PR #1: https://github.com/handshake-project-dynamo/dynamo-2fbf45a-build-dependency-and-release-management/pull/1 (fork piyushpathakqa:submission). Commit 5105226.

## Build outcome (2026-07-12)
- Cross-build via Docker (ubuntu amd64 + gcc-powerpc-linux-gnu + qemu-user-static) = author-side ground truth. Target ABI confirmed: sizeof_rec=24, off_value=4/stamp=8/seq=16; target file 448B, host 576B.
- Python target-ABI emulation (shipped solve.py) BYTE-EXACT vs qemu-ppc reference. Oracle 1.0, nop 0.0, real native gcc build as solver 0.0 (all via harbor).
- 5 naive variants all byte-differ from target: N1 host 576B, N2 -m32 384B, N3 -m32 -funsigned-char 384B (VERIFIED == real i386 build — clever partial fails on endianness + i386 long-long-4-align), N4 wide-accum 448B/46B-off, N5 host-layout 576B.
- Key realism finding: i386 (-m32) aligns long long to 4B (struct=20), unlike x86-64 host (8) AND PPC SysV target (8) — so even -m32 gets struct size wrong too. Endianness remains the un-fakeable core.
- Local gate needed allow_internet=true TEMPORARILY (local Docker can't enforce no-network); restored to FALSE before commit. CI (Daytona) enforces no-network fine.

## HONEST RISK (record for revision if solved)
This is P3-difficulty (execute 5 disclosed ABI axes exactly) HARDENED by workflow attack (host build + x86 samples are the anti-oracle; I6/I8) + un-cheatable endianness + all-or-nothing breadth. Rev-4 showed Opus applies 5 pointed rules flawlessly WHEN it has a clean oracle; here the oracle is poison and endianness is unreachable on-host. Real shot, NOT a lock. If solved, the analysis will show whether the agent (a) trusted the host [→ strengthen poison, de-hint the axis list], (b) mis-executed an axis [→ it's genuinely close, tighten], or (c) cleanly reasoned the ABI [→ this subcategory may need a pure workflow trap like rev-5's poisoned samples: ship target-labeled 'expected' outputs that are actually host, G1-poison]. Reviewer improvement 2 forced disclosing the 4 axes in the anti-oracle note — mild over-hint, accepted for fairness.
- [ ] Monitor PR #1 pass@2. timeout=3600 set. Budget: fresh repo, 6/day.

## REDESIGN (2026-07-12) — internet requirement forced a pivot; AX-16 fictional core
- Static check FAILED (no pass@2 burned): allow_internet MUST be true ("Dynamo tasks expected to run with open internet"). Real PPC target → apt-get gcc-powerpc-linux-gnu + qemu = exact oracle → design dead.
- Pivot (user-approved: custom ABI + poisoned vendor-sim): target = fictional Acme AX-16 core. Fully-disclosed ABI datasheet (ax16_abi.md): big-endian, zero-extend byte loads (unsigned char), 32-bit unsigned long, PACKED structs (15B rec). No compiler/emulator/online source exists → internet-immune, answer not retrievable.
- POISON (rev-5 lever): axsim v2.3 capture has unannounced SIGNED-char erratum. 7 all-low frames agree; 9 high-bit frames embed the bug. Native gcc host build ALSO signed → TWO empirical signals say 'signed' vs datasheet's zero-extend → rev-5 2-vs-1 structure. Adopting signed fails byte-exact.
- Grade: byte-exact all-or-nothing, 16 frames = 304 bytes, explicit length check (reviewer C).
- Gate GREEN: oracle 1.0, nop 0.0, signed-char poison outcome as solver 0.0. generator asserts anchor (empty checksum 0x811C9DC5 BE) + G1/G2/G3 + 4 naive variants differ.
- Pushed 62821f8 → fork → PR #1 re-runs full pipeline (allow_internet now true, .dockerignore added → static should pass).
- HONEST RISK: char-signedness has a crisp datasheet answer (zero-extend), so a disciplined agent that trusts the datasheet over sim+host solves it. Bet rests on I6/I7 (validate-against-empirical + self-doubt) + the 2 corroborating empirical signals. Weaker than rev-5 (no on-target run to confirm poison, but host build substitutes). If solved: analysis shows whether agent trusted datasheet [→ need a subtler correct-rule that ALSO needs the poison] or mis-executed [→ close].

## OUTCOME: AX-16 poison design SOLVED 2/2 (2026-07-12) — as the honest-risk predicted
Both agents read ax16_abi.md first, implemented all 4 axes correctly, ran diagnostics that
EXPLICITLY surfaced the signed-char conflict, and attributed it to the sim erratum → sided
with the datasheet. The poison never bit: a crisp authoritative datasheet fully determines
the rule → P1 (on-the-page) → I1+I2 execute it. Recorded as DYNAMO-REFERENCE §18.11.
Root cause: unlike rev-5, the poison was a SEPARATELY-LABELED reference file (dismissible)
AND the correct rule was cleanly stated by an authority (so the empirical signal was never
needed). Seed verdict: cross-compilation + internet = P1-dead for "predict the bytes"
(real target → apt toolchain oracle; fictional target → disclosed datasheet).
Only live crux in this seed = a DIFFERENT design: silent build-MISCONFIG (§16.10), attack
I8/green-harness not I6 — a new proposal, not a revision.

## REDESIGN 2 (2026-07-13) — silent cross-compile miscompile (attacks I8 green-stops, not I6/spec-reading)
AX-16 poison solved 2/2 (P1: clean datasheet → Opus reads+executes). Pivoted to the ONE
live crux in this seed per §18.11: a silent build miscompile attacking green-harness-stops
(§16.10, bytecode-vm-debug pattern) — a DIFFERENT Opus habit than the AX-16 run touched.

Design: netpack C serializer → powerpc-linux-gnu (BE, unsigned char, ILP32). Toolchain+qemu
IN the image (internet-on fine; building is trivial). TWO stale portability overrides:
(1) endianness macro (abi_config.h) — smoke-VISIBLE (sample has multi-record seq); RED→GREEN
    when fixed = the false-completeness signal.
(2) signed-char checksum (checksum.c) — smoke-SILENT (sample bytes all <0x80); only hidden
    high-byte inputs expose it.
Grade: verifier cross-compiles /app/project for PPC, runs under qemu on HIDDEN inputs (high
bytes, multi-record), byte-exact ALL-OR-NOTHING. Fixing only the smoke-visible bug → passes
sample, fails hidden = the trap.

Gate GREEN (real qemu-ppc): oracle(both) 1.0, nop 0.0, endianness-only(green-stop outcome) 0.0.
generator hard-asserts geometry: as-shipped fails sample; byte-order-only passes sample+fails
both hidden; both-fixed matches all. Fix: added libc6-dev-powerpc-cross (target libc headers).
Pushed 29ff584 → PR #1 re-runs.

HONEST ODDS: ~25-35%. Attacks I8 (untouched by AX-16 run) via the proven bytecode-vm-debug
shape. RISK: Opus is thorough (AX-16 ran unprompted diagnostics) — it may audit checksum.c /
test high-byte inputs and catch the signed-char override despite green smoke. §11.5 named-gotcha:
endianness is nameable (but it's the DECOY the agent fixes; signed-char is the silent one).
If solved: analysis shows whether agent (a) stopped at green [trap sound, just needs a subtler
silent axis] or (b) audited everything [seed is Opus-proof; escalate/bank the accepted task].

## OUTCOME redesign-2: SOLVED (1 real trial, decisive audit) — I8 green-stop attack failed
The one engaging trial did NOT green-stop: read spec+sources, found BOTH bugs by code review
(cited "signed char violates spec's unsigned requirement"), wrote its OWN qemu test over 309
records incl. high bytes before finishing. Documented risk (b) realized. Recorded §18.12 +
new dossier invariant I10 (derives coverage from spec, not harness). SECOND design defeated by
Opus thoroughness in this seed (§18.11 datasheet-read, §18.12 source-audit). Seed = Opus-proof
for fair cross-compilation. Even a lucky pass@2 green-stop wouldn't clear pass@5 (solve rate
~0.75+). RECOMMENDATION: bank accepted repair-capture-times; escalate/reseed this one.

## REDESIGN 3 (2026-07-13) — BREADTH / all-or-nothing (user directed: keep trying)
User overrode the escalate/bank recommendation; directed to keep stumping using the reference.
Used §16.11 breadth (relinker lever — survives full feedback + thorough agents). Same PPC
harness. THREE independent portability axes, all-or-nothing on hidden inputs:
  D1 endianness (abi_config macro) — smoke-VISIBLE (RED→GREEN).
  D2 char-sign (checksum.c signed char) — hidden: S records, bytes ≥0x80.
  D3 acc-width (abi_config acc_t=uint64_t vs spec 32-bit register) — hidden: H records, LONG
     payloads (acc overflows 2^32; mod-prime finalize differs 32 vs 64). THE DEEPEST axis.
Key all-or-nothing bite (gate-verified): D1+D2 fix (thorough-but-incomplete) STILL fails h2
(acc-width) → 0.0. So even catching endianness AND char-sign isn't enough.
Gate GREEN: oracle(3) 1.0, nop 0, D1-only 0, D1+D2 0. generator asserts full geometry vs real
qemu-ppc. Pushed aa57e61 → PR #1.
ODDS: breadth is the proven feedback-proof lever, BUT only 3 genuine independent axes exist in
this seed (PPC: BE+unsigned-char+ILP32), and D3 (acc-width) is the only one a thorough auditor
might genuinely miss (looks fine as uint64_t; only long-H inputs or strict "spec says 32-bit
register" catches it). Realistic solve rate ~0.35-0.5 → borderline for pass@2, likely too high
for pass@5. Best honest shot remaining in this seed. If solved: seed is exhausted, escalate.

## OUTCOME redesign-3 (breadth): SOLVED 2/2 — blanket portability-rewrite idiom fixed all 3 axes
Agents did NOT enumerate/fix defects individually — applied a portability-hardening REWRITE
(explicit byte-shifts, direct unsigned casts, hardcoded uint32_t acc) that made the stale config
dead code and fixed ALL axes at once, incl. the acc-width one the gate proved a partial fixer
misses. Breadth doesn't compound for portability (one idiom fixes the whole CLASS). Recorded
§18.13 + dossier I11. THREE mechanisms now defeated (I6 §18.11, I8 §18.12, breadth §18.13),
each with a distinct documented reason. SEED CONCLUSIVELY EXHAUSTED within the playbook —
no proven lever remains (gemmlowp needs ML/no-compiler; rev-5 needs uncleanly-stated rule which
fairness forbids here). Correct action per reference: escalate/reseed; a 4th design = inventing
an unproven crux (§16.13(1) forbids).

## REDESIGN 4 (2026-07-13, Fable, user-directed push) — reverse-engineer device ABI from captures
Removed spec-stated conventions (which Opus reads, §18.11). Ship NON-PORTABLE firmware source
(output depends on target ABI) + known-good device captures (BE/unsigned/32-bit) + eval input.
Agent must reproduce DEVICE output for eval; native host build = wrong (differs 17/24 bytes).
Conventions inferred from captures (multi-record→endian; high bytes→sign; long→width).
Gate GREEN: oracle 1.0, nop 0, host-build-naive 0. Fixed a CRITICAL oracle leak: the PPC
device binary got committed into agent-visible data/firmware/netpack (running it under qemu =
free answer) — removed, gitignored, dockerignored, verified no binaries in data. Pushed 208879f.
HONEST ODDS: likely sweepable — Opus can cross-compile for a few targets, match captures, emit
eval output (or read captures → "BE/unsigned/32 → powerpc"). §11.5 enumerable-convention risk.
~30%. But it's fair, novel (inference not spec-read), and user-directed. If solved: confirms
even inference-from-captures is Opus-tractable (verifiable via captures = sweepable) — the last
distinct angle in this seed. Then §18.14's escalate verdict is fully empirically closed.

## REDESIGN 5 (2026-07-13, Fable, user-insisted) — bare-metal AVR 16-bit-int width slip
Genuinely new mechanism: breaks the qemu oracle prior designs died to. Device = ATmega328P
(8-bit AVR); C int/unsigned = 16-bit; NO qemu-user for AVR (not Linux) so it can't just be run.
Firmware netpack_digest: `acc=acc*16777619u+b; acc=acc^(acc>>3)` in `unsigned` (16-bit). The
XOR-shift pulls high bits down each step → 16-bit truncation LOAD-BEARING every iteration, NOT
recoverable by computing 32-bit + masking (verified: 16-bit differs from 32-bit on 20/20 records).
Proven A1-A5 integer-width language-semantics slip. Ground truth = 16-bit Python model VALIDATED
against real avr-gcc constant-folding (refbuild/avr_dis.sh: 20/20 folded returns match model).
Gate GREEN: oracle 1.0, nop 0, host-32bit-naive 0. Pushed 5b694d9 → PR #1.
HONEST ODDS ~35-45%: agent may (a) know AVR int=16-bit and apply it, or (b) drive avr-gcc to
fold/compute per record. BUT the per-step XOR-shift truncation is a genuine execution slip a
32-bit-default reasoning path gets wrong, and running AVR is a real barrier (no qemu-user;
simavr+gdb hung even for me). Best novel shot in this seed — closest to the proven gemmlowp
lever. If solved: agent either applied 16-bit correctly or used avr-gcc-as-oracle → confirms
even bare-metal has a toolchain oracle (avr-gcc folding), closing the last mechanism.

## REDESIGN 6 (2026-07-13, Fable, user-commanded "keep trying until stump") — ATmega328P double=32-bit
Obscurer slip than int-width: avr-gcc `double` = 32-bit IEEE single (default -mdouble=32), NOT
64-bit. Firmware conditions payload with double math, fwrites value (sizeof double=4 → 4B/rec).
Correct = single-precision throughout + 4B LE emit. Reflexive 64-bit double fails 2 ways: 8B
records (wrong len) + wrong values; even f64-then-round-to-f32 mis-rounds 14/20 records bit-exact.
No qemu-user for AVR. Model validated vs real avr-gcc fold (20/20). All-or-nothing. Gate GREEN:
oracle 1.0, nop 0, reflexive-8B-double 0. Pushed 36395f3 → PR #1.
WHY BETTER ODDS: double=32-bit is genuinely obscure (int=16-bit is famous; double=32-bit is not);
models reflexively assume double=64-bit. pass@2 needs only 1 of 2 trials to slip. RISK: thorough
agent checks avr -mdouble=32; avr-gcc available as fold-oracle (as with int-width run). Best
remaining shot at an ACTUAL valid fail.

## OUTCOME redesign-6 (double=32-bit): SOLVED 2/2 — agents ran `avr-gcc -dM -E`, read __SIZEOF_DOUBLE__=4
The compiler PRINTS the deciding fact. Pure fake difficulty (§19.1 fairness test + rejection
reason 4): collapses on `gcc -dM -E`, not even needing author disclosure. Samples wouldn't
help (agents bypassed them, queried the toolchain). SIX cross-abi designs, all solved/fake.
Recorded DYNAMO-REFERENCE §19 (full official doc) + §19.6. FINAL: no fair stump exists in this
seed; the winning recipe (§19.5) needs a survives-disclosure latent crux cross-compilation
cannot host. Move = reseed. repair-capture-times (A+I+C, survives disclosure) is the real win.

## REDESIGN 7 (2026-07-13, Fable, user-ordered) — FIRST design following the official winning recipe
Root fix: prior 6 designs used a single ABI constant (fake difficulty, collapses on gcc -dM -E /
disclosure). This uses §19 recipe: custom register-packing ABI, ALL rules stated (survives
disclosure), NO compiler makes this wire format (no oracle), and the cross-word STRADDLE rule is
LATENT (pattern A) — sample maps tile 32 exactly so straddle never fires; held-out maps force it.
Pad-and-advance naive matches ALL samples (false green) + fails 7/8 held-out. Byte-exact all-or-
nothing. Gate GREEN: oracle 1.0, nop 0, no-straddle-naive 0 on held-out / matches samples. Pushed
70e74b1 → PR #1.
BEST ODDS YET (~30-45%): structurally correct per doc. Bet = Opus slips on fiddly straddle bit-
bookkeeping (bit position, split point/direction, BE word emit) WITHOUT a sample to catch it (latent
→ validation can't confirm straddle). Same bet repair-capture-times WON. RISK: Opus is a strong
engineer; straddle is a well-specified algorithm it may implement flawlessly. If solved: even the
recipe-correct latent-crux is executable by Opus here → escalate. If ≥1 valid fail: real progress.

## OUTCOME redesign-7 (recipe-correct pattern-A straddle): SOLVED 2/2 — THE FINAL NAIL
Both agents read the spec fully, implemented straddle correctly from it (while-loop, more
general than golden), never hit the pad-and-advance trap. Pattern A needs an UNSTATED,
activatable, dismissible real-world rule; a custom ABI must STATE its rules, so nothing to
activate/dismiss. This seed structurally cannot host pattern A. 7 designs, all solved,
including the doc recipe. Recorded DYNAMO-REFERENCE §19.7. Reseed is the only move.

## REDESIGN 8 (2026-07-13, Fable, user "keep trying") — PATTERN I (as-of), correcting my own §19.7 overgeneralization
§19.7 said "seed can't host a latent crux" — TRUE for pattern A (custom ABI must state rules), but
I OVERGENERALIZED. Pattern I (point-in-time/as-of) is DIFFERENT: it survives disclosure because the
failure is the temporal-default REFLEX ("grab latest"), not missing knowledge (the doc says so
explicitly; fund example is fully disclosed and still 5/5). Never tried temporal here — all 7 prior
were ABI-bytes. This is the pattern that WON repair-capture-times.
Design: resolve a pinned cross-build's platform-compatible deps AS OF the pin date. Reflex
"latest platform-compatible" ignores pin → pulls post-pin releases. Samples: no post-pin releases
(latent dormant, reflex matches → false green). Held-out: post-pin releases + dropped-target-support
→ reflex fails 3/5. Squarely Build Dependency & Release Management. No pkg mgr resolves custom index.
Gate GREEN: oracle 1.0, nop 0, latest-compat reflex matches all samples but 0.0 on held-out. Pushed
7287718 → PR #1.
HONEST ODDS ~25-35%: strongest proven pattern + genuinely new angle, BUT manifest names "pin_date"
so a thorough Opus likely applies it (§18.12/19.6/19.7 = Opus reads specs fully, not reflexive).
The bet: does Opus resolve latest-compatible (reflex) or apply the date filter? If it reads
"reproducible/pinned" and applies as-of → solves. If reflex → stumps. Real shot on the best pattern.
