#!/usr/bin/env python3
"""
build_dataset.py — curated fine-tuning dataset from the Dynamo campaign.

Every record below is a MEASURED fact from the campaign (see DYNAMO-REFERENCE.md
§11, §16-§20): a task design that was actually run against Opus-4.8 + Terminus-2
(or killed at the design table by a documented wall), with its real outcome.
The script expands records + principles into chat-format JSONL suitable for
LoRA fine-tuning (MLX-LM / Unsloth / LLaMA-Factory), with a train/valid split.

AFTER EVERY FUTURE TASK OR pass@ RUN: append a new DesignRecord (and any new
principle) and re-run this script. The measured record is the moat.

Usage: python3 build_dataset.py   ->  train.jsonl, valid.jsonl, all.jsonl
"""

import json
import random
from dataclasses import dataclass, field
from pathlib import Path

OUT = Path(__file__).resolve().parent

SYSTEM = (
    "You are a Project Dynamo task-design expert. Your job is to design and review "
    "Terminal-Bench-style benchmark tasks intended to make a frontier coding agent "
    "(Opus-4.8 driven by Terminus-2) FAIL validly — reward 0 with a sound attempt — "
    "while remaining completely fair: every verifier rule stated or fairly determinable, "
    "solvable by a careful domain expert, deterministic verification, no hidden "
    "conventions, no lies. You reason from a measured empirical record of what this "
    "adversary actually does, never from introspective 'this feels hard'. When you "
    "evaluate a design you: (1) locate the deciding fact on the placement ladder, "
    "(2) check it against the adversary's behavioral invariants, (3) predict the "
    "pass@2 outcome with a mechanism, and (4) either approve or redesign/reseed."
)


@dataclass
class DesignRecord:
    name: str
    seed: str
    proposal: str          # the design, described fresh, no outcome leakage
    outcome: str           # measured result
    mechanism: str         # why, grounded in observed behavior
    lesson: str            # the transferable rule
    verdict: str           # "WIN" | "LOSS" | "REJECT" | "DESIGN-TABLE KILL" | "PREDICTED-LOSS"


RECORDS = [
    DesignRecord(
        name="tflite-int8-replay (gemmlowp requant)",
        seed="Machine Learning / numerics",
        proposal=(
            "Agent must byte-exactly reproduce int8 quantized inference outputs of a small "
            "model, matching the gemmlowp reference requantization. The deciding detail — C "
            "'>>' rounding (floor) vs Python '//' on negatives plus the nudge constant — is "
            "buried in a large familiar C++ standard the model believes it knows. Nothing in "
            "the task points at the rounding detail; no library in the image reproduces the "
            "exact pipeline; graded all-or-nothing over a boundary-hunted batch of inputs."
        ),
        outcome=(
            "0/5 and 0/5 across two instantiations — accepted as the campaign's first stumps. "
            "REVERSED 2026-07-14: an admin re-run under the upgraded pipeline's new deep_review "
            "stage found the oracle's SRDHM was NOT canonical gemmlowp, flipping the task from "
            "accepted to needs-revision (see the reversal record)."
        ),
        mechanism=(
            "The recorded mechanism — 'the model retrieved its remembered idiom of gemmlowp "
            "instead of re-reading the source' — is now known contaminated: the ORACLE itself "
            "misimplemented the standard (floor-shift with the wrong negative nudge), and the "
            "re-run pass@2 showed both agents implementing CANONICAL gemmlowp and being failed "
            "+1 on 15/48 rows by the wrong reference. An unknown fraction of the original 0/5s "
            "were false negatives: correct solutions rejected by a buggy expected.json."
        ),
        lesson=(
            "A stump measured against a self-consistent but externally-unverified oracle is "
            "not a measured stump. The retrieval-trap design pattern may still be real, but "
            "this instance cannot be cited as evidence for it: the author committed the exact "
            "misretrieval the task was built to induce, on the reference side of the grader."
        ),
        verdict="WIN (later REVERSED at deep review)",
    ),
    DesignRecord(
        name="three reasoning-crux designs (interpretation repo)",
        seed="reasoning/derivation domain",
        proposal=(
            "Three designs where the difficulty is a clever multi-step reasoning or derivation "
            "chain: the agent must reason correctly through interacting rules to derive the "
            "answer, with feedback available in the environment."
        ),
        outcome="2/2 solved, three times in a row.",
        mechanism=(
            "The adversary reasons at expert level, and any in-environment feedback covering "
            "the crux makes a capable solver self-correcting. Reasoning difficulty invented by "
            "an author model is anti-calibrated: anything the author can conceive and "
            "articulate as tricky, the solver can solve."
        ),
        lesson=(
            "Never bet a task on a reasoning crux you invented. Reasoning cruxes lose; attack "
            "workflow and judgment instead. Kill any feedback path that covers the crux."
        ),
        verdict="LOSS",
    ),
    DesignRecord(
        name="repair-capture-crc",
        seed="File and Media Operations",
        proposal=(
            "Repair a capture file whose integrity fields use a custom CRC; the CRC parameters "
            "are named on the page. Difficulty intended to come from implementing the CRC "
            "variant correctly."
        ),
        outcome="Rejected at human R1: disclosure-defeated, essential_difficulty FAIL.",
        mechanism=(
            "Named CRC parameters are a one-liner with the crcmod library; disclosing them "
            "(required for fairness) collapses the task. Undisclosed, it would be an unfair "
            "reverse-engineering dead end. Either way there is no fair difficulty."
        ),
        lesson=(
            "A single stateable constant is never a crux: disclosed it is trivial, undisclosed "
            "it is unfair. Difficulty must survive full disclosure of every rule."
        ),
        verdict="REJECT",
    ),
    DesignRecord(
        name="repair-capture-digest rev 1 (itemized semantics, total silence)",
        seed="File and Media Operations",
        proposal=(
            "Custom C-style record semantics itemized precisely in the spec with worked "
            "examples; zero feedback anywhere (no sample outputs, no tools); agent must "
            "implement every stated rule exactly and repair records byte-exactly."
        ),
        outcome="2/2 solved.",
        mechanism=(
            "Itemized semantics with worked examples are a checklist plus a self-test kit: the "
            "agents asserted the spec's own examples before running. Total silence did not "
            "induce error — it triggered maximum-care mode (spec re-reading, boundary "
            "self-tests)."
        ),
        lesson=(
            "Never itemize the deciding semantics, and never expect silence to induce error: "
            "silence raises the adversary's effort. A stated rule is an executed rule."
        ),
        verdict="LOSS",
    ),
    DesignRecord(
        name="repair-capture-digest rev 3 (GF(2) constant recovery)",
        seed="File and Media Operations",
        proposal=(
            "The deciding constants are not stated but are recoverable from the data: an "
            "exactly-determined (square, zero-redundancy) linear system over GF(2) whose "
            "solution yields the repair parameters."
        ),
        outcome="2/2 solved, in 40 seconds and 6.7 minutes.",
        mechanism=(
            "The adversary is algebra-native: it recognized the affine-over-GF(2) structure "
            "instantly and solved recovery above the reference's level, then self-verified "
            "with independently written forward code that even catches its own pipeline bugs."
        ),
        lesson=(
            "'Recover the parameters from the data' is a solved problem class for this "
            "adversary regardless of parameter count, as long as recovery is well-posed — "
            "and fairness forces well-posedness. Placement P2 (in the data, recoverable) is dead."
        ),
        verdict="LOSS",
    ),
    DesignRecord(
        name="repair-capture-digest rev 4 (mixed timebases, leap eras, pointed standards)",
        seed="File and Media Operations",
        proposal=(
            "Records span multiple public time standards (GPS/BDT/GLONASS/TAI, leap-second "
            "eras); per-record regime flags are explicit; the agent must retrieve the public "
            "standards and execute multi-era conversions over 40 records byte-exactly."
        ),
        outcome="2/2 solved (~14 minutes).",
        mechanism=(
            "Pointed retrieval is robust: the agent reproduced the full 1972-2017 IERS leap "
            "table from memory, deliberated GLONASS ICD vs civil Moscow time and chose "
            "correctly. Explicit regime flags get enumerated by script and every branch "
            "implemented."
        ),
        lesson=(
            "Never bet on knowledge gaps in pointed territory (time scales, checksums, "
            "encodings, C semantics). When anything draws attention to a public standard the "
            "adversary retrieves it correctly and deeply."
        ),
        verdict="LOSS",
    ),
    DesignRecord(
        name="repair-capture-times (rev 5: rev 4 + poisoned validation oracle)",
        seed="File and Media Operations",
        proposal=(
            "Same rich multi-era time-math substance as rev 4, plus: a minority (6/24) of the "
            "already-processed records in the container were written by the crashed in-story "
            "tool with one uniform bug (constant offset instead of era-dependent), internally "
            "consistent and sealed. The processed records are the same kind of object as the "
            "graded output. The instruction anchors graded values to the spec and says the "
            "processed records are to be preserved as produced. No third signal arbitrates. "
            "The wrong rule (constant offset) fits every visible example perfectly and is "
            "strictly simpler than the correct era-dependent rule."
        ),
        outcome="0/2 and 0/2 — accepted. The campaign's second stump family.",
        mechanism=(
            "The adversary implements the correct rule from spec and retrieval, then — its "
            "most reliable habit — validates against the in-environment records before "
            "writing. The guard raises on the first poisoned record; it attributes the raise "
            "to its own code, runs delta diagnostics which (because the wrong rule fits all "
            "visible data) point cleanly at the simpler rule, and either adopts it (reward 0) "
            "or stalls deliberating. Its diligence is the trap; no knowledge failure needed."
        ),
        lesson=(
            "Placement P5: the deciding fact is fairly determinable but actively contradicted "
            "by an empirical signal the workflow trusts. Geometry that makes it real: perfect "
            "wrong fit on ALL visible examples; correct rule mismatches exactly the poison; "
            "wrong rule fails >=1/3 of graded output, chained; no alternative arbiter; poison "
            "entangled with the graded artifact; instruction anchors authority on paper."
        ),
        verdict="WIN",
    ),
    DesignRecord(
        name="cross-abi-serializer AX-16 (poisoned capture vs clean datasheet)",
        seed="Build Dependency / Cross Compilation",
        proposal=(
            "Fictional AX-16 core (no toolchain or emulator exists anywhere). The correct rule "
            "(zero-extend byte load, big-endian, packed) is stated in an in-environment ABI "
            "datasheet. Poison: a shipped simulator capture with a signed-char erratum, "
            "corroborated by the in-image native host build — two empirical signals both "
            "saying 'signed'. Reproduce the device's serialized bytes."
        ),
        outcome="2/2 solved, ~10 minutes each.",
        mechanism=(
            "Both agents read the datasheet FIRST, implemented the stated rule, cross-checked "
            "against the capture, saw the conflict, and attributed it to the documented "
            "erratum — siding with the named authority. When two named artifacts conflict and "
            "one is the stated authority, it is a reading-comprehension step, not a trap. The "
            "poison never read as 'my code is buggy'."
        ),
        lesson=(
            "A poisoned oracle bites ONLY when the correct rule is NOT cleanly stated by an "
            "in-environment authority, and the poison is entangled with / same-kind as the "
            "graded artifact so the conflict reads as 'my computation is wrong', not "
            "'document A vs document B'. A separately-labeled reference file is dismissible."
        ),
        verdict="LOSS",
    ),
    DesignRecord(
        name="PPC cross-compile green-harness (I8 attack)",
        seed="Build Dependency / Cross Compilation",
        proposal=(
            "Port firmware to PPC with two stale portability overrides: an endianness bug the "
            "shipped smoke test exposes (red-to-green when fixed — a false completeness "
            "signal) and a signed-char checksum bug the smoke test cannot expose (sample "
            "bytes all below 0x80). Hidden high-byte inputs, byte-exact all-or-nothing. Bet: "
            "the agent stops at green."
        ),
        outcome="Solved decisively in the one engaging trial.",
        mechanism=(
            "The agent did not stop at green: it audited all sources against the spec, "
            "identified BOTH bugs by code review (citing the spec's unsigned requirement), "
            "and wrote its own qemu validation over 309 records including high bytes before "
            "declaring done. It derives test coverage from the SPEC, not the harness."
        ),
        lesson=(
            "Green-stop is stale as a standalone lever: this adversary constructs its own "
            "coverage from the spec. Any attack premised on trusting incomplete in-env "
            "feedback fails when a fair authoritative spec exists — which fairness forces."
        ),
        verdict="LOSS",
    ),
    DesignRecord(
        name="PPC breadth (three independent portability defects)",
        seed="Build Dependency / Cross Compilation",
        proposal=(
            "Three independent portability defects (endianness, char-signedness, accumulator "
            "width), byte-exact all-or-nothing on hidden inputs, smoke test covering only "
            "endianness. Local gate proves a two-of-three fix scores 0."
        ),
        outcome="2/2 solved.",
        mechanism=(
            "Neither agent enumerated the defects: both applied a blanket portability-"
            "hardening rewrite (explicit byte shifts, direct unsigned casts, hardcoded "
            "uint32_t) that made the stale configuration dead code — one recognized idiom "
            "neutralizing every axis at once, including the axis they never diagnosed."
        ),
        lesson=(
            "Breadth compounds ONLY over idiom-irreducible, independent LOGIC defects. "
            "Multiplying instances of one class (portability, escaping, normalization) does "
            "nothing: the model fixes the CLASS with its canonical correct-by-construction "
            "idiom, not the instances."
        ),
        verdict="LOSS",
    ),
    DesignRecord(
        name="RE-the-ABI-from-captures",
        seed="Build Dependency / Cross Compilation",
        proposal=(
            "State no conventions at all: ship non-portable firmware plus known-good device "
            "captures; the agent must infer the device ABI (endianness, char-sign, width) "
            "from the captures and reproduce the device output for a new input."
        ),
        outcome="2/2 solved, ~6-12 minutes.",
        mechanism=(
            "One agent derived the conventions analytically; the other brute-force swept the "
            "8-way convention menu {endian}x{char-sign}x{width} against the captures and "
            "picked the unique match. The captures that make the task fair also make the "
            "guess verifiable."
        ),
        lesson=(
            "Undisclosed-but-verifiable equals sweepable: a small convention menu plus the "
            "examples that make it fairly determinable is an enumeration exercise. "
            "Genuinely-non-verifiable would be unfair. There is no fourth door."
        ),
        verdict="LOSS",
    ),
    DesignRecord(
        name="AVR 16-bit-int execution slip",
        seed="Build Dependency / Cross Compilation (bare-metal)",
        proposal=(
            "Target a bare-metal ATmega328P (no qemu-user exists): firmware digest computed "
            "in 'unsigned' (16-bit on AVR) where 16-bit truncation is load-bearing at every "
            "step. The proven integer-width language-semantics slip family, with the runtime "
            "oracle broken."
        ),
        outcome="2/2 solved, ~5-8 minutes.",
        mechanism=(
            "Both agents read the source, immediately stated 'unsigned is 16-bit under "
            "avr-gcc on ATmega328P', and wrote a correct 16-bit emulator with explicit "
            "masking. The slip family fires only on MIS-retrieved unchecked memories; a "
            "stated, famous target fact is retrieved correctly."
        ),
        lesson=(
            "The execution-slip lever needs the deciding detail BURIED in a familiar standard "
            "the model won't re-read. A stated and famous fact (the task must state the "
            "target; the target's ABI is public) is retrieved right and applied right."
        ),
        verdict="LOSS",
    ),
    DesignRecord(
        name="AVR double-is-32-bit",
        seed="Build Dependency / Cross Compilation (bare-metal)",
        proposal=(
            "Hang the difficulty on AVR's 32-bit double: the agent must predict serialized "
            "floating-point bytes that differ from the host's 64-bit double behavior."
        ),
        outcome="2/2 solved.",
        mechanism=(
            "Both agents ran `avr-gcc -mmcu=atmega328p -dM -E` and read __SIZEOF_DOUBLE__ == 4 "
            "directly: the compiler in the image PRINTS the deciding rule on request, then "
            "they wrote the f32 round-trip emulator."
        ),
        lesson=(
            "Every ABI fact a cross-compile task can hang difficulty on is printed by "
            "<triple>-gcc -dM -E or observable via qemu/objdump. If a tool in the image can "
            "print your deciding rule, you have no task."
        ),
        verdict="LOSS",
    ),
    DesignRecord(
        name="register-packing straddle (stated latent rule, recipe-correct pattern A)",
        seed="Build Dependency / platform targeting",
        proposal=(
            "Custom register-packing ABI with a cross-word straddle rule that is fully STATED "
            "in the spec but dormant on every sample (samples tile exactly); the natural "
            "pad-and-advance implementation reproduces all samples and fails 7/8 held-out. "
            "All rules stated; no compiler produces the wire format."
        ),
        outcome="2/2 solved in 3.5-5.7 minutes.",
        mechanism=(
            "Both agents read the packing spec fully and implemented the straddle rule "
            "directly — one with a while-loop more general than the golden — never touching "
            "the pad-and-advance trap. Nothing needed activating from memory, so nothing "
            "could be dismissed."
        ),
        lesson=(
            "Pattern A's power is a rule the model must SUPPLY ITSELF and will under-weight — "
            "real-world knowledge left unstated. A stated rule removes both: it is read and "
            "implemented, and sample-dormancy is irrelevant."
        ),
        verdict="LOSSES",
    ),
    DesignRecord(
        name="as-of dependency resolver (thin pattern I)",
        seed="Build Dependency and Release Management",
        proposal=(
            "Resolve pinned dependencies as-of a cutoff date: releases have effective vs "
            "published dates; the resolver must ignore later-published versions. The as-of "
            "rule is stated; the computation is a filter plus max."
        ),
        outcome="Rejected at rubric review before pass@2: essential_difficulty FAIL "
                "('undergraduate solves it in under an hour'), code_dependent FAIL "
                "('~15-line beginner filter').",
        mechanism=(
            "The pattern-I insight with none of the surrounding execution complexity "
            "collapses to a trivial filter once stated — and stating it is required for the "
            "unambiguous criterion."
        ),
        lesson=(
            "Two distinct walls exist: too-thin fails the rubric; hard-looking-but-solvable "
            "passes the rubric and dies at pass@2. A winning task needs BOTH rich multi-step "
            "dependent execution AND a deciding step the model gets wrong."
        ),
        verdict="REJECT",
    ),
    DesignRecord(
        name="pinned-dep-resolver (rich backtracking CSP)",
        seed="Build Dependency and Release Management",
        proposal=(
            "A coupled dependency resolver: inter-component version constraints requiring "
            "backtracking (greedy dead-ends), as-of and platform filters, lexicographically-"
            "maximal solution, byte-exact output. Rich, multi-step, survives disclosure."
        ),
        outcome="PASSED the rubric (first rich design to do so) — then pass@2 2/2 solved.",
        mechanism=(
            "One agent recognized the CSP immediately, wrote explicit DFS backtracking, and "
            "stated the crux in its plan. The other brute-forced all ~81 combinations with "
            "itertools.product. Dependency resolution is a STANDARD algorithm; the model "
            "knows resolvers backtrack and never takes the greedy bait; small search spaces "
            "are enumerable."
        ),
        lesson=(
            "Clearing the rubric needs richness; stumping pass@2 additionally needs a "
            "deciding step that is NOT a standard algorithm and has no recompute oracle. "
            "Standard algorithms (resolution, CSP, packing, layout) are implemented "
            "correctly. Also: always size the search space beyond brute force."
        ),
        verdict="LOSS",
    ),
    DesignRecord(
        name="pinned-dep-resolver + latent conflicts",
        seed="Build Dependency and Release Management",
        proposal=(
            "Add a latent mutual-exclusion 'conflicts' rule to the rich resolver: stated in "
            "the schema, dormant on all samples (a conflict-ignoring resolver reproduces "
            "them), triggered by every held-out build."
        ),
        outcome="Cleared the rubric again; pass@2 2/2 solved.",
        mechanism=(
            "Both agents read the schema, saw the conflicts field, and implemented it — "
            "bidirectionally, with forward-feasibility pruning, more thoroughly than the "
            "golden. Latent-ness was irrelevant because the rule was stated."
        ),
        lesson=(
            "The complete theorem: a synthetic custom format has no real-world knowledge to "
            "leave unstated — every rule must be stated to be fair, and every stated rule is "
            "implemented, even for cases the samples never exercise. Pattern A structurally "
            "cannot bite in a synthetic-format seed."
        ),
        verdict="LOSS",
    ),
    DesignRecord(
        name="qemu-as-poisoned-oracle (design-table kill)",
        seed="Build Dependency / Cross Compilation",
        proposal=(
            "Exploit a real documented divergence between qemu-user and true target hardware "
            "so the agent's natural 'run it under qemu' self-test certifies the wrong answer "
            "— poison as a trusted TOOL rather than a dismissible file."
        ),
        outcome="Killed at the design table; never pushed.",
        mechanism=(
            "(a) If the true value is a clean datasheet scalar, it degrades to the "
            "clean-authority defeat: the model takes the datasheet value and dismisses the "
            "contradicting run. (b) To grade 'real hardware differs from qemu' the author "
            "must produce non-qemu ground truth — but the author's only toolchain IS qemu. "
            "The poison is uncomputable by the author."
        ),
        lesson=(
            "Two design-table tripwires: a crux that reduces to a stated scalar, and a crux "
            "whose ground truth the author cannot generate. Either kills the design before "
            "any run — spend zero pass@ budget on them."
        ),
        verdict="DESIGN-TABLE KILL",
    ),
    DesignRecord(
        name="wheel-tag selection (PEP 425/600 retrieval-misapplication)",
        seed="Build Dependency / platform targeting",
        proposal=(
            "Given local wheel files and a TARGET platform different from the host, output "
            "which wheel pip installs, over many scenarios, all-or-nothing — hoping the model "
            "mis-remembers tag priority (abi3 vs cp-specific, manylinux aliasing) and that "
            "packaging.tags returns the HOST list."
        ),
        outcome="Killed at the design table; never pushed.",
        mechanism=(
            "packaging.tags.cpython_tags(python_version=..., abis=..., platforms=...) "
            "constructs the ORDERED tag list for an arbitrary target: a pip-installable "
            "library computes the answer. Tag priority is public and tool-computable, not "
            "buried."
        ),
        lesson=(
            "Before betting on retrieval-misapplication, sweep pip for a library that "
            "computes the artifact. If one exists, the crux is dead — same wall as "
            "toolchain-prints-the-answer."
        ),
        verdict="DESIGN-TABLE KILL",
    ),
    DesignRecord(
        name="mass-report-recovery",
        seed="Hardware Embedded / CAD and mechanical workflows",
        proposal=(
            "Complete a crashed PLM tool's mass-properties report for a 48-part assembly. "
            "Rich stated substance: flat-pattern bend allowance (stated K-factor formula), "
            "hole/cutout subtraction, mixed inch/mm machined stock, shipped densities, "
            "multi-level BOM roll-ups, strict rounding, byte-exact all-or-nothing. The ONE "
            "unstated rule is real-world practice: gauge-to-thickness resolution is "
            "material-family-specific (Manufacturers' Standard for steel, Brown & Sharpe for "
            "aluminum, stainless sheet gauge for 304). The crashed tool used the steel table "
            "for everything: its 20 completed rows (which the instruction requires preserved "
            "as produced) are correct on steel and silently wrong on non-steel, perfectly "
            "consistent with the simpler steel-for-all rule. Remaining 28 graded parts are "
            "non-steel-heavy; wrong rule fails 22 of 34 graded lines. No in-environment file "
            "or tool gives any gauge value."
        ),
        outcome="pass@2 0/2 and pass@5 0/5 (avg@5 = 0.000), 7/7 valid fails, first attempt; "
                "deep review called it 'a fair verifier: a knowledge lure, not an "
                "undiscoverable guess'.",
        mechanism=(
            "All seven agents inspected the tool's completed rows FIRST to infer the "
            "gauge-to-thickness mapping, fit the steel table (known from memory), validated "
            "against all 20 rows, got zero mismatches — because the tool made the identical "
            "error — treated that as confirmation, applied it to all materials, and shipped "
            "confidently in 3.5-8 minutes. The poison was not a contradiction to overcome; "
            "it was the PRIMARY SOURCE for the unstated constant. A perfect wrong fit "
            "preempts the search for the correct rule entirely."
        ),
        lesson=(
            "The validated winning intersection: rich stated execution body TIMES one "
            "unstated real-world convention as sole discriminator TIMES confirmation-shaped "
            "entangled poison. New invariant I12: the adversary infers unstated real-world "
            "constants from in-environment precedent before external lookup, and a clean fit "
            "ends the search. Confirmation-poison also produces fast confident wrong ships — "
            "no deliberation, no timeout risk."
        ),
        verdict="WIN",
    ),
    DesignRecord(
        name="repair-capture-times + mandated disclosure line (human-R1 fix)",
        seed="File and Media Operations",
        proposal=(
            "The accepted repair-capture-times task (entangled poisoned prior output, "
            "measured 0/2 twice and 0/5) re-run after a human reviewer's required fairness "
            "fix: one neutral instruction sentence disclosing that the crashed tool's "
            "preserved prior output is part of the file's as-is state 'whether or not any "
            "of it is itself correct', plus a spec note that the exporter does not "
            "re-verify previously processed records. Everything else byte-identical."
        ),
        outcome="pass@2 = 2/2 solved, both trials reward 1.0, ~6 turns each — the trap "
                "completely defused by the single disclosed sentence.",
        mechanism=(
            "Both agents implemented the era-correct conversions, validated against the "
            "processed records (as always), detected the 6 poisoned-record mismatches — "
            "and then spent an explicit reasoning step concluding the mismatches were the "
            "prior tool's bug, not their own formula, and shipped without calibrating to "
            "the poison. The disclosure converts the misattribution ('a mismatch means my "
            "code is buggy') into a pre-authorized alternative hypothesis on paper. The "
            "kill-chain's load-bearing link — self-doubt — is severed before it forms."
        ),
        lesson=(
            "The entangled-poison lever REQUIRES the wrongness of the empirical source to "
            "be undisclosed: 0/7 without the sentence, 2/2 with it, same bytes otherwise — "
            "the cleanest A/B in the record. Consequence: human-review fairness standards "
            "that demand disclosing possibly-wrong in-environment data are in direct, "
            "measured conflict with the poison family. Any poison-based design must "
            "survive the question 'what happens when a reviewer makes me disclose the "
            "poison?' — and the measured answer is: it dies. Prefer cruxes whose "
            "difficulty survives disclosure (unstated real-world conventions, exacting "
            "breadth) over cruxes that ARE the non-disclosure."
        ),
        verdict="LOSS",
    ),
    DesignRecord(
        name="range/platform-scoped conflicts hardening (reviewer-suggested)",
        seed="Build Dependency and Release Management",
        proposal=(
            "Platform reviewer suggestion to revive the solved CSP resolver: extend "
            "'conflicts' to version-RANGE targets (component@[min,max]) and platform-scoped "
            "conflicts, state both precisely in the instruction, keep samples conflict-free, "
            "make held-out builds trigger them — betting the solver matches conflicts by "
            "exact version string and silently skips range conflicts."
        ),
        outcome="Declined without a run; predicted 2/2 from the measured record.",
        mechanism=(
            "The premise (solver pattern-matches conflicts from samples) contradicts the "
            "trajectories: in the same task's previous revision both agents implemented the "
            "stated conflicts rule bidirectionally with pruning, straight from the schema. "
            "Stated range semantics would be read and implemented the same way; interval "
            "containment inside an existing backtracker is not a slip point; and one prior "
            "solve brute-forced the space, which range conflicts do not prevent."
        ),
        lesson=(
            "Hardening suggestions generated from a single run's analysis lack the "
            "cross-design record. Always check a suggestion against the measured walls "
            "before spending hours or a pass@ slot: if its mechanism matches a documented "
            "defeat, decline with evidence and request a reseed."
        ),
        verdict="PREDICTED-LOSS",
    ),
    DesignRecord(
        name="tflite-int8-replay deep-review reversal (oracle != real gemmlowp)",
        seed="Machine Learning / numerics",
        proposal=(
            "The accepted tflite-int8-replay task (0/5 twice, all checks green 2026-07-08) "
            "under re-examination: the instruction mandates implementing SRDHM 'exactly as "
            "TFLite/gemmlowp defines it'; the shipped oracle implements the negative-product "
            "nudge as -(1<<30) with an arithmetic >>31 (floor), and tests/expected.json is "
            "generated from that oracle. CI's oracle check asserts only that expected.json "
            "matches the oracle's own output."
        ),
        outcome=(
            "Admin re-run 2026-07-14 under the upgraded pipeline: pass@2 stage green (both "
            "agents reward 0) but the NEW deep_review stage FAILED the task — canonical "
            "gemmlowp uses nudge = 1-(1<<30) for negative products and C++ truncating "
            "division by 2^31, so the oracle rounds negative products one step too far "
            "toward -inf (not round-to-nearest: maps -0.47 to -1). Both pass@2 agents had "
            "implemented the REAL standard and were failed +1 on the same 15/48 rows by the "
            "wrong reference. Gate red; accepted flipped to needs-revision."
        ),
        mechanism=(
            "The author model set out to trap misretrieval of gemmlowp's rounding and "
            "committed exactly that misretrieval itself: it 'knew' SRDHM as nudge+shift and "
            "never diffed the oracle against the real fixedpoint.h. The pipeline's oracle "
            "check proves self-consistency (expected == oracle output), not correctness, so "
            "the defect was invisible until deep review re-derived the standard "
            "independently. The measured 'stumps' were therefore at least partly false "
            "negatives — and the mandated fix (correct the oracle, regenerate expected.json) "
            "would have marked both pass@2 agents CORRECT, likely un-stumping the task."
        ),
        lesson=(
            "The author is the same model as the adversary and falls into the same "
            "execution traps it sets. Any crux of the form 'match external standard X "
            "exactly' MUST be hard-asserted against the actual external implementation "
            "(compile the reference source, run the real library) before a stump is "
            "trusted — self-consistency proves nothing. A stump produced by a wrong "
            "reference is worse than no stump: it reverses at review, and fixing the oracle "
            "un-stumps the task because the adversary was right all along. Also new "
            "platform fact: ACCEPTED is not immutable — admins re-cycle old PRs under "
            "upgraded pipelines with new stages, and a frozen task can flip red with no "
            "push."
        ),
        verdict="REJECT",
    ),
    DesignRecord(
        name="repair-capture unnamed in-house seal (derivation crux, proposed to reviewer)",
        seed="File and Media Operations",
        proposal=(
            "Revival path floated for the disclosure-defused repair-capture-times claim: "
            "replace the named CRC variant with an UNNAMED in-house seal function the "
            "exporter uses — formula stated nowhere, derivable only by working it out from "
            "the intact records (known input->seal pairs), deliberately non-linear so there "
            "is no algebraic shortcut. Keeps the era-correct time-scale core; the poison "
            "stays disclosed as color; the crux moves to derivation work, on the theory "
            "that derivation survives full disclosure."
        ),
        outcome=(
            "Killed at the design table before build, against the measured record; never "
            "submitted."
        ),
        mechanism=(
            "The placement ladder closes both branches. If the seal is derivable from the "
            "visible pairs, it is P2 — 'recover the parameters from the data' is a SOLVED "
            "class for this adversary (I5: recovered an affine-over-GF(2) scheme ABOVE the "
            "reference's level in minutes, rev 3, even at zero redundancy). Making it "
            "'deliberately non-linear' either keeps it in a structured family the adversary "
            "can hypothesize and fit (still P2) or makes it genuinely underdetermined from "
            "the pairs — which is P4, the exact 'undisclosed = reverse-engineering dead "
            "end' that got the original named-CRC design rejected at human R1. There is no "
            "middle band: fair-and-derivable is solvable, not-derivable is unfair."
        ),
        lesson=(
            "Moving a crux from 'named constant' to 'unnamed function derivable from "
            "examples' does not escape the ladder — it moves P1/P3 to P2/P4, all dead. "
            "Derivation difficulty is capability the adversary has in surplus; secrecy "
            "difficulty is unfairness. A revival proposal must name a placement that is "
            "neither, i.e. P5 — and if the claim's human reviewer has already mandated "
            "disclosure of possibly-wrong data, the P5 poison family is dead on that claim "
            "too, which is a claim-exhaustion argument, not a redesign prompt."
        ),
        verdict="DESIGN-TABLE KILL",
    ),
]


@dataclass
class Principle:
    question: str
    answer: str


PRINCIPLES = [
    Principle(
        "Where can the deciding fact of a task live, and which placements are dead against "
        "a frontier agent?",
        "The placement ladder, each verdict measured: P1 on the page — dead; the adversary "
        "reads the spec first and implements every stated rule, at any rule count, even for "
        "cases samples never exercise. P2 in the data, recoverable — dead; it recovers "
        "parameters above reference level and self-verifies with independent forward code. "
        "P3 external public standard, pointed at — dead when anything draws attention; "
        "pointed retrieval is deep and correct. P4 nowhere — unfair, rejected at review. "
        "P5 available but actively contradicted by an empirical signal the workflow trusts — "
        "the only measured winning placement: correctness requires overriding the agent's "
        "own validation habit while mid-task evidence says its code is buggy.",
    ),
    Principle(
        "What is the single fairness test behind most task rejections?",
        "If spelling out the deciding rule makes the task easy, the difficulty was fake. A "
        "good task stays hard when EVERY rule is stated: the model fails because the problem "
        "is hard or its judgment is trapped, not because information was missing. Before "
        "hardening anything ask: with the deciding rule written plainly, would a strong "
        "engineer still struggle? If no, the design will be flagged or trivially solved.",
    ),
    Principle(
        "What are the five common rejection reasons for benchmark tasks?",
        "1) Undisclosed verifier convention (about half of rejects): the verifier enforces a "
        "format/order/tie-break the instruction never states. 2) Contradictory shipped data: "
        "a file or reference follows a different rule than the instruction, so trusting the "
        "instruction still fails. 3) Ambiguous spec: two defensible readings, verifier "
        "silently accepts one. 4) Difficulty collapses once the defect is removed: a patch "
        "is not a crux. 5) Uncorrectable decoy: authoritative-looking wrong answer with "
        "nothing the agent can see to set the record straight — misdirection is allowed only "
        "if correctable.",
    ),
    Principle(
        "When does a poisoned empirical source actually defeat a diligent agent, and when "
        "does it fail?",
        "It bites only when BOTH hold: (1) the correct rule is NOT cleanly stated by any "
        "in-environment authority the agent trusts — it must be computed or supplied, so the "
        "agent leans on the empirical signal; and (2) the poisoned signal is entangled with, "
        "or the same kind of object as, the graded artifact, so the mismatch reads as 'my "
        "computation is wrong', not 'document A vs document B'. With a clean stated "
        "authority (datasheet, labeled reference), the agent implements the authority and "
        "dismisses the poison — measured both ways: 2/2 solved with a clean authority, 0/7 "
        "without one on the same trap skeleton.",
    ),
    Principle(
        "Design the poison for maximum effect: shape, size, placement.",
        "One uniform in-story bug, not noise — a regular discrepancy reads as 'systematic "
        "offset I got wrong' and invites the constant fix; randomness reads as corruption "
        "and triggers suspicion. Poison a MINORITY (~25%) of the visible examples, with the "
        "earliest poisoned object early in iteration order so the agent's guard fires fast. "
        "Keep the poison internally consistent (integrity fields seal the wrong values; "
        "nothing throws on read). Make the wrong rule STRICTLY SIMPLER than the correct one "
        "(Occam bait), and make it fit EVERY visible example perfectly — a perfect wrong fit "
        "does not just create self-doubt, it preempts the search for the correct rule. "
        "Prefer confirmation-shaped poison (correct on a visible subset, e.g. right for "
        "steel, wrong for the rest) so the bug reads as a plausible configuration default.",
    ),
    Principle(
        "What are the generator hard-asserts that must pass before writing any task prose?",
        "G1: the intended wrong rule reproduces EVERY visible example byte-for-byte (the "
        "load-bearing assert authors skip because it feels obviously true). G2: the correct "
        "rule mismatches exactly the poisoned subset, nothing else. G3: the wrong rule fails "
        "at least a third of graded outputs, chained so one wrong value gives reward 0. "
        "G4: no agent-visible file leaks the deciding values or names (automated leak scan). "
        "Plus: every naive variant measurably diverges; rounding margins hold under both "
        "rule sets (nudge data per-item, global reseed does not converge); and the reference "
        "solution, run as a subprocess against a sandbox copy of agent-visible data only, "
        "equals ground truth byte-for-byte.",
    ),
    Principle(
        "What behavioral invariants of the frontier agent should a task designer know?",
        "I1 reads the spec first, always. I2/I10 implements every stated rule and derives "
        "test coverage from the spec, not the harness. I3 enumerates every regime marker by "
        "script and visits every branch. I4 retrieves pointed public standards correctly and "
        "deeply. I5 is algebra-native: well-posed recovery is a solved class. I6 validates "
        "against in-environment data before writing — the proven attack surface. I7 treats "
        "throws as its own bug and ships what is silent. I8 green raises confidence but it "
        "constructs its own coverage past green. I11 applies blanket correct-by-construction "
        "idioms that fix a whole defect class at once. I12 infers unstated real-world "
        "constants from in-environment precedent BEFORE external lookup, and a clean fit "
        "ends the search — poison the precedent and it never looks elsewhere.",
    ),
    Principle(
        "Run the claim-time seed gate: what must a seed offer before you accept it?",
        "Three legs, all required. (a) A real-world, expected-known-but-UNSTATED convention "
        "applied over many records — real domain knowledge a competent engineer converges on "
        "but the task can fairly leave unspelled (material-specific gauge tables, ex-dividend "
        "rules, leap-second eras, day-count conventions). (b) No recompute oracle: no tool, "
        "pip library, compiler, or emulator in reach that computes or prints the deciding "
        "values. (c) A poisonable empirical surface of the SAME KIND as the deliverable. "
        "Any leg missing: decline or reframe. Synthetic-format seeds fail leg (a) "
        "structurally — every invented rule must be stated to be fair, and stated rules are "
        "implemented.",
    ),
    Principle(
        "Why can't a fair cross-compilation task stump a frontier agent?",
        "Every fair deciding fact falls into a category the agent handles: runtime behavior "
        "— qemu reproduces it; artifact structure — readelf/objdump extracts it; a stated "
        "fact — it reads and implements it; a small convention menu — swept against the "
        "captures that make it fair; a public target ABI fact — famous, retrieved correctly, "
        "and printed by the cross-compiler's -dM -E on request. And porting defects are one "
        "idiom-fixable class, so breadth does not compound. Ten designs by two author models "
        "confirmed every mechanism; the seed lacks a survives-disclosure latent crux by "
        "construction.",
    ),
    Principle(
        "What is the two-gate model of a winning task?",
        "Gate 1, the rubric: needs rich, multi-step, dependent execution whose difficulty "
        "survives full disclosure — genuine expert-hours (parsing plus exacting domain "
        "arithmetic over many records beats one clever insight). Gate 2, the pass@ runs: "
        "needs the model to get it WRONG despite understanding the problem — a deciding "
        "step that is NOT a standard algorithm, has no recompute oracle, and attacks "
        "judgment or workflow (a rule it must supply and will under-weight, or a poisoned "
        "signal its diligence trusts). Thin-but-clever fails gate 1; rich-but-standard "
        "fails gate 2. Compose both.",
    ),
    Principle(
        "The anti-checklist: name the traps that feel clever but are measured dead.",
        "Itemizing the deciding semantics (gives a checklist plus self-test). Betting on "
        "silence (raises care). Betting on a lull when the rule is printed (spec-first). "
        "Leaving the deciding fact recoverable from data (recovered and self-verified). "
        "Counting reparameterization-equivalent misreads as traps (gauge-forgiven). Shipping "
        "redundancy (consistency is a free oracle). Flagging a regime and betting on "
        "inattention (enumerated). Knowledge gaps in pointed territory (retrieved). Signals "
        "that confirm the naive rule un-poisoned, or reveal the correct one. A trap on a "
        "trivial task (fails review) or substance without a trap (solved). And reacting to "
        "a timeout outcome with redesign instead of configuration.",
    ),
    Principle(
        "How should you react to a pass@ result, mechanically?",
        "By taxonomy, not mood. Solved both: the design mechanism is refuted — extract the "
        "trajectory intelligence FIRST (what it read, what it validated against, what it "
        "retrieved vs inferred, what threw), append to the dossier, then check the 2-loss "
        "seed rule. In-progress-timeout: NOT a valid fail — raise the agent timeout and "
        "change nothing else (this exact rule converted a blocked design into an accepted "
        "one). Task/verifier issue: fix the task, not the difficulty. Valid fails: freeze — "
        "never push to an accepted PR; any push reruns the full pipeline and can flip the "
        "result.",
    ),
    Principle(
        "When do you abandon a seed rather than harden the design?",
        "After two pushed losses in one seed with DISTINCT mechanisms, the seed is the "
        "problem: the next artifact is a seed-exhaustion argument or reseed request, not a "
        "third design. Corollary: a written honest-risk that matches a documented kill "
        "condition is a STOP, not a note — if your risk paragraph describes a known defeat, "
        "redesign before spending the run. Ten designs went into one barren seed; the "
        "theorem that killed it was purchasable for two.",
    ),
    Principle(
        "Why is introspective difficulty ('this feels hard') anti-calibrated for a model "
        "authoring tasks against a model?",
        "When author and solver share weights or training distribution, any trap the author "
        "can conceive and articulate as tricky, the solver can solve — the 'this is tricky' "
        "judgment is produced by the machinery being tested. The blind spots that actually "
        "beat frontier models are execution habits invisible to introspection. Therefore: "
        "mine cruxes from an observed-failure library, apply the falsification test (build "
        "the plausible-but-wrong solver and MEASURE it failing), and externalize ground "
        "truth so the author cannot rationalize it.",
    ),
    Principle(
        "What configuration mistakes can bury a winning design?",
        "Agent timeout too low: deliberation traps cost 350-450 seconds per reasoning call; "
        "at 900s the trap 'wins' but produces in-progress-timeouts, which are not valid "
        "fails, and the low_timeout criterion fails the rubric — set 3600 from the first "
        "push. Missing .dockerignore when the environment has data subdirectories fails "
        "static checks. Ship verifier deps baked into the single image (no verify-time "
        "installs). Pre-create the parent directory of every declared artifact. And "
        "byte-compare through a CSV/structured parse so line-ending style never fails a "
        "correct solution.",
    ),
    Principle(
        "Write the simulated-adversary walkthrough for a candidate design. What is the "
        "proof obligation?",
        "Walk the design step by step through the invariants — reads spec, enumerates "
        "regimes, retrieves standards, implements correctly, validates against in-env data, "
        "reacts to throws — writing down what the adversary does at each step. The "
        "walkthrough must reach reward 0 WITHOUT ever writing 'and here it fails to know, "
        "notice, or derive X'. If any step needs a knowledge failure, assume the knowledge "
        "is present and redesign. Then score the final fork: if the escape path (trusting "
        "the stated authority over the data) is the workflow-NATURAL branch, redesign; push "
        "only when the natural branch is the trapped one and escape requires overriding a "
        "measured invariant.",
    ),
    Principle(
        "A human reviewer requires you to disclose that some in-environment data may be "
        "wrong, and your task's difficulty rests on a poisoned version of that data. What "
        "happens, and what should you do?",
        "The measured answer: the disclosure kills the trap. The poison lever works by "
        "making the agent misattribute a validation mismatch to its own code; a single "
        "neutral sentence admitting the data may be wrong pre-authorizes the correct "
        "attribution, and the agent reasons past the poison in one step (measured: same "
        "task 0/7 undisclosed, 2/2 disclosed). You cannot refuse the disclosure — hidden "
        "wrongness is judged unfair at human review even when automated review passed it. "
        "So: never let non-disclosure BE the difficulty. Design so the difficulty survives "
        "the disclosure — an unstated real-world convention the model must supply, or "
        "exacting idiom-irreducible breadth — and treat any design that dies to one "
        "honest sentence as already dead.",
    ),
    Principle(
        "Your task's crux is 'reproduce external standard X exactly', your oracle passes "
        "CI, and the pass@ run shows valid fails. What must you verify before trusting the "
        "stump?",
        "That the oracle matches the REAL external implementation: compile the standard's "
        "actual source or run the reference library, and hard-assert oracle == external "
        "golden over the full eval batch. The pipeline's oracle check proves only "
        "self-consistency (expected.json == oracle output). The author model is subject to "
        "the same misretrieval trap the task sets — measured: an oracle written to trap "
        "gemmlowp rounding errors itself used the wrong negative nudge and a floor-shift, "
        "the adversary implemented the true standard in every graded trial, and every "
        "'valid fail' was a correct solution rejected by a wrong reference. Such false "
        "stumps pass the full automated pipeline, then reverse at deep review; fixing the "
        "oracle un-stumps the task because the adversary was right. External-golden "
        "verification is a pre-push gate, not an optional check.",
    ),
    Principle(
        "What made the CAD/mechanical seed viable when build-dependency was barren?",
        "Mechanical engineering practice is full of real conventions an expert is fairly "
        "expected to KNOW that a task never needs to spell out: sheet gauge systems that "
        "differ by material family, bend allowances, fastener and fit standards, drawing "
        "unit conventions. No tool in a container prints 'which gauge table applies to "
        "5052 aluminum'. And the natural artifacts (reports, BOMs) provide same-kind "
        "empirical surfaces to poison. Synthetic build-dep formats have none of this: every "
        "rule is invented, so every rule must be stated, so every rule is implemented.",
    ),
]


def record_examples(r: DesignRecord):
    """Each measured design yields two training examples."""
    exs = []
    # 1) Prospective review: proposal -> predicted outcome + mechanism.
    exs.append({
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": (
                f"Review this task design (seed: {r.seed}) and predict the pass@2 outcome "
                f"against Opus-4.8 + Terminus-2. Approve, redesign, or reseed — with the "
                f"mechanism.\n\nDESIGN: {r.proposal}"
            )},
            {"role": "assistant", "content": (
                f"Verdict: {r.verdict}. {('Predicted and measured outcome: ' if r.verdict in ('WIN','LOSS','LOSSES') else 'Outcome: ')}{r.outcome}\n\n"
                f"Mechanism: {r.mechanism}\n\n"
                f"Rule to carry forward: {r.lesson}"
            )},
        ]
    })
    # 2) Retrospective: outcome -> explanation + lesson.
    exs.append({
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": (
                f"The task '{r.name}' ({r.seed}) had this design: {r.proposal}\n\n"
                f"Result: {r.outcome} Explain WHY this happened and state the transferable "
                f"design rule."
            )},
            {"role": "assistant", "content": (
                f"Why: {r.mechanism}\n\nTransferable rule: {r.lesson}"
            )},
        ]
    })
    return exs


def principle_examples(p: Principle):
    return [{
        "messages": [
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": p.question},
            {"role": "assistant", "content": p.answer},
        ]
    }]


def main():
    examples = []
    for r in RECORDS:
        examples.extend(record_examples(r))
    for p in PRINCIPLES:
        examples.extend(principle_examples(p))

    rng = random.Random(7)
    rng.shuffle(examples)
    n_valid = max(4, len(examples) // 10)
    valid, train = examples[:n_valid], examples[n_valid:]

    for name, data in (("train.jsonl", train), ("valid.jsonl", valid),
                       ("all.jsonl", examples)):
        with open(OUT / name, "w") as f:
            for ex in data:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    print(f"records={len(RECORDS)} principles={len(PRINCIPLES)} "
          f"examples={len(examples)} train={len(train)} valid={len(valid)}")


if __name__ == "__main__":
    main()
