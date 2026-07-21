# Proposal — flow-ledger-backfill (Security / Network Forensics)

> Paste everything between the markers into the proposal box. Category lines stay at top, unedited.

---

Category: Security
Sub-Category: Network Forensics

## 1. Why this task is genuinely difficult

**The scenario.** A network detection-and-response (NDR) sensor records low-level per-segment
TCP metadata (timestamps, endpoints, sequence numbers, flag bits, segment lengths) into an
append-only capture log, and a downstream summarizer process turns that telemetry into
per-flow ledger records (directional byte counts, packet counts, connection state, duration,
integrity digest). During a suspected data-exfiltration incident, the traffic spike crashed
the summarizer mid-run: the capture log is complete, but the flow ledger has a gap covering
the incident window. The agent must backfill the missing ledger records — exactly as the
flow-record specification defines them — so the investigation can quantify what was taken.

**Who does this work and why it is valuable.** This is core DFIR / network-forensics work: a
network forensic analyst or incident responder reconstructing connection records from raw
capture telemetry when the normal pipeline failed at the worst moment. The deliverable —
accurate per-flow, per-direction transfer volumes — is what determines exfiltration sizing,
breach-notification scope, and legal exposure. Getting the byte accounting wrong by even a
few percent changes the incident's severity classification, so correctness is the entire
point of the exercise.

**Data provenance.** The dataset is fully synthetic, produced by a deterministic generator
(fixed seed): no real network traffic, hosts, or personal data. Realistic complexity is
engineered in, not sampled: the incident window contains hundreds of TCP conversations that
exercise the wire-protocol regimes a real capture would contain — loss and retransmission
(including partial overlaps), initial sequence numbers near 2^32 so sequence arithmetic
wraps mid-flow, half-open and RST-torn connections, keepalive probes, simultaneous close,
and interleaved long-lived flows. The generator's realism is itself validated externally:
each synthetic conversation is also emitted as a genuine pcap and the reference byte
accounting is cross-checked against independent packet-analysis tooling, so the ground truth
matches what professional-grade reassembly produces — the task ships only the sensor's
metadata log, never the pcap.

**Why it is hard for an expert — the specific pitfalls.**
1. *Byte accounting is a wire-protocol semantics problem, not a subtraction.* The correct
   per-direction byte count is the coverage of the flow's transferred data, computed in
   sequence space: retransmitted and overlapping segments must not be double-counted,
   control flags that occupy sequence positions without carrying data must not inflate the
   count, and all arithmetic is modulo 2^32 (several graded flows wrap). The
   plausible-looking shortcut — "last sequence number seen minus first" per direction —
   is silently wrong on exactly the loss-heavy, long-lived flows that matter most in an
   exfiltration investigation, and produces clean-looking integers everywhere.
2. *The historical record is not a safe calibration source.* The ledger contains thousands
   of records the summarizer produced before it crashed, and the capture log overlaps some
   of them, so the natural professional move — recompute a sample of already-summarized
   flows and check for agreement — is available. But a subset of historical records was
   emitted by the sensor's load-shedding fast path, whose accounting is a documented class
   of real-world telemetry bug. The analyst must decide, mid-task, whether a discrepancy
   between their implementation and the landed records means their code is wrong or the
   historical tooling was — a genuine and common forensic judgment call (tool validation
   vs. self-doubt), and the place where careless or over-trusting workflows fail.
3. *Multi-rule reconstruction substance.* Beyond the crux, the ledger schema imposes a full
   set of stated rules that must all be executed correctly: originator/responder direction
   attribution, flow keying and idle-timeout splitting, connection-state classification,
   duration rounding, record ordering, and a per-record plus file-level integrity digest
   that chains all graded records together. Every rule is stated in the spec; the work is
   sustained, exact execution across hundreds of records.

## 2. Intended solution approach

High-level strategy: (1) parse the segment metadata log and group segments into flows per
the spec's keying and timeout rules; (2) attribute direction from connection establishment;
(3) for each direction, compute transferred bytes as the union of data-bearing sequence
intervals in modulo-2^32 sequence space — coalescing retransmissions/overlaps and excluding
flag-consumed sequence positions; (4) derive state, counts, and duration per the stated
rules; (5) emit the backfilled ledger records in the specified order and compute the
per-record and file-level digests.

**The key insight** is that flow byte totals live in sequence space, not in segment
arithmetic: the analyst must treat each direction as an interval-coverage problem over a
wrapping 32-bit ring, and must anchor correctness to the flow-record specification (and
standard TCP semantics) rather than to agreement with the historical ledger — recognizing
that the minority of historical records that disagree with a correct implementation are the
output of the sensor's buggy fast path, which the instruction directs to preserve as-is,
not to emulate. A solver that "fixes" its implementation until it matches the historical
records will converge on the simpler, wrong accounting rule and fail the graded window.

**Expert effort estimate.** A qualified network-forensics engineer comfortable with TCP
internals and scripting: best case ~5–6 focused hours; realistically 8–10 hours including
validation against the historical ledger and diagnosis of the fast-path discrepancy. This
is multi-step terminal work throughout (exploring the logs, implementing, running,
cross-checking, debugging edge regimes) — not paper-solvable and not a one-shot.

## 3. Verification

The agent must produce one artifact: the backfilled flow-ledger file for the gap window at
a specified path, in the specified line-oriented record format, plus the file-level digest
record. Verification is fully deterministic and result-only (no inspection of method):

- The verifier compares every backfilled record field-exactly against the generator's
  ground truth (integers and enumerations only: bytes, packets, state codes, millisecond
  durations, digests) and checks the chained file-level digest. Reward is binary
  all-or-nothing: any single wrong field breaks its record digest and the file digest.
- No tolerances are used, and none are needed: every graded field is a single-valued
  integer or enumeration under the spec, so exact match cleanly separates the correct
  accounting from every plausible-but-wrong variant. Wrong methods are rejected by
  construction because the graded flow set is deliberately heavy in the regimes where
  naive accounting diverges (retransmission, wraparound, flag-consumed sequence
  positions); a large fraction of graded records differ between the correct rule and
  each naive variant, so partial-credit luck is impossible.
- Author-side quality gates (already part of the build plan): the reference solution is
  asserted equal, via subprocess, to an external golden derived from independent
  packet-analysis tooling over the generated pcaps; each measured naive variant is
  asserted to fail a large fraction of graded records; a no-op scores 0; the reference
  scores 1.0 end-to-end. Ground truth is never present in the agent-visible image, and
  the answer cannot be looked up or hardcoded (it exists nowhere but the generator).

## 4. Category / Sub-Category justification

This is Security / Network Forensics in both substance and skill: the task is the
reconstruction of network communication records (who talked to whom, in which direction,
how much data moved, over what connection lifecycle) from low-level capture telemetry
during a security incident — the canonical network-forensics deliverable. The deciding
expertise is wire-protocol semantics as applied in forensic accounting (TCP sequence-space
analysis, retransmission handling, connection-state interpretation) plus the
evidence-handling judgment of validating tool output during an investigation. No other
category fits: the difficulty is not generic data processing — every pitfall is a
network-protocol fact, and the deliverable is a forensic artifact.

---

## APPENDIX — PRIVATE DESIGN NOTE (DO NOT SUBMIT; playbook mapping)

- **Skeleton:** §20.5 validated recipe, domain #9 (network forensics). Placement **P5**;
  crux = I6/I12 confirmation-poison over landed flow-ledger precedent.
- **Two authorities:** normative = flow-record spec (+ standard TCP semantics, pointed at
  as a body of detail only — no arbiter words); empirical = landed ledger records, a
  minority produced by the fast path computing **W = naive per-direction seq-delta**
  (strictly simpler than C = mod-2^32 interval-union coverage minus flag-consumed
  positions, retrans deduped).
- **Geometry to hard-assert:** G1 W fits every landed row (clean rows chosen where W==C);
  G2 C mismatches exactly the poisoned subset; G3 ≥⅓ graded flows in divergence regime +
  chained digest; G4 no third arbiter (no pcap in env; no tool consumes the custom log;
  spec worked-examples avoid the divergence regime). F1 anchor + F2 preserve sentences in
  instruction. F5/§20.9: generator emits real pcaps per conversation, asserts golden ==
  tshark/Zeek reassembly via subprocess.
- **Arbiter-words grep (§20.16) before any push**, over every agent-visible file, for the
  W-vs-C delta vocabulary: payload, retransmi*, duplicate/dedup, phantom, consume(s) a
  sequence number, SYN/FIN byte, wrap/wraparound, unique, coverage. Field descriptions use
  notation-level wording only ("bytes carried by the flow in each direction, `orig_bytes`
  / `resp_bytes`").
- **In-story bug:** load-shedding fast path (correct-on-a-subset steel: normal-path rows
  are C==W flows; fast-path rows are W on W≠C flows). Changelog may note the fast-path
  *setting* existed — never its behavior. Earliest poisoned row early in ledger order.
- **§18.7 walkthrough (done on paper, no knowledge failure assumed):** I1 reads spec
  (conflict not on page) → I3 enumerates flows/gap → I4 retrieves TCP semantics correctly
  (knowledge is NOT the bet) → implements C → I6 validates vs landed ledger → uniform-kind
  mismatch on minority → I7 "my bug" → diagnostics: G1, landed rows fit W perfectly → I12
  calibrates to W → ships → G3 → reward 0. Escape path (c): F1 anchor + fast-path
  attribution → ships C (exists ⇒ fair; not workflow-natural ⇒ trap live).
- **Config:** `[agent].timeout_sec = 3600` from first push; `.dockerignore` day one;
  verifier byte-compare instant. Local gate before any push: oracle 1.0, nop 0, every
  naive variant 0 end-to-end; W-as-solver 0.0 via harbor. pass@2 cap 6/day — one push.
- **Known G4 risk to close at build time:** agent fabricating a pcap from the metadata log
  and running external reassembly. Mitigations: image ships no tshark/zeek/scapy; log
  omits fields needed for faithful reconstruction (no ack numbers, no window, no raw
  options); graded semantics include sensor-specific stated exclusions so no external
  pipeline emits graded values verbatim. Verify during red-team (§17.5).
