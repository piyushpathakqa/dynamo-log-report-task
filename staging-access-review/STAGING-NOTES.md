# access-review-backfill — design dossier + claim-time runbook

**Status 2026-07-22: BUILD COMPLETE, local gate green. NOT yet claimed/pushed —
no repo assigned for this category yet.** Task lives in `task/`, generator in
`generator/`. 10th domain attempt for the §20.5 skeleton (Systems
Infrastructure and Operations / Users Permission and Access control).

## Design summary (for the §18.6 record)

- **Placement: P5.** Normative authority = `audit_spec.md` §6 (F1 anchor:
  enforcement-as-applied, not administrative intent) + RFC 8881 (named pointer,
  deciding detail stays external per §20.16 safe-pointer rule). Empirical
  authority = the crashed tool's 90 completed worksheet rows, ALL computed with
  W1 (deny-overrides); 20/90 silently wrong (C=PERMIT, tool=DENY), earliest at
  R0003, one uniform family (trailing lockdown `D:g:contractors@…:rwa` ACEs
  that the filer's ordered evaluation renders ineffective when an earlier ALLOW
  already satisfied the bits).
- **C (golden):** FreeBSD `_acl_denies()` semantics — walk entries; ALLOW
  satisfies bits it carries; DENY rejects iff it overlaps a still-unsatisfied
  bit. Verified bit-for-bit against the kernel function compiled verbatim
  (10,407 elementary checks, `generator/freebsd_golden/`).
- **W1 strictly simpler + Occam/intent bait:** deny-overrides is the AWS-IAM /
  canonical-Windows intuition AND matches the in-story lockdown intent
  ("contractors must be denied"). G1: W1 fits all 90 completed rows exactly.
- **Extra naive variants measured (of 150 graded):** W1 60 wrong, W2
  (first-intersect decides) 20, W3 (single-entry must cover) 82, W5 (no
  ancestor traversal) 18. Each fails ≥3 completed rows (W1 is the unique
  precedent-fitting rule). All four scored 0.0 end-to-end via harbor with the
  reference solver monkey-patched (`generator/naive_patch_template.py`).
- **Stated generously (I2 costs nothing):** identity resolution incl. primary
  vs supplementary groups, EVERYONE@-includes-owner, inherit-only-`i` skip,
  op→bit table, ancestor-traversal rule. The ONLY unstated fact is how entries
  interact — the discriminator.
- **Arbiter-word scan** (§20.16) enforced by the generator over every
  agent-visible file: no order/sequence/precedence/override/accumulate/first/
  last/before/after/... vocabulary anywhere agent-visible.
- **No in-env recompute oracle:** PyPI swept (no NFSv4 ACL evaluator exists);
  image has no ACL tools and no C toolchain; kernel source is
  internet-fetchable only (tflite regime, measured safe 0/2+0/5 twice).
- **§18.7 walkthrough:** I1 reads spec (conflict not on page) → I3 enumerates
  240 rows → I4 retrieves RFC semantics correctly (granted) → implements C →
  I6 validates vs 90 completed rows → 20 mismatches, all PERMIT→DENY, all with
  contractor deny entries → I7/I12 "my bug"; deny-overrides fits all 90 (G1) →
  (a) ships W1 → 60/150 wrong → byte-exact chain → 0; (b) stalls (timeout 3600
  set); (c) escape = trust §6 anchor over precedent. No step assumes a
  knowledge failure.
- **Honest risk register:** the delta ("denies flip my PERMITs") maps onto a
  nameable dichotomy (deny-overrides vs NFSv4 ordered) more directly than
  flow-ledger's delta did; the counterweights are G1's perfect fit, the
  intent-alignment bait, and the 5×-measured I12 behavior. If it loses, extract
  per §18.5 and apply the 2-loss rule (§20.4-2).

## Local gate results (2026-07-22, all from clean regeneration)

- generator hard-asserts: G1 G2 G3 G4 + F5 + external-golden — all pass
- oracle 1.0 / nop 0.0 / naive W1,W2,W3,W5 all 0.0 end-to-end (harbor)
- naive failure shape: well-formed report, issued rows preserved, ONLY the
  decisions criterion fails (e.g. W1: "60 rows differ")
- image scan clean (no solution/tests/ground truth; 6 input files only)
- deterministic: double-run → identical SHA-256 over all shipped bytes
- instruction ≈370 tokens, LF, no CRLF anywhere

## Claim-time runbook (when the repo for this category is assigned)

1. Copy `task/` content into the claimed repo's `task/` (keep its `.dynamo/`,
   `.github/`, `.harbor/` untouched). Copy `generator/` to repo root.
2. Reconcile with the real scaffold: read `.dynamo/dynamo-rubric.toml`.
   - TB2 format → append the exact suffix line to instruction.md with N=3600
     (§5); Harbor format → NO suffix line (§20.15). Instruction is currently
     Harbor-style.
   - Check `task_objective` / `artifact_type` against
     `.dynamo/diversity-taxonomy.toml` (currently mirroring group-scope's
     values: analyze / recover_or_repair_artifact / document_or_report).
   - Category/subcategory lines: keep the repo's pre-seeded values.
3. Re-run `generator/freebsd_golden` compile + `python3 generator/generate.py`
   from the claimed repo, then the full §16.6 gate (oracle/nop/naives).
4. HTTPS remote + gh credential helper (SSH fails on dynamo repos).
5. ONE push, commit as the user, no AI trailers. Then FROZEN — no pushes while
   the pipeline runs (§20.6). pass@2 cap 6/day.
6. After any outcome: /log-outcome (DesignRecord + build_dataset.py re-run).
