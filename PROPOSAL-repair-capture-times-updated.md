# Updated proposal — claim dynamo-4ad62d4 (PR #2, repair-capture-times)

v2 (2026-07-15, evening): amended for REV 6 (disclosure-shield build, task commit
19c1d21). Supersedes the v1 text that passed the proposal quality gate earlier today;
adds the bus-local time base / rounding-boundary layer so the approved proposal matches
the rev-6 task at push time (no drift blocker repeat). Submit via the portal's
proposal-edit option BEFORE pushing the task branch.

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
parameters into the spec. The difficulty lives in three layers. (1) Era-correct
time-scale normalization: records span multiple public time scales (GPS, BeiDou, GLONASS,
and a TAI-referenced base), and converting each channel's native `raw_time` to UTC
milliseconds requires applying the correct leap-second era and per-scale epoch semantics
record by record; grading is exact and all-or-nothing across the whole file, so a single
era slip anywhere fails everything, and there is no validator in the environment to
signal the mistake. (2) Exact boundary arithmetic on a sixth, bus-local time base: the
capture bus's own clock stamps some channels with signed sub-millisecond tick counts
(4096 ticks per second, relative to a bus epoch carried in the header), and the
specification states the conversion rule plainly — nearest millisecond, with an exact
half-millisecond rounded away from zero. The rule is fully disclosed; the difficulty is
executing it exactly, because many of the records needing repair fall on the boundary
regime (exact half-millisecond ticks and negative sub-millisecond offsets) where the
common rounding idioms of every mainstream language silently disagree with the stated
rule by one millisecond while agreeing with it everywhere else. (3) An attribution
judgment, disclosed to the solver: the crashed tool's prior output is still in the file
and must be preserved exactly as it appears, and the instructions state that this prior
output may not itself be correct — some already-processed records were in fact written by
the misbehaving tool with a systematically wrong offset, while others, including records
on the rounding boundary, were processed correctly. An engineer who validates their own
implementation against the processed records — the natural diligence move — must judge
each discrepancy family on the specification alone: mismatches caused by the tool's real
bug must be attributed to the tool, while a mismatch caused by their own boundary
arithmetic must be recognized as their own and fixed, even though the disclosed
possibility of tool error makes "the tool was wrong there too" the comfortable reading of
both. Misjudging either family fails a substantial fraction of the graded records.

Intended solution approach (and key insight)

Parse the container (header plus records) per the specification, identify the unprocessed
records by their zero placeholders, convert each one's `raw_time` to UTC milliseconds
using the correct public time-scale semantics and leap-second era for that record's time
base — and, for the bus-local base, exact integer arithmetic implementing the stated
round-to-nearest with halves away from zero (not the language's default rounding) —
recompute each repaired record's CRC-32 digest and the chained file digest, preserve
every already-processed record byte-for-byte, and write the byte-exact result to
/app/repaired.bin. Key insight: the specification and the public time standards are the
sole authority for the repaired values — the crashed tool's prior output is historical
state to be preserved, not a reference to calibrate against, so every discrepancy between
one's implementation and a processed record must be adjudicated against the spec: it is
evidence of the tool's misbehavior only where the tool actually violated the spec, and
evidence of one's own bug where it did not. A focused data-recovery engineer needs
roughly 4–6 hours: container parsing, era-correct conversions for each time scale, exact
boundary rounding, the per-family attribution calls, and exact re-sealing.

How the solution will be verified

The agent writes the repaired file to /app/repaired.bin. The verifier compares it byte
for byte against the reference repaired file (produced by the reference implementation
from the same crashed input) and requires an exact match. Because the output is exact
bytes, exact match with no tolerance is the fair grader: UTC milliseconds are discrete,
every faithful implementation of the specified conversions yields identical bytes, while
a wrong leap era, a wrong epoch, an off-by-one rounding idiom on the boundary records, or
calibrating to the crashed tool's prior output diverges on many records at once. The
reference implementation derives the answer from the agent-visible file and spec (nothing
hardcoded; the generator additionally cross-checks the rounding rule against an
independent decimal implementation), proving the task is solvable; ground truth lives
only in the verifier, and no integrity-checking or time-conversion tool ships in the
environment. Measured record of this design lineage on this pipeline, for transparency:
reference 1.0, nop 0; the pre-disclosure revision ran pass@2 = 0/2 twice and pass@5 = 0/5
with all seven failures graded valid; after the reviewer-required disclosure that
processed records may be wrong, pass@2 = 2/2 — the current revision therefore moves the
load-bearing difficulty into the era arithmetic and the exact boundary rounding, which
survive full disclosure.

Category & sub-category justification

The task is exactly recovery and repair of a file: taking a capture left broken by a
crashed tool and restoring its missing normalized values and integrity data so it is
valid again. It is not parsing for analysis or format conversion — the deliverable is the
repaired file itself, reconstructed by recomputing the damaged data, which is the heart
of File and Media Operations / Recovery and repair.
