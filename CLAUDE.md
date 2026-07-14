# Project instructions — Dynamo task authoring

**When the task is to author/build a Project Dynamo (Terminal-Bench 2 / Harbor) task —
whether from scratch, after claiming, or after a review send-back — you MUST, before
designing anything:**

1. **Open `DYNAMO-REFERENCE.md` and read §16.13 first** (the author-model-independent
   framework), **then §18 (THE FABLE HANDOFF — mandatory)**: the adversary dossier
   (§18.2), the placement ladder (§18.3 — verdicts are measured, do not re-litigate
   P1–P4), the poisoned-oracle construction manual (§18.4, the only lever measured to
   beat Opus-4.8 here: 0/2 twice, accepted), and run BOTH pre-flight checklists
   (§16.13 + §18.6) plus the §18.7 simulated-adversary walkthrough before choosing a
   crux. Do NOT invent a crux from introspection ("what would be hard?") — mine it
   from the observed-failure library (§11.2, §11.4, §16.11, §16.12, §18.1). Knowledge/
   derivation/retrieval cruxes are measured dead (10/10 solved); attack measured
   WORKFLOW invariants instead (§18.5).
2. Then use `DYNAMO-REFERENCE.md` end-to-end: §16.5 generator skeleton (with hard-asserts:
   oracle == external golden via subprocess, a plausible naive solver MEASURABLY fails ≥N
   eval rows, no leaks), §13 pre-submit gate, §15 reviewer lens.
3. Validate locally before every push (oracle 1.0, nop 0, every naive variant 0); remember
   pass@2 is capped 6/day per repo — never push to pass@2 until the local naive-fails check
   is strong.

Key reference files in this repo:
- `DYNAMO-REFERENCE.md` — full author+submit playbook. **§16.13 is the mandatory starting
  point for any authoring task.** Copy this file into each forked task repo.
- `LEARN-tflite-int8-replay.md` — plain-language ML explainer + glossary (learning).

The single durable lever that has twice taken Opus-4.8 to pass@5 = 0/5: an
**execution/porting crux** (e.g. C `>>` floor vs Python `//` truncate in gemmlowp int8
requant), graded exact-match against an external standard, no feedback, all-or-nothing over
a boundary-hunted batch. Reasoning cruxes lose to Opus — see §16.11.

Commit as the user (no AI-attribution trailers). This repo's memory only auto-loads for
sessions rooted in this directory — start Dynamo sessions here, or open `DYNAMO-REFERENCE.md`
explicitly.

After every task outcome (pass@ result, rubric verdict, review reply, design-table
kill): append a DesignRecord/Principle to `training-data/build_dataset.py` and re-run
it — this maintains the local-model fine-tuning dataset (see training-data/README.md).
