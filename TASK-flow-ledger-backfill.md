# TASK dossier — dynamo/flow-ledger-backfill (Security / Network Forensics)

**Repo:** dynamo-b759b72-security · **PR:** #1 (fork piyushpathakqa, branch `submission`)
**Status (2026-07-21): pass@2 0/2 (2 valid fails) · rubric PASS all 31 · duplicate UNIQUE
· validation green · pass@5 + deep review PENDING. DO NOT PUSH while the pipeline runs
(any push re-rolls everything, §20.6). See §20.25 for the logged outcome.**

## Design (P5, §20.5 skeleton, 9th domain)

- **Story:** Ashport Systems NDR sensor `sen-04`; flow summarizer crashed at
  10:57:23.417 UTC (epoch 1781780243417) during a traffic surge; segment log kept
  recording (09:00–12:30 UTC). Backfill the 59 ledger records whose emission point
  falls in the outage window.
- **Crux (C):** per-direction bytes = payload-stream size in mod-2^32 sequence space
  (interval union of data segments; repeats/coalesced overlaps add only new coverage;
  keepalive garbage byte at covered position adds 0; SYN/FIN carry no payload).
- **W1 (Occam bait / poison rule):** `sum(dlen)` per direction.
- **Poison:** landed ledger = 75 rows; ALL 15 divergence-regime rows carry W1 values
  (in-story load-shedding fast path; congestion → both loss and shedding, so the
  G1-enabling correlation is realistic). Digest-sealed (F3). Earliest poisoned row
  index 8.
- **Other measured naive variants:** W2 span incl. SYN slot, W3 exact-dup-only dedup,
  W4 phantom slots, W5 PSH-only. All 0.0 end-to-end via harbor.
- **Fairness anchors:** F1 ("Each record must hold exactly the values the flow-record
  specification defines"), F2 (ledger "as issued", leave unchanged), spec notation-only
  wording ("payload stream ... derived from the recorded segments' sequence numbers and
  payload lengths") — one inference step from the delta; forbidden-word grep enforced
  in generator (`FORBIDDEN` list).
- **External golden (§20.9):** `generator.py --zeek` synthesizes real pcaps from the
  same event streams, runs dockerized Zeek, asserts C == conn.log orig/resp_bytes —
  139/139 flows, 0 mismatches.
- **Numbers:** 8,188 segment lines · 139 flows · graded 59 (W1 wrong on 33, W2 57,
  W3 19, W4 59, W5 28) · agent timeout 3600 · verifier 120.

## Measured pass@2 mechanism (from platform analyzer)

Both trials, identical: implemented interval union correctly → validated vs landed
rows (I6) → ~10 mismatches → found `sum(dlen)` reproduces all 75 (G1) → called it
"the validated reconstruction method", rewrote, shipped W1 → +1460 on first graded
row → chained digest → 0. Trial WSxyMQy had the byte-exact correct output on disk
and overwrote it (near_miss FAIL on proximity; everything else PASS). Both read the
F1 sentence and violated it at the same step.

## Rules of engagement

- FROZEN: no pushes to the PR for any reason while gates run; answer advisories with
  comments only (§18.9-13).
- If pass@5 blocks on infra strata: request rerun via PR comment, never push (§20.17).
- Re-roll variance is priced at ~1 solve per ~30 trials (§20.24) — a 1/5 with ≥3 valid
  fails still passes the gate; do not panic-redesign.
- Generator + naive ledgers + playbook copy are committed in the fork; agent image
  contains only `data/` (segments, ledger, spec).
