# Updated proposal — claim dynamo-4ad62d4 (PR #2, repair-capture-times)

Submitted via the portal's proposal-edit option (which appeared 2026-07-15), replacing the
stale approved CRC-32/BZIP2 text. Purpose: close reviewer blocker 1 (proposal↔task drift)
by making the approved proposal describe the AS-BUILT task. This does NOT unblock pass2
(2/2 post-disclosure, §20.8); it cleans the record so the claim-level conversation
(fairness-vs-difficulty tension / reseed, §20.10) happens from a fully-compliant position.

Design-table guardrails honored: no unnamed-seal text (killed, §20.10), no new poison
(reviewer-dead on this claim), no revert to named-CRC (P1-dead, and would re-drift).

---

Category: File and Media Operations
Sub-Category: Recovery and repair

Task (working title): Complete a crashed normalizer pass on a binary telemetry capture

Why this is genuinely difficult

The agent is given a binary telemetry capture (a synthetic but realistic record-structured
telemetry log in the CAPX version-4 container format) whose export tool crashed partway
through its normalizer pass: many records still carry zero placeholders in their `utc_ms`
and `digest` fields, and the file's trailing digest was never written. The agent must
complete the pass by hand, producing the byte-exact repaired file — the daily work of a
data-recovery / digital-forensics engineer reconstructing a damaged capture so the
consuming tool can read it again. The data is synthetic (a fixed-seed generator produces
the header, records, and crash state), which lets the format and the damage be controlled
exactly while still mirroring real record-plus-checksum container formats.

The difficulty is deliberately not "compute a checksum" — the integrity fields use the
everywhere-standard CRC-32, because this pipeline's own rubric review established that a
parameterized CRC variant collapses to a library one-liner once fairness forces its
parameters into the spec. The difficulty lives in two layers. (1) Era-correct time-scale
normalization: records span multiple public time scales (GPS, BeiDou, GLONASS, and a
TAI-referenced base), and converting each channel's native `raw_time` to UTC milliseconds
requires applying the correct leap-second era and per-scale epoch semantics record by
record across roughly forty records; grading is exact and all-or-nothing across the whole
file, so a single era slip anywhere fails everything, and there is no validator in the
environment to signal the mistake. (2) An attribution judgment, disclosed to the solver:
the crashed tool's prior output is still in the file and must be preserved exactly as it
appears, and the instructions state that this prior output may not itself be correct —
some already-processed records were in fact written by the misbehaving tool with a
systematically wrong offset. An engineer who validates their own implementation against
those records — the natural diligence move — sees disagreements and must correctly
attribute them to the crashed tool rather than "fix" a correct implementation to match it;
adopting the tool's simpler wrong rule fails a third of the graded records.

Intended solution approach (and key insight)

Parse the container (header plus records) per the specification, identify the unprocessed
records by their zero placeholders, convert each one's `raw_time` to UTC milliseconds
using the correct public time-scale semantics and leap-second era for that record's time
base, recompute each repaired record's CRC-32 digest and the chained file digest, preserve
every already-processed record byte-for-byte, and write the byte-exact result to
/app/repaired.bin. Key insight: the specification and the public time standards are the
authority for the repaired values — the crashed tool's prior output is historical state to
be preserved, not a reference to calibrate against, so discrepancies between a correct
implementation and the tool's records are evidence of the tool's misbehavior, not of one's
own. A focused data-recovery engineer needs roughly 4–6 hours: container parsing,
era-correct conversions for each time scale, the attribution call, and exact re-sealing.

How the solution will be verified

The agent writes the repaired file to /app/repaired.bin. The verifier compares it byte for
byte against the reference repaired file (produced by the reference implementation from
the same crashed input) and requires an exact match. Because the output is exact bytes,
exact match with no tolerance is the fair grader: UTC milliseconds are discrete, every
faithful implementation of the specified conversions yields identical bytes, while a wrong
leap era, a wrong epoch, or calibrating to the crashed tool's prior output diverges on
many records at once. The reference implementation derives the answer from the
agent-visible file and spec (nothing hardcoded), proving the task is solvable; ground
truth lives only in the verifier, and no integrity-checking or time-conversion tool ships
in the environment. Full measured record on this pipeline, for transparency: reference
1.0, nop 0; in its pre-disclosure state the task ran pass@2 = 0/2 twice and pass@5 = 0/5
with all seven failures graded valid; after adding the reviewer-required disclosure that
processed records may be wrong, pass@2 = 2/2 — so under the current (fair) wording the
era-correct time-scale normalization is the load-bearing difficulty.

Category & sub-category justification

The task is exactly recovery and repair of a file: taking a capture left broken by a
crashed tool and restoring its missing normalized values and integrity data so it is valid
again. It is not parsing for analysis or format conversion — the deliverable is the
repaired file itself, reconstructed by recomputing the damaged data, which is the heart of
File and Media Operations / Recovery and repair.
