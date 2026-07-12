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
