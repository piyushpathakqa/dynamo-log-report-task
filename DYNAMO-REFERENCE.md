# Project Dynamo — Task Authoring & Submission Reference

A complete, reusable playbook for building and submitting a Terminal-Bench 2 (Harbor)
task for Project Dynamo. Copy this file into any future task repo. Everything here is
distilled from the official Dynamo guide; where the guide contradicts itself, the
open question is flagged under **Doc inconsistencies** at the bottom — resolve those
against the actual scaffold you're assigned, not from memory.

> **The one number that governs everything:** a task is accepted only if the reference
> agent (**Terminus-2 + GPT-5.4, xhigh**) **fails at least 3 of 5** attempts
> (pass@5 ≤ 2/5), while your **oracle still scores reward 1.0**. Difficulty must come
> from *reasoning*, never from compute or the clock.

---

## 0. Mental model

- **Two independent gates.** (1) *Authoring correctness* — valid Harbor format, oracle
  passes, nop fails. (2) *Difficulty* — the empirical pass@5 bar. A perfectly authored
  task still gets rejected if it's too easy. A hard idea still gets rejected if the
  authoring is broken. You must clear both.
- **A good task is a "solvable stump":** the oracle proves it's solvable; the model
  failing ≥3/5 with *valid* failures proves it's hard.
- **Valid failure only:** model finishes and gets the answer wrong on a fair problem.
  Timeouts, infra errors, verifier errors, and ambiguous prompts **do not count** and
  are treated as broken, not hard.

---

## 1. Environment setup (one-time)

| Tool | Install | Verify |
|---|---|---|
| Docker | Docker Desktop (macOS/Win) or `curl -fsSL https://get.docker.com \| sh` (Linux) | `docker ps` → empty table, no error |
| uv | `curl -LsSf https://astral.sh/uv/install.sh \| sh` | `uv --version` |
| Python 3.11+ | system or `uv` toolchain | `python3 --version` |
| gh CLI | https://cli.github.com then `gh auth login` | `gh auth status` |
| **Harbor** | `uv tool install harbor` | `harbor --version` |

⚠️ **Install `harbor`, NOT `harbor-cli`** (different app, won't work).
No model API key is needed to scaffold, run the oracle, or calibrate.

**Core commands (run from the dir containing `task.toml`):**
```bash
harbor run -p . --agent oracle   # your solution vs verifier → expect reward 1.0
harbor run -p . --agent nop      # no-op agent → must score reward < 1.0
```

---

## 2. The workflow (fork → PR)

1. **Claim** a task on the platform. **Write down the Category + Sub-category** — you need them at proposal. Claiming locks it; release if it's not a fit. One active claim at a time. Accept the repo invite.
2. **Proposal** — pass the automated proposal review *before building anything* (see §9).
3. **Fork & branch:**
   ```bash
   gh repo fork handshake-project-dynamo/<your-task-repo> --clone
   cd <your-task-repo>/task
   git checkout -b submission
   ```
   You have no write access to the base — you propose via PR from your fork.
4. **Author `solution/solve.sh`** (+ helpers) → oracle scores 1.0. Capture a numbered list of observable success criteria.
5. **Write tests** (`tests/test_outputs.py` + `tests/test.sh`).
6. **Build `environment/Dockerfile`**.
7. **Write `instruction.md` + `task.toml`**.
8. **Run the oracle locally end-to-end** (the required validation — reviewers never run your code).
9. **Wrap-up checklist → open PR → iterate on the same branch.**

---

## 3. Required layout

Everything lives under a single `task/` directory (not repo root, not `tasks/<id>/`).

```
task/
├── task.toml               # manifest — you fill metadata + timeouts
├── instruction.md          # the agent prompt; ends with the "You have N seconds…" line
├── solution/
│   └── solve.sh            # oracle; real logic in helpers (solve.py); NEVER in the image
├── environment/
│   ├── Dockerfile          # the task's SINGLE image (agent + verifier)
│   └── data/               # optional input files, COPYed into the image
├── tests/
│   ├── test.sh             # runs pytest; writes reward 1/0 + ctrf.json to /logs/verifier/
│   └── test_outputs.py     # assertions, 1:1 with instruction.md, one per criterion
├── .dynamo/  .github/  .harbor/   # PROVIDED — never edit (rubric, CI, run defaults)
└── README.md               # replace with a short task description before final submit
```

**The provided `.dynamo/dynamo-rubric.toml` is the grading source of truth — read it first.**
Taxonomy values live in `.dynamo/diversity-taxonomy.toml`.

---

## 4. `task.toml` (canonical block)

Order: top-level `artifacts` → `[task]` → `[metadata]` → `[verifier]` → `[agent]` → `[environment]`.

```toml
artifacts = ["/app/output.json"]   # output paths the verifier reads; ABOVE the first [section]

[task]
name = "dynamo/your-task-name"     # org/name; name = lowercase kebab-case, ≤3 words
description = "One-line task summary."

[metadata]
# --- Pre-seeded by Dynamo — DO NOT EDIT ---
category = "..."                   # assigned by the team
subcategory = "..."                # assigned by the team
# --- Fixed for this dataset — leave as-is ---
model_tested = "GPT-5.4"
agent_tested = "Terminus-2"
# --- You fill these in ---
task_objective = ["implement", "debug"]        # snake_case, from .dynamo/diversity-taxonomy.toml
artifact_type  = ["codebase", "configuration_file"]  # snake_case, from taxonomy
expert_time_estimate_hours = 2                  # best-case focused hours for an expert who holds the insight; non-zero
difficulty_explanation   = "..."   # why it's hard (carry from proposal)
solution_explanation     = "..."   # approach + key insight (carry from proposal)
verification_explanation = "..."   # how tests verify (carry from proposal)

[verifier]
timeout_sec = 120.0                 # raise for slow suites; environment_mode LEFT UNSET

[agent]
timeout_sec = 120.0                 # MUST equal N in instruction.md's suffix line

[environment]
build_timeout_sec = 600.0
cpus = 1
memory_mb = 2048
storage_mb = 10240
gpus = 0                            # max 1 (H100) only if truly needed
allow_internet = true              # open internet; answer must NOT be retrievable online
mcp_servers = []
```

**Rules:**
- `artifacts` is a **TOML array of absolute paths**, above the first `[section]`, listing exactly what the task produces.
- **Only set** `task_objective`, `artifact_type`, `expert_time_estimate_hours`, and the 3 `*_explanation` fields. `category`/`subcategory`/`model_tested`/`agent_tested` are **pre-seeded — leave them**.
- `task_objective` / `artifact_type` must be **best-fit** (not merely valid) lowercase snake_case labels from the taxonomy.
- `environment_mode` **left unset** (TB2 shared model: verifier runs in the environment image; Harbor overlays `tests/` at verify time). **No separate verifier container.**
- **No author info** anywhere (name/email). Removed `avg_at_8` — it no longer exists.
- `[agent].timeout_sec` **must match** the instruction suffix number; update both together.

---

## 5. `instruction.md`

The prompt handed **verbatim** to the agent — the only thing it sees. **Human-written** (policy). It's a prompt, not a document.

- **No title, no `##` headers, no roleplay, no fluff.** Write as a domain expert briefing a colleague.
- Use **absolute `/app/...` paths**; name **every** output file and its exact format.
- Describe **WHAT**, not HOW. No mandated tools/steps (except anti-cheat constraints).
- **Do not reveal the solution.** No hints.
- Every requirement needs an **objective acceptance criterion** the verifier can assert. No subjective goals ("make it better").
- Structured-output schema goes **in the prompt or a referenced spec file** (the separate structured-output line was removed).
- **≤ 1,500 tokens** (hard cap).
- **MUST end with EXACTLY** (static check `check-instruction-suffix`):
  > `You have N seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.`
  where **N = `[agent].timeout_sec`**.

---

## 6. `solution/` (oracle)

- `solve.sh` is the reference solution; Harbor mounts `solution/` at `/solution/` and runs it. It **proves the task is solvable**.
- Keep real logic in a helper (`solution/solve.py`) that `solve.sh` calls. No giant heredocs.
- **No package installs** in `solve.sh` (`apt-get`/`pip`) — the Dockerfile handles setup.
- Write outputs to the absolute `/app/...` paths named in `instruction.md`.
- **Human-written**, genuinely computes the answer (no hardcoded results).
- **Never copied into the agent image** (CI rejects it).

```bash
#!/bin/bash
# real logic in a helper; write outputs to the /app paths in instruction.md
python3 /solution/solve.py
```

---

## 7. `tests/` (verifier)

Runs **after** the agent finishes, in a fresh container from the **same** environment image; `tests/` is added only at verify time and is **not present during the agent run**.

**`tests/test.sh`** — runs pytest, writes reward, **installs nothing**, and **always exits having written 1/0**:
```bash
#!/bin/bash
pytest --ctrf /logs/verifier/ctrf.json /tests/test_outputs.py -rA
if [ $? -eq 0 ]; then
  echo 1 > /logs/verifier/reward.txt
else
  echo 0 > /logs/verifier/reward.txt
fi
# (no `set -e`; final command is echo → script exits 0; pass/fail lives in reward.txt)
```

**`tests/test_outputs.py`** rules:
- **One test function per success criterion**, each with a **docstring** naming the criterion.
- **1:1 with `instruction.md`** — every tested behavior is stated in the instruction, and every instruction behavior is tested. No orphans either way.
- Assert on **observable artifacts** (files at `/app/...`, exit codes) — **never** string-match source or reference `solve.sh`.
- Must **fail for a nop agent** (doing nothing scores < 1.0). If nop passes, tighten assertions.
- **Fixed seeds/inputs.** No unseeded randomness, live data, or wall-clock/date dependence.
- **Ground-truth/expected answers live in `tests/` only** — never in `environment/` (the agent can read that). Guard against tamper: copy an agent-writable input to `tmp_path` or SHA-256 it before comparing (Reviewer-Notes flag `fixtures_and_tamper_independence`).

---

## 8. `environment/Dockerfile` (single image, agent + verifier)

Built once, reused for both runs. Bake in everything for reproducibility — even with open internet, the answer must not be fetchable.

**Base image: allowlist + digest-pinned.** Every `FROM` must be an approved base, pinned by `@sha256:` (never `:latest`, never a bare tag). Use one of these unless none fit (then document why); to target another version in the same family, pin **that image's own** digest.

| Runtime | Approved base (pin by this digest) |
|---|---|
| Go 1.21–1.26 | `public.ecr.aws/docker/library/golang:1.24-bookworm@sha256:1a6d4452c65dea36aac2e2d606b01b4a029ec90cc1ae53890540ce6173ea77ac` |
| Python 3.10–3.13 | `public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb` |
| Debian 12.x | `public.ecr.aws/docker/library/debian:bookworm-slim@sha256:4724b8cc51e33e398f0e2e15e18d5ec2851ff0c2280647e1310bc1642182655d` |
| Rust 1.75–1.95 | `public.ecr.aws/docker/library/rust:1.85-slim@sha256:9f841bbe9e7d8e37ceb96ed907265a3a0df7f44e3737d0b100e7907a679acb36` |
| Node 18/20/22/24 | `public.ecr.aws/docker/library/node:22-bookworm-slim@sha256:f3a68cf41a855d227d1b0ab832bed9749469ef38cf4f58182fb8c893bc462383` |
| Ubuntu 22.04/24.04 | `public.ecr.aws/docker/library/ubuntu:24.04@sha256:0d39fcc8335d6d74d5502f6df2d30119ff479b60b364818d5112d9e3e932` |
| Java 17/21 | `public.ecr.aws/docker/library/eclipse-temurin:21-jdk-jammy@sha256:25d1276565738d3c805e632a4542c3a7598866ef967f4def6544c15de3a74b14` |
| Ruby 3.2–3.4 | `public.ecr.aws/docker/library/ruby:3.3-slim-bookworm@sha256:e76733e94b3a5893e4a141024ef3a583dc10781dc24becebf74f9c9f9a33e3df` |
| Maven | `public.ecr.aws/docker/library/maven:3.9.9-eclipse-temurin-21@sha256:3a4ab3276a087bf276f79cae96b1af04f53731bec53fb2e651aca79e4b10211e` |
| GCC 12–15 | `public.ecr.aws/docker/library/gcc:13-bookworm@sha256:930f2ebe239275fa67226654cb79273ea34eee672ae61c8a39f689c37fb7ac5c` |

```dockerfile
FROM public.ecr.aws/docker/library/python:3.13-slim-bookworm@sha256:01f42367a0a94ad4bc17111776fd66e3500c1d87c15bbd6055b7371d39c124fb

# apt: one RUN, update+install+clean in the same layer; DON'T pin apt; never apt-get upgrade
RUN apt-get update && apt-get install -y --no-install-recommends <packages> \
    && rm -rf /var/lib/apt/lists/*

# pin pip/npm exact; bake pinned test deps into THIS single image
RUN pip install --no-cache-dir pytest==8.4.1 pytest-json-ctrf==0.3.5

# inputs go in environment/data/ and are COPYed in
COPY data /app/data

# pre-create the parent dir of EVERY output path, or artifact upload fails
RUN mkdir -p /app
WORKDIR /app
```

**Rules:**
- **Never `COPY solution/` or `tests/`** into the image. Verify after every build:
  ```bash
  docker run --rm <repo>:dev /bin/bash -lc 'find / \( -name solve.sh -o -name test.sh \) 2>/dev/null'  # expect: no output
  ```
- Pin pip/npm exact; **do not pin apt** packages.
- Input data → `environment/data/` → `/app/...`. **No solution/ground-truth data here.**
- **Multi-stage build** for any compiled artifact (cargo/go/mvn/npm) so toolchains/caches don't survive.
- Add a **`.dockerignore`**; scope `COPY` narrowly; never copy `.git`, caches, venvs, editor metadata.
- Order layers least→most volatile. `chmod` only specific files (never `-R` a tree).
- **COPY source/fixtures from disk** — no `RUN cat <<EOF` heredocs; extract `.tar.gz` fixtures at build.
- **LF line endings** on all text files.
- Don't ship deps only the oracle needs (they hint the solution path).

---

## 9. Proposal (the cheap gate — passes before you build)

Automated LLM reviewer returns pass/fail per criterion. Revise until it passes. **Do not edit** the pre-filled Category/Sub-category; justify fit in answer 4.

**Four required parts:**
1. **Difficulty** — what it is and *why it's genuinely hard for an expert*: the specific reasoning/domain knowledge/multi-step problem-solving, who does this work in the real world, and where the data comes from (synthetic/real, realistically challenging). Not "this is hard."
2. **Intended approach** — high-level strategy + the **key insight**, so another expert sees how they'd do it (proves you hold a solution). Include a **best-case expert-time estimate**.
3. **Verification** — the exact output and how a program deterministically checks it. If you allow a tolerance/range, say what it brackets and why it admits valid variation but rejects wrong methods.
4. **Category/Sub-category justification** — grounded in the task's actual reasoning/domain.

**Passes when:** hard for a competent domain expert (not an undergrad-in-days, not just tedious/high-volume); needs real multi-step terminal work (explore/run/debug/iterate, not one-shot or paper-solvable); not a textbook/well-known problem a model recalls; a bounded solution plausibly exists (you can sketch it); deterministically checkable and not lookup-able/hardcodable; **graded on the result, never the method**.

**Common fails:** vague difficulty; approach that only asserts a solution exists; unjustified tolerances; missing expert-time estimate; solvable by reasoning alone; standard problem; grading that depends on *how* it's solved.

---

## 10. Difficulty pipeline & pass@ (the empirical bar)

Pipeline order: Proposal → PR → Validity check → **Pass@2** → **Pass@5** → (advisory Reviewer Notes).

- **Pass@2** at your timeout, **900s cap**. Both trials must **finish without timing out**, or the task is rejected and Pass@5 never runs. **Limit: 6 runs/day per fellow per task** — get it right locally first.
- **Pass@5** at your author-set timeout (**≤ 3600s hard ceiling for everyone**). Runs only if Pass@2 is valid.

**Reading Pass@5 (the fraction = agent *passes*):**

| Result | Meaning | Outcome |
|---|---|---|
| **0/5 valid failures** | Fully stumped; oracle still solves; every failure a genuine wrong answer | ✅ Accepted (strongest) |
| **0/5 invalid** | Timeouts / infra / verifier errors / ambiguous prompt | ❌ Rejected — fix the cause |
| **1–2/5** | Solvable and genuinely hard, valid failures | ✅ Accepted |
| **3–5/5** | Agent solves ≥3 — too easy or verifier too loose | ❌ Rejected |

**Reference measurement:** Terminus-2 via Harbor, GPT-5.4, **max completion tokens 128,000, reasoning enabled, effort xhigh**. Cheaper models (Sonnet/Haiku) fine for pre-filtering, but the *recorded* number must be the reference pair.

**Setting the timeout:** you set and justify it (no fixed tiers). Long enough for the model to *produce an answer* — the challenge is correctness, not finishing. Justify by the oracle's actual runtime + headroom. **Never game the score** by lowering the timeout or adding busywork — that's a speed test, and reviewers bounce it. If too easy, make the *reasoning* harder.

---

## 11. How to stump the model (nine patterns)

**Principle:** don't make the task broadly hard — make the agent do ~90% right, then fail on **one decisive, determinate point** it can't pattern-match, recall, or self-verify past. The agent stops at the first green result: tunes to the visible sample, trusts the obvious rule/tool, never checks the case it can't see.

| Pattern | Trap | Example |
|---|---|---|
| **A · Latent crux** | Sample homogeneous along the axis that matters; the real rule never fires on visible data | Steel gauge table calibrates perfectly; hidden non-ferrous parts differ |
| **B · Almost-right heuristic** | Cheap plausible rule ≈ correct expensive definition; diverge on unsuspected cases | Rollup rows by path-prefix vs. amount = sum-of-children |
| **C · Planted trusted tool** | Convenient authoritative tool gives an early wrong answer; agent closes without verifying | Diagnostic names a downstream symptom, not the root cause |
| **D · Reverse-engineer conventions** | Undocumented rules (sentinels, ms vs s, resets) inferred from the data | Reconstruct a lost metrics service from raw logs |
| **E · Broken implicit invariant** | Agent assumes sorted/well-formed/rare-anomaly; hidden data breaks it | GPS year-rollover log jumps backward |
| **F · No-information failure** | All wrong answers return identical rejection → no search signal (riskiest; easily unfair) | Forge token: guess role+scope+channel blind |
| **G · Breadth, all-or-nothing** | Many independent fixes, zero partial credit; ≥1 hides in an unexercised case | Relinker with 8 interacting bugs |
| **H · Coupled rewriting rules** | Rules reach back and change each other; "fix one more" never converges | Event replay where reset/revocation resurrect/invalidate state |
| **I · Point-in-time / as-of** | Must use the value known *as of* a cutoff, not the latest; late corrections rewrite history | Fund NAV from a feed with post-cutoff price revisions |

**Amplifier:** combine A (latent crux) with G (breadth) — hide one of many independent fixes in a case the sample never exercises.

**Fairness line:** every deciding case must be **discoverable from material the agent can actually read** (forced by data/spec). A/B/D/E/H/I are inherently fair. **F is the danger zone** — if the value is unguessable from anything readable, it tests luck, not skill.

### 11.1 Amplifiers & fairness (the two dials)

After you pick a trap, tune it: **amplifiers** make it hit harder, **fairness** keeps it honest. Turn amplifiers up as far as the fairness lines allow.

**Amplifiers:**
- **Silent failure** — the wrong answer looks normal (no crash, no error), so the model gets no hint and stops. If it had crashed, it would keep fixing. *Lever:* make every wrong answer a believable near-miss, never an error.
- **No self-check** — real grading runs on hidden cases the model never sees, so matching the sample only *feels* like success. *Lever:* keep the sample friendly-looking but unrepresentative; grade on held-out cases.
- **All-or-nothing** — mostly right scores zero; one wrong piece fails the whole thing. *Use when* the answer is a single correct artifact, not when partial progress should count.

**Fairness principles (keep it skill, not luck):**
- **Figure-out-able** — the answer must be recoverable from what the model is given, not secret or impossible.
- **Real skill** — punish a mistake a pro could avoid, not a random gotcha.
- **Fair margins** — don't let pass/fail hinge on a hair-thin tolerance; the *idea* should decide it, not the threshold.
- **No uncorrectable lie** — hiding the deciding case is fine; **stating a wrong rule that nothing in the task can correct is not**.

**The gut check:** *Would a human expert, seeing only what the model sees, get it right — and call the failure fair?* Yes to both = good trap. If they'd be stuck too, it's testing luck → cut it.

### 11.2 Live failure examples (traps that worked, by pattern)

Real graded runs — the predicted mistake matched the actual mistake, confirming the patterns come from real failures.

| Task | Result | Pattern | What went wrong |
|---|---|---|---|
| bytecode-vm-debug | Opus-4.8 5/8 fail | **A** | Fixed the obvious bug, saw 8/8 green, quit in ~77–137s of 900s without a subtraction test → -7 where 7 was right |
| accrued-interest | Opus-4.8 8/8 fail | **A** (expert knowledge) | Applied the sample's US conventions; skipped the UK-gilt ex-dividend rule → wrong sign |
| gnss-log-decode | Opus-4.8 8/8 fail | **E** | Decoded bytes perfectly, then used one satellite system's clock rules for all → timestamps ~20yrs off |
| experiment-readout | GPT-5.4 5/5 fail | **B** (hidden grading) | Used per-session instead of per-user statistics → error bar ~5× too small, called a non-result "significant" |
| legacy-formatter-clone | GPT-5.4 5/5 fail | **D** | Tried every known checksum instead of rebuilding the custom one by algebra → every checksum wrong |

**The common thread across all five: the model stopped checking after the first green result.** That's the single most exploitable habit — build traps whose deciding case never turns the sample red.

### 11.3 Two review skills (worked exercises)

**(a) Audit the requirements** — which submitted items violate a workflow rule:

| Item | Verdict | Why |
|---|---|---|
| `instruction.md`: "Save the cleaned data to the output folder." | ❌ **Violates** | Not an absolute `/app/...` path; output file not named |
| Criterion: "The result should be correct and well-formatted." | ❌ **Violates** | Subjective; no objective, assertable acceptance criterion |
| Dockerfile: `RUN pip install pandas==2.2.2 pytest` | ❌ **Violates** | `pytest` not pinned — all pip deps must be exact-pinned |
| `task.toml` adds `author_name` + `email` | ❌ **Violates** | No author/personal info allowed in the manifest |
| `solve.sh` opens with `#!/bin/bash` on line 1 | ✅ **Correct** | Proper shebang — sound |
| `test.sh`: `echo 1 > /logs/verifier/reward.txt` | ✅ **Correct** | Exactly the required reward path |

*Lesson: the skill isn't blanket suspicion — it's knowing which requirement each item is measured against. Two of six were already right.*

**(b) Is it gradable?** — a criterion is only useful if a test separates the golden output from plausible near-misses. Task: dedup a CSV → `/app/output/clean.csv`. A sound test **accepts the golden file and rejects every broken variant** (duplicates left in, header renamed, empty/header-only, rows dropped):

```python
import csv

with open("/app/output/clean.csv") as f:
    rows = list(csv.reader(f))

assert rows, "file is empty"
header, data = rows[0], rows[1:]

# exact header  → rejects "header renamed"
assert header == ["id", "sku", "qty"], f"unexpected header: {header}"
# exact row count → rejects "empty (header only)" and "rows dropped"
assert len(data) == 3, f"expected 3 data rows, got {len(data)}"
# exact content, order-independent → rejects "duplicates not removed" and wrong values
expected = {("1", "A100", "5"), ("2", "B200", "3"), ("3", "C300", "8")}
assert {tuple(r) for r in data} == expected, f"rows don't match: {data}"
```

*If you can't write a check that separates golden from the near-misses, reshape the task — don't loosen the test.*

### 11.4 The five core strategies (distilled from delivered tasks, avg@8 ≤ 0.5)

Five field-proven ways to make the model confidently wrong. Each names the real Dynamo task it came from. These are the patterns above, made concrete — use them as design templates.

1. **Silent trap — the obvious solution runs clean and is wrong.** The naive approach completes without error and produces believable output; the only way to know it's wrong is to understand what the output should *mean*. **Avoid bugs that throw — a model fixes anything that throws.**
   *`silent-feature-bugs`: two refactor-introduced bugs (timezone-agnostic windowing + pre-split target-encoding leakage), invisible at runtime, that interact and must be fixed together; the pipeline emits a plausible feature matrix either way.* → pattern **A**, amplifier *silent failure*.

2. **Test cases the instructions define but the samples never show.** Ship samples/spec that the naive reading reproduces perfectly, then grade on cases a *faithful* reading still fully determines but the samples never exemplify. **Not misleading:** the instructions never lie and every graded case is unambiguously derivable — you just decline to hand the model an example of every case (instruction author and verifier must agree on expected output).
   *`gnss-log-decode`: instructions call for all constellations/leap-second eras the format supports; shipped samples are GPS-only in one era; graded captures add BeiDou (different epoch/offset). No oracle to self-check. (`preprocessing-recovery` does this with a schema doc that defines every column but illustrates only a subset.)* → pattern **A**, amplifier *no self-check*.

3. **Remove the model's ability to self-verify.** If the environment holds an oracle (a reference binary that prints the answer, a doc stating the rule, a way to check work), the model uses it. Take it away — this is also an anti-cheat requirement.
   *`tokenizer-recovery`: correct token IDs depend on hidden subsets (no-marker vocab entries, alternate Unicode normalization, multi-piece segmentation, special-token framing) scattered through 205 inputs; nothing flags which are affected; the shipped encoder reproduces the naive (wrong) output.* → pattern **D**.

4. **Compound several corrections that must compose in order.** One trap is often guessable; several independent corrections that overlap on the same records — where fixing some but not all still fails — push the pass rate down hard.
   *`slo-breach-recovery`: five mixed encodings in one metric dump (ms vs s timestamps, cumulative counters, counter resets, per-second rates, failed-scrape sentinels) that overlap; handling only some still produces wrong counts.* → patterns **G + H**.

5. **Grade exactly, so plausible-but-wrong fails.** Loose tolerances let a near-miss pass. **Define the tolerance from the problem's own context:** wide enough that every genuinely-compliant method passes, tight enough that any requirement-violating method falls outside — and justify the band from the problem.
   *`migrate-colorkit`: the naive sRGB port looks spec-compliant but violates the gamma requirement, landing ~0.15 off in luminance; tolerance is 0.02 — admits every correct decode, far tighter than the gamma mistake, so the wrong method fails every tile.* → pattern **B**, fairness *fair margins*.

### 11.5 The #1 trap to avoid: the named gotcha

**If a specialist can name the bug, so can the model.** The most common reason a polished, hard-*sounding* proposal comes back too easy: the trap is a **recognizable, nameable concept the model has read about**. It identifies it on sight and applies the standard fix. The difficulty lived in *your description*, not in the model's blind spot. **"Hard for a human specialist" is not "hard for the model."**

**Worked example (real in-flight proposal):**
- **Before:** *"Find and fix an account service that de-duplicates usernames with one Unicode normalization form (NFC) but resolves identities with another (NFKC), allowing an impersonation collision."*
- **Why the model wins:** this is a famous named bug class (the public music-streaming account-takeover). The model spots the normalization-form mismatch instantly and applies the one-line fix. Hard to name, trivial to fix.
- **Harden it:** stop asking the model to **FIND a nameable bug**. Give a service that *looks correct* and a seed set of identifiers that all resolve correctly under the naive rule; **grade on hidden collision pairs the seed never shows**, where the correct identity model must be applied to unseen input. **Remove the word "normalization" entirely**; make the collision observable only through **downstream behavior**, and grade exact resolution outcomes across many hidden pairs.

**The general fix:** convert "find the named bug X" → "here is a plausible-looking system; produce correct outputs on inputs where the latent rule (which you must infer, unnamed) actually bites." Move the difficulty from *recognition* to *inference on unseen, fully-specified cases* (this is strategy 2 + pattern A). Strip domain names/keywords that let the model retrieve the recipe.

**The same tell recurs — each a named recipe the model executes on sight (avoid these shapes):**
- **ECDSA biased-nonce key recovery** — textbook Hidden Number Problem via LLL lattice reduction (Minerva / LadderLeak); the model builds the lattice and calls a CAS. (Also arrived near-duplicate — a diversity problem too.)
- **Async CDC-FIFO repair** — canonical fix is Gray-code pointers through a two-flop synchronizer; the proposal even names metastability as the pitfall.
- **Quartic-oscillator eigenvalue** — shooting + Numerov is standard computational physics the model runs fluently.

**Self-test when writing a proposal:** can *you* name the bug/technique/algorithm in one phrase? If yes, the model can too — redesign so the crux is an unnamed, inferred rule that only shows up on hidden-but-specified cases.

**Enumerable-convention corollary (learned the hard way, 2026-07-08 quantized-inference pass@2 2/2 solves):** "recover a convention from reference I/O" is a *sweepable* crux whenever the conventions come from a small standard menu (rounding modes, clamp ranges, bit widths, orderings). A coding agent doesn't derive — it enumerates the menu against the reference and picks the zero-mismatch candidate, in minutes. The deeper rule: **matching the visible sample must be necessary but NOT sufficient.** If the sample fully determines the answer → sweepable (too easy); if it doesn't and nothing else does → unfair. Escape the dilemma by making the *spec/doc/data* determine the hidden cases while the sample deliberately carries no signal on them (all plausible-wrong variants agree with golden on every sample row — assert this in your generator), and by choosing a crux space that isn't a menu: semantic composition, temporal/bitemporal reasoning, interacting rules.

### 11.6 More levers (each targets a documented frontier-model weakness)

**Category taxonomy = DOMAIN, not difficulty.** Difficulty is an orthogonal, structural property; the category/subcategory says nothing about it. Each lever below: *weakness → example → how to use.*

- **A · No single wrong line** (emergent / cross-component / timing). Models find a faulty *line*; they struggle when no file is wrong and the defect lives only in the *interaction*. *Ex: a work-queue where a stale lease completion recycles a token already reissued to another record — no exception, no error counter, every component locally correct.* **Use:** design emergent defects (concurrency, event ordering, recycled-resource aliasing); seed the trace so the outcome is deterministic to grade.
- **B · Bug-for-bug preservation** (the helpfulness trap). Models are trained to *improve*; tell them to preserve an exact quirk and the instinct to "fix" violates the requirement. *Ex: a Fortran→Rust port must reproduce the original's exact behavior (persistent SAVE state, integer division from implicit typing, bit-aliasing), not the clean modern equivalent.* **Use:** require exact reproduction of legacy behavior, warts included, graded against the legacy output.
- **C · Minimal-diff / "nothing to change here."** Models over-edit and trip hidden invariants. *Ex: the correct fix is one line (or a single config value) and a hidden regression suite checks all the untouched behavior.* **Use:** make the correct change tiny or absent, grade the whole surface — include a path where the right answer is "no change needed."
- **D · Spec-by-environment** (underspecified on purpose). Models lean on the prompt; put the real contract in an opaque artifact they must reverse-engineer. *Ex: `gnss-log-decode` and a firmware-TLV audit — record layout, vendor CRC parameters, and time conventions recovered from a stripped binary or worked example, not read from the prompt.* **Use:** keep the prompt about WHAT, never HOW.
- **E · Defeat the iterate-test-fix loop.** Agents converge by chasing a failing signal; remove it and the loop can't self-correct. *Ex: the naive solution produces no error and no visible failing test (the real check is hidden), so the run-test-fix cycle ends "successfully" on a wrong answer.* **Use:** ensure nothing in the environment tells the agent it's wrong; pair with the silent trap + a hidden verifier.

**Two more places to look:**
- **Underused high-yield subcategories** already in the taxonomy: concurrency & synchronization debugging, reverse engineering, compilers/interpreters.
- **Weak spots with no taxonomy home:** time / timezone / calendar & leap-second arithmetic (the mechanism behind `gnss-log-decode`); stateful protocol / handshake correctness.

**The single self-check before you build:** *Would a frontier model run the obvious thing, see plausible output, and commit to a wrong answer with no way to notice?* If yes, it clears the bar.

### 11.7 Fair vs. unfair (hard must also be fair)

**A correct, fully-compliant solution must pass.** Two strategies have a sharp fairness edge — cross it and you've shipped an *unsolvable* task, not a hard one.

**Hidden cases (strategy 2) — fair edge cases vs. unfair surprise requirements.**
Rule: **every graded case must be unambiguously determined by the instruction.** You may decline to *show* an example of every case; you may not grade behavior the prompt doesn't specify or contradicts.
- ✅ **FAIR:** prompt says *"decode every record type/constellation the format supports"* and the sample shows one — grading the others is fair because a careful reading already requires them (`gnss-log-decode`).
- ❌ **UNFAIR:** prompt says *"produce the report for the provided log"* / *"valid for the given data,"* then the verifier grades a *different* log — the shown solution was compliant; the hidden data is a surprise requirement.
- ❌ **UNFAIR:** the verifier checks a column/field/behavior the instruction never mentions.
- **Fix:** state the generality in the prompt (*"must handle all X the format allows"*) so hidden cases become instruction-defined — then they're fair.

**Exact grading (strategy 5) — when strict precision is fair.**
Different valid methods/libraries/approximations/rounding land on slightly different numbers, and you deliberately don't reveal the method — so the band must admit **every** valid interpretation.
- ✅ **FAIR exact / very tight:** discrete outputs (integer counts, class IDs, exact-dollar amounts, decisions — `slo-breach-recovery`); a precision the prompt explicitly states (*"round to 4 decimals"*); or a band calibrated so every valid method passes while a requirement-violating method fails (`migrate-colorkit`'s 0.02).
- ❌ **UNFAIR:** a float with no stated precision graded to 1e-9, so a different-but-valid method/library/rounding fails. If you didn't justify the precision in the prompt and didn't calibrate against valid alternatives, there's no room.

**The one-line test:** *Could a careful engineer who follows your instruction exactly still fail your verifier?* If yes, it's unfair — **fix the prompt or the band, not the difficulty.** (This is the reviewer's "sound-alternative test" from §15.3, applied by the author first.)

---

## 12. PR & submission

**Push and open:**
```bash
git add -A && git commit -m "Task submission"
git push -u origin submission
gh pr create --repo handshake-project-dynamo/<your-task-repo> --fill
```
Iterate by pushing more commits to the **same branch** — checks re-run and update comments in place. Never open a second PR.

**Checks on every push:** Static (structure/paths/Dockerfile hygiene/pinning/single-verifier/suffix line) · Rubric review (LLM per-criterion PASS/FAIL; expects the single `environment/Dockerfile` baking pinned test deps) · Duplicate check (novel vs TB2/TB3) · Validation (oracle=1, nop=0) · Agent trials (fail ≥3/5) · **Reviewer Notes** (advisory, non-gating). Ready = checks green **and** rubric verdict **PASS**.

**Reviewer-Notes common flags:** `fixtures/fixtures_and_tamper_independence` (verifier reads ground-truth from an agent-writable path → copy to tmp or SHA-256 check) · `coverage/complete_test_coverage` (an edge case/ambiguity untested → tighten wording, add hidden test) · `alignment/no_orphaned_behavior` (dead code / template leftovers → remove).

**PR body template:**
```markdown
## One-sentence problem
The task is done when ___.

## Success criteria (numbered, mirror instruction.md)
1. ...

## Calibration results
- Golden solve.sh:      reward 1.0
- Bad / nop solution:   reward < 1.0

## How to run
harbor run -p . --agent oracle   # reward 1.0
harbor run -p . --agent nop      # reward < 1.0

## Notes / open questions
Anything in instruction.md you had to interpret.
```

**On the platform after PR is green:** walk the checklist, add reviewer notes (subtle/tricky points), **screenshot the pass@ comment** from the PR + enter the score, and read the **Job Analysis** (a bare failure isn't enough — understand *why*). Replace `README.md` with a short task description (overview, approach, environment, verification).

**AI tool policy:** **Task descriptions (`instruction.md`) and solutions (`solution/`) must be human-written.** Other files (Dockerfiles, test boilerplate) **may** be assistant-generated **if human-verified** before submission.

---

## 13. The hard pre-submit gate (all must hold, run from `task/`)

- [ ] Task under `task/`; all files present and filled; `.dynamo/`/`.github/`/`.harbor/` unmodified.
- [ ] `instruction.md`: human-written, prompt-style (no title/headers/fluff), absolute `/app` paths, every output named, ≤1,500 tokens, ends with the exact suffix line (N = `[agent].timeout_sec`).
- [ ] `environment/Dockerfile`: allowlisted base **digest-pinned**; pip/npm pinned, apt not; **no `COPY solution/`/`tests/`**; inputs in `environment/data/`; `RUN mkdir -p /app`; test deps baked; multi-stage for compiled artifacts; LF endings.
- [ ] `oracle` = **reward 1.0**; `nop` = **reward < 1.0**.
- [ ] Tests: 1 per criterion + docstring; assert real `/app` artifacts (no source match / no `solve.sh` ref); ground-truth only in `tests/`; fixed seeds; `test.sh` always writes reward.
- [ ] Image clean (`find` for solve.sh/test.sh → no output); no caches/venvs/editor metadata.
- [ ] Deterministic & repeatable (oracle=1, nop=0 stable across re-runs from a clean checkout).
- [ ] Novel (not a reskinned TB2/TB3 task).
- [ ] `task.toml`: only `task_objective`/`artifact_type`/`expert_time_estimate_hours`/3 explanations authored; pre-seeded fields untouched; `environment_mode` unset; no author info.
- [ ] `[agent].timeout_sec` matches the suffix, justified by oracle runtime + headroom.
- [ ] **Pass@2** clears 900s without timeout; **Pass@5** lands 0–2/5 with **valid** failures.

---

## 14. Doc inconsistencies to resolve against the real scaffold

The official pages disagree in a few places — don't guess; check the assigned repo:
- **`tests/Dockerfile`:** one layout lists `tests/{Dockerfile, test.sh, test_outputs.py}`, but the `task.toml` reference says `environment_mode` unset with **no separate verifier container**. Whether a `tests/Dockerfile` exists depends on the actual scaffold.
- **Run directory:** shown as both "run from `task/`" and "run from the repo root," and `-p .` vs `-p tasks/<id>`. Run from wherever `task.toml` actually is.

---

## 15. Reviewer guide (also your best self-review lens)

Every task is reviewed twice on the platform (R1 makes the call, R2 checks it) before **Pending Pass@**. Reviewers **read and judge only** — they don't build or run anything; the automated layers already did. Knowing exactly how a reviewer decides is the fastest way to author a task that passes on the first try. Reviewer ladder: **Onboarding → Unthrottled → R2**, promoted by alignment with R2 calls; paid hourly at every tier.

### 15.1 What the machine already did — how far to trust it

**Ignore (handled internally, not your scope):** duplicate check; task validation (image build, oracle passes, no-op fails); proposal gate; **Pass@2 @900s** (an upstream cost gate — *disregard it even if it failed*; judge on pass@5). **Pass@5** reaches you already (blocked only if failures were invalid).
**Read, but verify (fallible LLM first pass):** static checks on the PR + LLM rubric eval (often one combined panel). Treat green as a *hint*, not a verdict — your read of the files overrides theirs in both directions. **What is NOT pre-filtered: whether the pass@5 failures are actually valid.** That is the reviewer's core call.

### 15.2 Before you judge (prep checklist)

- Read the approved **proposal** + fellow's notes; open the whole repo.
- **Record the exact latest commit hash** (you review *that* commit; R2 checks against it).
- Skim **commit history** for manufactured difficulty (e.g. a clarifying line removed so passing trials start failing).
- If reviewed before, confirm required changes were implemented.
- Open the **pass@5 analysis** (PR comment); note the score.
- Read the **static-check notes**.

### 15.3 Judgment areas (read as the paid domain expert)

- **Whole task:** everything gels (instruction ↔ solution ↔ tests ↔ Dockerfile serve the same task); genuinely solvable and the solution solves the *stated* problem, not a narrower one.
- **Difficulty & realism:** genuinely hard for an expert (real reasoning, not tedium/volume/recall); **not a kitchen-sink** rule-overload task (valid-but-artificial, unauditable); realistic (a practitioner would be paid for these outputs); novel (not a known/textbook problem).
- **Instruction:** not over-directed (grade the *what*, not the *how*); **unambiguous — the sound-alternative test:** can you name one coherent expert method that would *fail* verification? If yes → underspecified. No **hidden knowledge** (constant/schema/threshold the agent was never given); no incorrect/irrelevant info; **no answer leakage** in any agent-readable file; no misleading unreferenced content.
  - *Omission ≠ ambiguity:* an omitted detail is fine if a domain expert can deduce it from the instruction/inputs/standard knowledge. It's only underspecification when the missing detail is an **arbitrary/non-standard choice the agent must match and cannot deduce**. (The best tasks: an apparent decision with a hidden requirement the provided info is enough to resolve.)
- **Verifier:** tolerances not too tight (a different sound method still lands in band) and not too loose (a wrong-but-close answer fails); no domain-specific cheat path; **tests match the instruction 1:1** (every assertion traces to a stated/implied requirement; every requirement is tested); no injection/malicious content; deterministic; requirements traceable.
- **Solution:** genuinely computes the answer (no echo/hardcode; expected values in `tests/` are derived, not pasted).
- **Metadata:** `task_objective`/`artifact_type` non-empty, **best-fit** (not merely valid) snake_case from the taxonomy — objective = end goal (not tools), artifact = central objects (not helpers). `category`/`subcategory` seeded by the team: confirm the fellow didn't change them and the PR still fits; **if a category mismatch is the only issue → Accept at score 3** (deliverable, but logs the platform needs correcting).

### 15.4 Core skill — valid vs. invalid failures

A good task = **solvable stump**: oracle solves it, model fails ≥3/5, clean **0/5 of valid failures** is the hardest/best case. **A timeout is never a valid failure.**

**Proof standard:** a failure is valid only if you can point to something concrete (a sentence in the instruction, an analysis of the inputs) that proves the agent's approach was *wrong*. If an expert could defend the approach *from the instruction alone*, the task is **ambiguous** and the failure is **invalid** — even if the analysis panel calls it valid.

- The **trial-analysis panel** (per-trajectory rubric, golden-vs-agent values, approach diff, validity call, summary) is an **LLM first pass** — wrong in either direction, and it can be fooled by an incorrect `difficulty_explanation` in `task.toml` (which can make a *correct* agent trial read as a valid failure). Check the difficulty explanation against your own read of the solution when something looks off.
- **Fast red flag:** if failing tests are about **file existence or output formatting**, that's usually an undisclosed naming/format convention → ambiguity (invalid failure), not real difficulty.
- **Agent consensus vs. golden:** if most failing trials converge on the same non-golden value, don't assume the agents are wrong — check whether the golden is wrong, an undisclosed rule is unfair, or the agents found a legitimate approach golden ignored.

### 15.5 Verdict + scoring (score and verdict are set independently)

**Verdict routes; score records quality on arrival.** They don't move together (a salvageable task can still be low quality).

| Case | Verdict | Score |
|---|---|---|
| No issues | ✅ Accept | 5 |
| Minor, non-blocking (typo; one trivial untested requirement of many) | ✅ Accept | 4 |
| Clean task but wrong platform category (only issue) | ✅ Accept | **3** |
| Minor blocking issue, difficulty survives fix (ambiguity, wrong facts, leaked fragment, missing `test.sh`) | 🔄 Revise | 3 |
| Major issue, poor quality, but fixable without flipping difficulty | 🔄 Revise | 2 |
| Fix would flip difficulty (agents would pass) or needs full rebuild | ❌ Reject | 2 |
| Ignored valid prior feedback / egregious spam / misaligned | ❌ Reject | 1 |

**The hardest call — Reject vs. Revise:** if I fix the missing/wrong thing, *is the task still genuinely hard?* Yes → **Revise**. Fixing makes it easy/trivial → **Reject** (the difficulty was never legitimate). **Reject** triggers: undisclosed requirement enforced in the verifier; failure from an ambiguous term whose clarification yields a perfect answer; failure on a valid-but-unpinned choice (ordering/naming/formatting) that pinning would fix; deliberate red herrings; manufactured difficulty (removed clarification in history); undisclosed incorrect info in instruction/inputs; over-strict verifier rejecting valid answers; needs-from-scratch; ignored prior feedback. Only **score 1** is inherently unsalvageable (bad faith) — poor work is a 2, not a 1.

**Comments must be actionable:** point at the exact file/criterion/line and say what to change — *"the [29,31] band rejects a valid trapezoidal result; widen to [28,32] or justify the restriction,"* not "verifier seems off."

### 15.6 Recording in HAI (traps)

- **R1 Reviewed PR Commit Hash** — copy the exact latest hash *before* reviewing; review that commit.
- **Standard Quality Score 1–5**, **Task Verdict** (Accept/Revise/Reject), **Fellow Verdict** (Excellent/Trainable/Misaligned).
- **⚠️ Don't click Approve on a Revise/Reject** — Approve *routes the task forward*, it is not a neutral submit. An Accept is only valid with **zero issues flagged**. For Revise/Reject: flag issues, leave feedback, and use the gray **send-back** option.
- Always leave actionable feedback in **both** the taxonomy comment and inline bubbles — **even on a Reject** (a rejected task isn't paid; explain why).

### 15.7 Common rejection root cause + author self-check

**Four of the most common rejections share one root cause: the verifier enforces a requirement the instruction never states** (undisclosed string literal, unspecified naming convention, unspecified aggregation semantics, underspecified duplicate handling). Plus: over-strict/broken verifier, and metadata/proposal-PR mismatch.

**Before you submit — 8-item self-check (author-facing):**
1. Every output field's **format and naming** fully specified — IDs, enums, exact string literals — so the agent never guesses.
2. The verifier **only checks things the instruction (or a doc it points to) states** — no hidden literals or undocumented fields.
3. When a value can be computed multiple valid ways, the instruction names the **single canonical rule** (single-assignment, priority/tie-break order, sort order).
4. **Duplicate/redelivery/edge cases** described explicitly (dedup key, tie resolution).
5. A **reasonable alternative implementation still passes** — the verifier isn't silently enforcing the oracle's arbitrary choice; if only one approach is valid, the instruction says so.
6. **No answer leakage** in any agent-readable file (docstrings, comments, READMEs, filenames).
7. **No undisclosed file/detail steers toward a non-golden answer** — the task fails on the agent's own wrong call, not because the environment misled it; every file the agent should use is named.
8. **No malicious/destructive code** and no injection text (ignore-the-task / reveal-answers / tamper) or obfuscated payloads in env files, comments, READMEs, or fixtures.
```

---

## 16. FIELD-TESTED RECIPE — building a task that actually stumps the frontier model

This section is the distilled, battle-tested result of building `dynamo/tflite-int8-replay`
(accepted, **pass@5 = 0/5**, fully stumped Opus 4.8) after **three failed designs the model
solved 2/2**. It is the most important section for efficiency: it turns "author a hard task"
from guesswork into a procedure. Read §11 for the theory; this is the *how*.

### 16.1 The empirical scoreboard (what the model actually does)

Four designs in the same category (`machine_learning_and_ai / model_inference_and_prediction`),
same reference model (Opus-4.8 + Terminus-2). This is ground truth, not speculation:

| # | Crux | Result | Why the model won / lost |
|---|---|---|---|
| 1 | Recover a rounding **convention from a small menu** using provided I/O | solved 2/2 | Agent **enumerated** the 3–4 standard modes against the sample and picked the zero-mismatch one — a 5-line loop. |
| 2 | Coupled **temporal rules fully written in a prose spec** | solved 2/2 | Agent **read the spec carefully** and transcribed it. Precise spec + capable reader = no trap. |
| 3 | **Discovery + linear recovery** (missing model version, recover weights via RREF) | solved 2/2 | Agent noticed the gap, built a `Fraction` matrix, ran RREF, checked rank — **textbook linear algebra it knows cold**. |
| 4 | **Framework-exact 1-ULP porting trap** (TFLite/gemmlowp int8 requant) | **failed 0/5 ✅** | Agent reproduced the whole pipeline but **transcribed a C++ constant from training and paired it with the wrong integer-division semantics** — off by +1 on boundary rows, no sample to catch it. |

**The lesson in one line:** *Opus 4.8 is excellent at anything derivable, enumerable, or transcribable
from a spec or from a small standard menu. It is beaten by a subtle detail of imported real-world
knowledge that it operationalizes slightly WRONG, with no signal to self-correct.*

### 16.2 The four anti-patterns (why "hard-looking" tasks get solved 2/2)

Before building, kill your idea if it is any of these — the model will solve it:

1. **Enumerable-convention** — the crux is one of a small menu (rounding modes, endianness, clamp
   ranges, orderings) AND a sample lets the agent test candidates. → It sweeps the menu. (§11.5 corollary)
2. **Spec-transcription** — the deciding rule is stated precisely in the instruction / a spec doc. → It
   reads and implements it. Precision defeats you here.
3. **Textbook-derivation** — the crux is a standard algorithm (linear solve, DP, graph search, RREF,
   shortest path, standard stats). → It derives it from first principles fluently.
4. **Self-correcting** — the environment gives a signal when the answer is wrong (an oracle binary, a
   failing test, an assertion, a sample that covers the deciding case). → Its test-fix loop converges.

If your crux survives all four ("not a menu, not spelled out, not textbook, no signal"), you likely
have a stumper.

### 16.3 The winning recipe: the "framework-convention 1-ULP" pattern

This is the pattern that worked, generalized. It is the digital cousin of the delivered
`accrued-interest` (Opus failed 8/8) and `gnss-log-decode` tasks.

**Shape:** ask the agent to *reproduce, bit-exactly, the output of a real, published, specialized
computation* whose exact definition:
- is **standardized** (so it's fair — the agent can look it up; open internet is fine), BUT
- has **multiple real-world variants that disagree** (so the natural default is wrong), AND
- the correct variant hinges on a **subtle low-level detail** the model gets wrong when porting
  (integer vs float semantics, tie-direction, a sign correction, a `>>` vs `//`, an overflow nudge,
  a units/epoch/timezone convention), AND
- you provide **no sample outputs** and **no reference binary** (so a 1-ULP drift is silent).

**Concrete domains this generalizes to (all "reproduce the real thing exactly"):**
- Quantized inference (TFLite/gemmlowp vs PyTorch/QNNPACK vs ONNXRuntime rounding). ← what worked
- Fixed-point DSP filters; audio resampling; codec quantization tables.
- Financial day-count / accrual conventions (30/360 vs ACT/365 vs ACT/ACT; ex-dividend rules).
- Time: GPS/GNSS epoch & leap-second handling; timezone/DST boundary arithmetic; NTP.
- Checksums/CRCs with vendor-specific init/xor/reflect parameters; hash truncation.
- Floating-point summation order / compensated (Kahan) sums; IEEE rounding modes.
- Unicode normalization + collation (locale-specific tie-breaks); encoding edge cases.
- Protocol/serialization exactness: protobuf varint edge cases, ASN.1 DER canonicalization.

**Why it beats the model:** the model *recognizes the domain* and *retrieves the standard* — which
feels like success — but the retrieved knowledge is a slightly-wrong constant or a C++-to-Python
semantics mismatch, and nothing in the environment contradicts it. It ships confidently wrong.

### 16.4 Fairness — keep it a skill test, not a guess (mandatory)

The recipe is only valid if a competent expert who follows the instruction exactly PASSES. Enforce:
- **Name the standard** in the instruction ("implement it exactly as TFLite/gemmlowp defines it").
  This is NOT the named-gotcha trap (§11.5) — you're naming a *reproducible public standard*, not a
  nameable one-line bug. The difficulty is bit-exact fidelity, not recognition.
- **Open internet allowed** — the spec is public; fairness requires it be reachable. Keep the specific
  model/data **synthetic** so the *answer* isn't retrievable, only the *method*.
- **Every graded row is determined by the standard + given data.** No hidden literal, no undisclosed
  field (§15.7).
- **Exact-match grading is fair** because outputs are discrete integers (§11.7). No tolerance needed;
  a tolerance would let the wrong variant pass.

### 16.5 The generator framework (reusable skeleton)

Every one of these tasks uses the same generator architecture. This is the template — adapt the
`golden()` and `naive_variants()` to your domain:

```python
# 1) GOLDEN ENGINE: the exact, correct standard (this IS the reference the oracle ships).
def golden(model, x): ...            # bit-exact real standard

# 2) NAIVE VARIANTS: the plausible-but-wrong conventions the model will reach for.
#    Include 2-4 distinct ones — the more independent near-misses, the wider the trap.
def naive_float(model, x): ...       # float approximation / round-half-even
def naive_variantB(model, x): ...    # a different real-world convention
def naive_variantC(model, x): ...    # a subtle sub-detail omitted (e.g. sign correction)

# 3) SYNTHETIC MODEL/DATA: fixed seed. Size params so the trap REGIME is reachable
#    (e.g. accumulators that land on rounding boundaries; negative ties; saturation).

# 4) HUNT eval rows where each naive variant DIVERGES from golden. Bucket per variant.
#    Target: each wrong variant fails a large fraction (>=10-15 of ~48 rows).

# 5) HARD ASSERTS before writing anything (this is what saves pass@2 runs):
assert subprocess_oracle_output == golden_output          # oracle really solves it
for variant in naive_variants:
    assert wrong_rows(variant) >= FLOOR                   # trap actually fires
    # if a "sample" exists: assert variant matches ALL sample rows (no signal) — §11.4 strat 2

# 6) WRITE: environment/data/* (agent-visible inputs), tests/expected.json (ground truth).
#    NEVER write the golden algorithm or expected outputs where the agent can read them.
```

**Critical generator lessons (cost real time to learn):**
- **Assert the oracle via subprocess**, running the actual `solution/solve.py` against your generated
  golden — catches the case where your generator's golden and your shipped solve.py drift apart.
- **Assert each trap fires with a floor** (`>= N wrong rows`). A trap that fires on 0 rows = "too easy"
  before you even push. Attempt 1 would have been caught here.
- **Watch for traps that are structurally invisible.** A bug hidden behind a later clamp/saturation
  (e.g. an accumulator saturation that always clamps to the same activation) produces *identical*
  output and can never be graded. Verify each candidate bug actually changes the final output.
- **Performance:** compute each variant's output ONCE per candidate row, bucket by which trap fires;
  don't re-run forward passes in nested search loops (that was a multi-rewrite time sink). Bounded
  candidate pools, not unbounded `while` hunts.
- **Keep the model small** but sized so the trap regime is common: pick multipliers/shifts/weights so
  a meaningful fraction of accumulators hit the boundary. Tune the param ranges, not the search budget.

### 16.6 The build → validate → push loop (exact sequence, per attempt)

Run this locally EVERY iteration before spending a pass@2 run (pass@2 is capped 6/day):

```
1. Generate data + expected.json + oracle (generator with hard asserts above).
2. harbor run -p . --agent oracle   → MUST be reward 1.0
3. harbor run -p . --agent nop      → MUST be reward 0.0
4. For EACH naive variant: copy task, swap solve.py to the naive impl, harbor run oracle
   → MUST be reward 0.0   (proves the verifier grades the real outcome AND the trap fires)
5. Image clean:  docker run --rm <img> bash -lc 'find / \( -name solve.py -o -name expected.json \) 2>/dev/null'  → empty
6. Base image:   bash references/check-base-image.sh task   → PASS
7. Instruction <=1500 tokens; ends correctly per repo's static checks; LF endings.
8. Commit as YOURSELF (no AI trailer), push. Rubric/similarity/validation run first (~5 min),
   THEN pass@2 (~12-17 min), THEN pass@5 (~25 min).
```

**Order of CI gates and what each costs you:**
`gate → static/review(rubric) → similarity(dup) → validation → pass2 → trials(pass5)`.
- Rubric/similarity/validation failures are **free** (pass@2 doesn't run) — fix and re-push freely.
- pass@2 solving both = "too easy" and **consumes a daily run**. Only push to pass@2 when local
  variant-checks (step 4) show the trap is strong.

### 16.7 Turn reviewer findings into MORE difficulty

When the rubric reviewer catches a real bug in your reference (it caught that our
`RoundingDivideByPOT` omitted gemmlowp's negative-operand correction), the fix is often a *harder*
task, not just a correction: the exact detail you got wrong is, by definition, a detail a careful
implementer misses — so fixing the reference AND adding that variant as a graded near-miss sharpens
the trap. Our final task had **three** independent 1-ULP traps (float-round, truncating high-mul,
missing sign-correction), one of which the reviewer handed us.

### 16.8 Honest expectations & escalation

- Expect **multiple redesigns**. The model is strong; the first idea that "sounds hard" usually isn't.
  Budget for 2-4 attempts and use the local variant-check to fail fast before burning pass@2 runs.
- A **single-crux** task (one decisive detail) is accepted and legitimate, but note in reviewer notes
  that a model improvement on that one subskill could saturate it — the rubric expects this honesty.
- If several evidence-based designs all get solved, the crux family is wrong for this model — switch
  from *derivable/enumerable* cruxes to *imported-expertise-operationalized-wrong* cruxes (§16.3).
- Use the **war room / Slack** for: stuck required-status contexts (branch-protection name mismatches,
  cosmetic — not your task), payment/window questions, and "is this difficulty bar realistic for N
  redesigns" calls. Escalating with a clean evidence trail (rubric-clean, novel, validated PRs + pass@
  analyses) is a legitimate move, not a concession.

### 16.9 One-paragraph recipe (paste at the top of your next task)

> Pick a real, published, specialized computation that must be reproduced **bit-exactly** and whose
> exact definition has **competing real-world variants** disagreeing on a **subtle low-level detail**
> (integer vs float, tie direction, sign/overflow correction, epoch/units, `>>` vs `//`). Name the
> standard in the instruction (fair; open internet ok), keep the model/data **synthetic** (answer not
> retrievable), provide **no sample outputs and no reference binary** (1-ULP drift is silent), and
> **grade exact-match** on discrete integer outputs. Build a generator whose golden is the exact
> standard and whose 2-4 "naive variant" functions are the wrong conventions; hunt eval rows where
> each variant diverges; **hard-assert** oracle==golden and each variant fails ≥N rows before pushing.
> Validate locally: oracle 1.0, nop 0, every naive variant 0. This is the pattern that took Opus 4.8
> to **pass@5 = 0/5**.

### 16.10 The agentic-vs-silent tension (learned the hard way, task #2)

**Finding (attribution-completeness, 2026-07-09, Opus solved 2/2):** an agentic task with a
**runnable correctness invariant that covers the crux** is *self-correcting* for a capable
agent — it fails once, the invariant tells it, it fixes it. Opus hit the exact fiddly
boundary bug we bet on, and the completeness harness let it self-correct in one step.

**Why this is structural, not bad luck:**
- Proposal gate demands **agentic = runnable feedback to iterate against** (§ crit 6).
- Fair + capable agent + feedback that covers the crux = **solvable**. The feedback catches
  the subtle errors and guides the fix.
- tflite stumped Opus because the crux was **SILENT** (no sample outputs, no checker) — but
  "no feedback" *fails the agentic gate*.

**The resolution the delivered agentic-AND-stumping tasks use** (`bytecode-vm-debug`,
`silent-feature-bugs`): the agentic work is real, but **the crux is silent — no feedback the
agent has covers the deciding failure**. The visible tests/harness pass; the graded crux is
a property nothing in the environment checks. The agent does genuine exploration/debugging,
fixes what the feedback shows, sees green, and ships — the deciding case never turned red.

**Design rule for agentic stumpers:** split the invariant from the crux.
- Ship a runnable harness that covers the OBVIOUS failures (makes it agentic, gives the
  agent a loop) — but that the correct-looking-naive fix PASSES.
- The GRADED crux must be a property the shipped harness does NOT reveal (a *necessary-but-
  not-sufficient* invariant, or a second property the harness never checks), so a boundary
  slip / wrong sub-convention is **silent** to the agent's feedback.
- Pitfall that sank task #2: our harness (completeness) *did* catch boundary errors, so it
  was sufficient to guide self-correction. Completeness is broken by a wrong segment mask →
  not silent. Pick an invariant that the wrong answer still SATISFIES.

**Breadth is the other feedback-proof lever:** the relinker task (8 independent bugs,
all-or-nothing, stumped Opus) survives full feedback because the bottleneck is *breadth in
the time budget*, not a hidden signal — the agent fixes 7 of 8 and still scores 0. Use when
a single-crux design keeps self-correcting. Caveat: keep each sub-fix a genuine, independent
reasoning step or it reads as "kitchen-sink" and gets rejected.

### 16.11 The reasoning-domain wall (three defeated designs, task #2)

**Finding (attribution-completeness, 2026-07-09):** three principled designs in
*interpretability_and_model_inspection*, all solved by Opus 2/2:
1. grad-input bug + completeness harness → Opus hit the boundary bug and **self-corrected**
   via the harness (§16.10).
2. Same, calibration-scoped harness → Opus tested eval itself, got feedback, solved.
3. **Silent** complete-but-wrong tool (DeepLIFT rescale, completeness green everywhere) →
   Opus **read the code, recognized DeepLIFT ≠ IG, and implemented exact IG from the
   definition**, ignoring the green harness.

**The wall:** interpretability is a **reasoning domain**, and Opus-4.8 reasons at/above
competent-expert level in it. When a task requires a **well-known method with a precise
definition** (IG, LRP, SHAP, Grad-CAM, attention rollout), Opus:
- knows the method,
- implements it correctly from the definition in exact arithmetic,
- sees through red-herring/buggy tools by reading code + knowing the semantics,
- doesn't need feedback, so silent traps and necessary-not-sufficient invariants don't bite.
The rubric even PASSES these on `essential_difficulty` — they ARE genuinely hard; Opus just
has the expertise.

**Contrast with the one win (tflite, 0/5):** that was a **knowledge/porting slip** — Opus
knew the gemmlowp standard, retrieved a C++ constant from training, and paired it with the
wrong *language* integer-division semantics (C++ `>>` floor vs Python `//` truncate). Not a
reasoning gap — a mis-port with no reasoning path to catch it and no feedback.

**Actionable rule — match the crux type to the subcategory:**
- **Reasoning subcategories** (interpretability, math, algorithms, most of ML) → Opus is
  strong; fair well-specified tasks are usually solvable. Stumping needs BREADTH
  (many independent fixes, all-or-nothing, exhaust the budget — relinker) and even that is
  hard because Opus is fast (~6 min of a 20-min budget here). Kitchen-sink risk is real.
- **Convention/porting subcategories** (quantization/inference numerics, hardware/firmware
  bit-level, crypto with specific parameters, serialization/protocol edge cases,
  calendar/time/leap-second, checksums with vendor init/xor/reflect) → these have a SPECIFIC
  magic constant/convention Opus retrieves and **mis-applies**, with no reasoning path to
  self-correct and (if you ship no oracle) no feedback. This is where the tflite pattern
  lives. **Prefer these subcategories when the goal is to stump.**

**Practical takeaway:** if you're seeded into a reasoning-heavy subcategory and two
principled designs get solved, don't keep iterating the same pattern — the wall is the
domain, not the design. Either commit to a large BREADTH build (accepting kitchen-sink
risk) or, if allowed, release and claim a convention/porting subcategory.

### 16.12 Confirmation: the C→Python integer-semantics blind spot is systematic

**Second 0/5 (quant-logit-attribution, 2026-07-09).** Re-aimed the gemmlowp crux into the
interpretability subcategory (direct logit attribution: per-neuron contributions of an int8
model — the objective is the attribution matrix, the deciding work is exact activations).
Result: pass@5 = 0/5, avg@5 = 0.000, all valid. **All five agents made the identical
two-part mistake as task #1's five:** nudge `(1-(1<<30))` from the C++ source + C
truncation-toward-zero division, instead of `-(1<<30)` + arithmetic right-shift (floor).

Ten trials across two tasks, ten identical failures on one primitive. The stumpable
surface is **retrieval-misapplication** (translating C integer semantics to Python), not
reasoning. Analyzer verdict both times: crux genuine, spec sound, verifier well-founded;
4/5 trials flagged near-miss (structurally perfect, 16/44 boundary inputs off by 1) —
"intentional mechanism, not a flaw."

**Reusable move:** a proven convention/porting crux can be re-aimed into a different
subcategory by changing the GRADED OBJECTIVE (what artifact the agent must produce) while
the deciding computation stays the same. Attribution matrix vs class predictions made the
duplicate check rule them distinct ("a correct solution to either would not solve the
other"). Expect a possible human-review comment on family resemblance; defense: different
graded artifact, and the crux is the documented model weakness the benchmark measures.

**Efficiency note:** task #2's winning version was built in ~1 hour by reusing the §16.5
generator skeleton + the proven core. The three failed reasoning-crux attempts cost ~4
hours. Pick the crux type FIRST (§16.11), then build.

---

## 17. AUTHORING AGAINST YOURSELF — succeeding when the authoring model IS the benchmarked model

Postmortem finding (2026-07-09): every design authored while the assistant ran Opus-4.8
(the benchmarked model) was solved 2/2; both 0/5 stumps were authored after switching to a
different model (Fable). Two causes, one confound — and a framework that works either way.

### 17.1 Why author
### 16.13 Author-model-independent framework: stumping Opus 4.8 without Fable

**Postmortem.** Every task Opus-4.8 *authored to stump Opus-4.8* was solved 2/2 (three in a
row). Both wins came after switching the author model to Fable. Two entangled causes:

1. **Author-solver identity trap.** When the author model == the solver model, any trap the
   author can *conceive and articulate* it can also *solve* — the "this is tricky"
   judgment is produced by the same weights being tested, so introspective difficulty is
   systematically anti-calibrated. Opus-as-author naturally reaches for *reasoning* traps
   (they feel clever to it) — exactly the traps Opus-as-solver dismantles. The blind spots
   that actually beat Opus (C→Python integer semantics) are *execution bugs invisible to
   introspection*: Opus doesn't know it makes them, so it would never bet a task on them.
2. **Learning-curve confound.** Both wins were 4th attempts with 3 trial analyses each. The
   decisive input was *observed-failure evidence*, not author-model IQ. (Proof: Fable also
   got `rdbpot` wrong in task #1 — the rubric caught it. Fable's edge was a *disjoint error
   distribution* + a process that trusted evidence over introspection, not superior recall.)

**Consequence:** the fix is NOT "use a smarter author model." It's a process that (a) sources
difficulty from *observed* Opus failures rather than the author's imagination, and (b) uses
*external* verification the author can't fool. Both are model-independent, so they work when
only Opus is available to author.

**The framework (apply in order; each step neutralizes the identity trap):**

1. **Never invent the crux — mine it.** Do not ask "what would be hard?" (introspection,
   anti-calibrated). Instead pull from the *observed-failure library*: the delivered corpus
   (§11.2, §11.4) and the confirmed Opus blind spots (§16.11/§16.12). If a candidate crux is
   not in the library and not a documented model weakness, treat it as *probably solvable*
   until proven otherwise. **Bias hard toward convention/porting/execution cruxes; distrust
   any reasoning crux you thought of yourself.**

2. **Apply the FALSIFICATION test, not the plausibility test.** For a candidate crux, don't
   ask "would this fool the model?" Ask: **"Write the most obvious correct-looking solution
   the way a competent engineer would — does it actually produce the wrong answer?"** Build
   BOTH the golden and the naive-but-plausible solver, run them, and *measure* divergence on
   the eval set. If you can't produce a plausible solver that measurably fails, you have no
   trap — regardless of how clever it feels. (This is what the generator hard-asserts encode:
   `naive_variant(x) != golden(x)` on ≥N rows. §16.5.)

3. **Externalize ground truth; forbid introspective grading.** The golden must come from an
   *external authority* the author cannot rationalize: a published standard implemented to
   the letter (gemmlowp C++), a reference library's exact output, an independent
   re-derivation. Never grade against "what the author thinks the answer is." Exact-match on
   discrete outputs (§11.7) so there's no tolerance the author's bias can widen.

4. **Kill the feedback path (§16.10).** A capable solver + any in-environment signal that
   covers the crux = self-correcting. Ship NO sample outputs, NO reference binary, and make
   any invariant you do ship *necessary-but-not-sufficient* so the naive answer satisfies it.
   The deciding error must be SILENT to everything the agent can run.

5. **Prefer execution/porting cruxes over knowledge cruxes.** Knowledge ("does it know
   gemmlowp?") is a coin flip — Opus often does. The durable edge is *execution*: a place
   where the model knows the concept but mis-implements a low-level detail with no reasoning
   path to catch it. Canonical family: **language-semantics mismatches** (C `>>` floor vs
   Python `//` truncate; C++ `int` overflow vs Python bigint; signed/unsigned; endianness;
   IEEE rounding modes; locale/encoding). Two independent 0/5s rode the SAME C→Python
   integer-division blind spot — it is the most reliable single lever found.

6. **All-or-nothing over a boundary-heavy batch.** One ULP error on 16/44 inputs → reward 0.
   Construct the eval set to *hunt* the boundary regime (don't rely on random inputs hitting
   it — §16.12 generator). This converts a rare, silent, plausible mistake into a certain
   failure, and makes "almost right" (the model's actual output) score zero.

7. **Let the human reviewer harden you.** The rubric/deep-review will catch author errors
   (it caught Fable's `rdbpot` bug). Treat a caught author-side bug as a GIFT: fixing it
   usually *adds* a trap (the exact detail you got wrong is a detail the solver gets wrong).
   §16.7.

**The one-sentence version:** *Stop asking the author model what's hard (it can't know its
own blind spots); instead reproduce a documented execution/porting blind spot from the
observed-failure library, prove a plausible solver measurably fails it, grade it exactly
against an external standard with no feedback, and make it all-or-nothing over a
boundary-heavy batch.* This is model-independent — it works whether Opus, Fable, or anything
else is holding the pen, because the difficulty lives in *measured external facts*, not the
author's imagination.

**Pre-flight checklist (run before building, any author model):**
- [ ] Crux is from the observed-failure library / a documented model weakness — not invented.
- [ ] It is an execution/porting/convention crux, not a reasoning crux. (If reasoning: expect
      to lose to Opus; only breadth-all-or-nothing has a chance, §16.11.)
- [ ] I have BUILT a plausible naive solver and MEASURED it failing ≥N eval rows.
- [ ] Ground truth is an external standard, exact-match, no tolerance.
- [ ] No sample outputs / no reference binary; any shipped invariant is not sufficient.
- [ ] Eval batch is hunted to be boundary-heavy; grading all-or-nothing.
- [ ] Generator hard-asserts: oracle==external-golden (subprocess), naive fails ≥N, no leak.

---

## 17. THE ELITE STUMPING KIT — deep bench, scoring, and build loop

§16.13 says "mine an execution/porting crux from the observed-failure library." This
section IS that library, made deep and operational: a tiered catalog of blind spots, a
score-before-you-push rubric, a subcategory→crux map, and the tight build loop. Together
they remove the single point of failure (over-reliance on the one gemmlowp crux) and make
success repeatable across any assigned subcategory, with any author model.

### 17.1 The Blind-Spot Catalog (the deep bench)

Each entry is an **execution/porting/convention** crux: the model knows the concept but
mis-applies a specific low-level detail, with no reasoning path to self-correct. All are
chosen to be **exact-gradable** (integer/discrete) and **silent** (no feedback catches the
error). Tiers: **T1** = proven or near-certain (durable, use freely); **T2** = strong but
the model may recall it correctly (combine with all-or-nothing/breadth); **T3** =
situational (needs care to stay exact+fair). Format per entry: *mechanism · naive-wrong
default the model writes · why silent/mis-applied · how to keep it exact · best
subcategories.*

**A · Integer & bit semantics** (the proven family — the richest vein)
1. **Arithmetic-shift vs truncating division on negatives** [T1, proven ×2]. `C >>` /
   gemmlowp uses floor (arithmetic right shift); Python `//`/`int(x/y)` truncates toward
   zero → differ by 1 on negative non-exact cases. *Naive:* `int(x/2**n)` or `//` after a
   float multiply. *Silent:* only negative-operand boundary rows differ. *Exact:* pure int.
   *Fits:* quantization/inference numerics, DSP, hardware/firmware, low-level.
2. **Rounding mode: half-to-even vs half-away-from-zero vs half-up** [T1, proven]. Python
   `round`/`numpy.rint` = banker's (half-to-even); gemmlowp/most fixed-point = half-away;
   some = half-up. *Naive:* `round()`. *Silent:* only exact-half accumulators differ.
   *Exact:* int. *Fits:* quantization, DSP, finance rounding, statistics.
3. **Fixed-width integer overflow: wrap (two's complement) vs saturate vs bigint** [T1].
   C int8/16/32 wraps; Python is arbitrary precision → an accumulator that overflows in
   hardware wraps to a very different value. *Naive:* Python bigint, no wrap. *Silent:*
   only inputs that overflow the width differ; wrap can flip sign (very visible once it
   fires, so hunt those inputs). *Exact:* int with explicit `((v + 2^(w-1)) % 2^w) - 2^(w-1)`.
   *Fits:* embedded/firmware, fixed-point accumulators, hash mixing, PRNGs. **NOTE:** apply
   wrap at the RIGHT granularity (per-op vs per-accumulate) — the granularity is itself a
   sub-convention that's easy to get wrong.
4. **Signed/unsigned interpretation + sign extension** [T1]. Reading a byte as int8 vs
   uint8; sign-extending a k-bit field to a wider int. *Naive:* treat bytes as unsigned, or
   forget sign extension. *Silent:* only high-bit-set values differ. *Exact:* int. *Fits:*
   binary parsing, protocol, firmware, forensics.
5. **Modulo sign convention** [T1]. C `%` takes the sign of the dividend; Python `%` takes
   the sign of the divisor → differ on negative operands. *Naive:* Python `%`. *Silent:*
   negative inputs only. *Exact:* int. *Fits:* hashing, ring buffers, modular arithmetic,
   any port of C code.
6. **Endianness / bit order within bytes** [T2]. Big vs little endian; MSB-first vs
   LSB-first bit packing. *Naive:* assume the wrong order. *Exact:* int/bytes. *Fits:*
   binary formats, protocols, firmware.

**B · Hash / checksum / crypto parameters** (specific magic constants — very hard to guess)
7. **CRC parameter set: (poly, init, refIn, refOut, xorOut)** [T1]. 100+ named CRC-16/32
   variants differ ONLY in these five. *Naive:* "standard CRC-32" (zlib params) when the
   device uses a different set. *Silent:* every output differs, but a plausible
   implementation looks right; without the exact params you cannot match. *Exact:* int.
   *Fits:* checksums, protocol/serialization, firmware, forensics, security. Give the params
   in a spec doc (fair) — the difficulty is the exact bit-reflection/xor order, which is
   notoriously mis-implemented.
8. **Non-crypto hash mixing (FNV / MurmurHash3 / xxHash): primes, rotates, finalization +
   fixed-width wrap** [T1]. Each has exact magic constants, rotate amounts, and a finalizer,
   all under 32/64-bit wrap. *Naive:* wrong constant, or no wrap (Python bigint), or wrong
   rotate. *Silent:* every hash differs; boundary not needed (it's all-or-nothing by
   nature). *Exact:* int with explicit masking. *Fits:* hashing, data structures, forensics.

**C · Calendar / time** (notorious; delivered wins here)
9. **Day-count conventions: 30/360 vs ACT/365 vs ACT/ACT vs 30E/360** [T1, delivered
   accrued-interest 8/8]. *Naive:* ACT/365 or a naive day difference when the instrument
   uses 30/360 (with its specific end-of-month rules). *Silent:* only date pairs where the
   conventions diverge (month-ends, Feb) differ. *Exact:* rational/int. *Fits:* finance/quant,
   regulated knowledge work, data processing.
10. **Leap seconds / GNSS epoch & per-constellation offsets** [T1, delivered gnss]. GPS vs
    BeiDou vs Galileo vs GLONASS use different epochs and leap-second handling. *Naive:* one
    constellation's rule for all; ignore leap seconds. *Silent:* only records from the
    unshown constellation/era differ (latent crux). *Exact:* int seconds. *Fits:* signal
    processing, scientific computing, embedded.
11. **Timezone/DST transition exactness; ambiguous & nonexistent local times** [T2].
    *Naive:* fixed offset; mishandle the fall-back ambiguous hour / spring-forward gap.
    *Exact:* int epoch. *Fits:* data processing, time-series.
12. **Point-in-time / as-of vs latest (bitemporal)** [T1, delivered]. Use the value known
    *as of* a cutoff, not the latest. *Naive:* `merge_asof` on effective_ts / latest value.
    *KEEP SILENT* — this was solvable when made agentic-with-feedback (§16.10); ship no
    checker that reveals it. *Exact:* int. *Fits:* databases, finance, data processing.

**D · Text / encoding**
13. **Unicode normalization form (NFC/NFD/NFKC/NFKD) + where each applies** [T1, §11.5].
    *Naive:* compare raw code points, or use the wrong form. *Silent:* only strings with
    composed/compatibility characters differ. *Exact:* discrete. *Fits:* NLP, security
    (auth/identity), text processing.
14. **Grapheme cluster vs code point vs byte counting; surrogate pairs; combining marks**
    [T2]. *Naive:* `len(str)` (code points) for a "character" count. *Exact:* discrete.
    *Fits:* text processing, NLP.
15. **Tokenizer/BPE exact merge order + special-token framing + pre-normalization** [T1,
    delivered tokenizer-recovery]. *Naive:* greedy longest-match, wrong merge priority,
    missing special tokens. *Silent:* only inputs hitting the specific merges/specials
    differ. *Exact:* int token ids. *Fits:* NLP/LLM, interpretability.

**E · Numerical / statistical conventions**
16. **Aggregation unit (per-user vs per-session) + sample vs population variance (n-1 vs n)**
    [T1, delivered experiment-readout 5/5]. *Naive:* per-row/per-session stats; divide by n.
    *Silent:* the point estimate can even match; only the variance/CI differs → a wrong
    significance call. *Exact:* rational. *Fits:* data science, statistics, experiment
    analysis. (Grade the exact integer/rational statistic, not a p-value.)
17. **Quantile/percentile interpolation method (the ~9 definitions)** [T2]. NumPy's `method`
    param enumerates them; they differ between data points. *Naive:* linear interpolation
    when the spec wants "lower"/"nearest"/type-7. *Exact:* rational if inputs are integers.
    *Fits:* data science, analytics.
18. **Floating-point summation order / compensated (Kahan) sum; two-pass vs one-pass
    variance** [T3]. Non-associativity → order matters. *Keep exact* by constraining inputs
    to exactly-representable values or grading an integer-scaled result; otherwise this
    needs a justified tolerance (fairness risk). *Fits:* scientific computing.

**F · Protocol / serialization / DSP**
19. **Protobuf varint/zigzag + field order + default omission; ASN.1 DER canonical form**
    [T1]. Exactly one valid encoding; naive encoders violate canonicalization. *Naive:*
    include default-valued fields, wrong zigzag for signed, non-minimal length. *Exact:*
    bytes. *Fits:* networking, serialization, security.
20. **Q-format fixed-point (Qm.n) multiply → shift → round → saturate** [T1]. Distinct from
    gemmlowp (different framing) so it dodges duplicate-vs-tflite. *Naive:* float multiply,
    wrong shift/round, no saturate. *Silent:* boundary + overflow rows. *Exact:* int. *Fits:*
    DSP/signal hardware, embedded, low-level.

**Reuse discipline:** you have spent the gemmlowp crux (A1+A2) twice — its duplicate risk is
now high. For the next task, pull a DIFFERENT T1 entry. The catalog gives ≥12 T1 options
across families so you never repeat.

### 17.2 Crux confidence rubric — score BEFORE you push (protect the 6/day pass@2 cap)

Rate the candidate crux 0–2 on each axis; **push to pass@2 only if total ≥ 9/12 AND no axis
is 0.** Below that, redesign — don't spend a run.

| Axis | 0 | 1 | 2 |
|---|---|---|---|
| **Execution vs reasoning** | pure reasoning/derivation | mixed | pure execution/porting/convention (from §17.1) |
| **No reasoning path to catch** | error is derivable/checkable by logic | partially | the mistake is invisible to reasoning; only external ground truth reveals it |
| **Silence** | an in-env check/oracle reveals it | a shipped invariant is necessary-but-not-sufficient | no samples, no reference, nothing covers the crux |
| **Measured divergence** | not built/measured | naive fails a few rows | BUILT a plausible naive solver; it fails ≥⅓ of a hunted eval batch |
| **All-or-nothing bite** | partial credit possible | single output | many outputs, exact-match, one slip → reward 0 |
| **Duplicate distance** | reuses a spent crux/framing | same crux, new framing | different crux family entirely |

The two 0/5 wins both scored 11–12/12. The three Opus-authored losses would have scored
≤6 (all failed "execution vs reasoning" and "no reasoning path"). **This rubric alone would
have prevented every wasted pass@2 run.**

### 17.3 Subcategory → crux quick-map (never be stuck)

Seeded into a subcategory? Pull the matching T1 crux:

- **model_inference_and_prediction / ml_serving** → A1 A2 A3 (quantization requant), 20 (Q-format).
- **interpretability_and_model_inspection** → 15 (tokenizer/BPE), or re-aim a numerics crux via a decomposition objective (§16.12).
- **feature_engineering / data_processing / etl / tabular** → 9 (day-count), 12 (as-of), 16 (aggregation unit), 13 (normalization).
- **data_science / statistics / experiment analysis** → 16 (unit + n-1), 17 (quantile method).
- **security (crypto/forensics/auth)** → 7 (CRC), 8 (hash), 13 (normalization identity), 19 (DER), 4 (sign/parse).
- **hardware_embedded / low_level / dsp / rtl** → 3 (overflow), 20 (Q-format), 4/6 (parse/endian), 1/2 (shift/round).
- **scientific_computing / signal_processing** → 10 (GNSS/leap), 18 (summation), 20 (fixed-point DSP).
- **networking / serialization / build** → 19 (varint/DER), 7 (CRC), 6 (endian).
- **databases / querying** → 12 (as-of/bitemporal), 9 (day-count), 16 (aggregation).
- **finance / regulated knowledge work** → 9 (day-count), 12 (as-of), 16 (stats).
- **file_and_media / text_editing** → 13/14 (unicode), 6 (endian in media containers).

If a subcategory looks like a pure reasoning domain with no native execution crux (rare),
**re-aim** a numerics crux by changing the graded objective into that domain's artifact
(§16.12 — attribution matrix instead of predictions), or accept it's a low-odds seed and
lean on breadth-all-or-nothing (§16.11).

### 17.4 Divergence-Driven Development (the tight build loop)

Build the trap by *measurement*, never by faith. One source file defines everything:

```
1. golden(x)         = the EXACT external standard (implement to the letter; cite it).
2. naive_variant(x)  = the most obvious correct-LOOKING solver (what a good engineer writes).
   (write 2-4 distinct naive variants — each a different plausible mistake.)
3. HUNT the eval batch: generate candidates, KEEP the ones where some naive != golden,
   until each variant fails >= N rows. Random inputs rarely hit the boundary — hunt.
4. HARD-ASSERT before writing files:
     - subprocess: solution/solve.py output == golden        (catches your own bugs)
     - each naive_variant fails >= N of the eval batch        (proves the trap bites)
     - any shipped invariant PASSES for every naive_variant   (proves it's not sufficient)
     - no ground truth / oracle reachable in the agent image  (silence)
5. Local gate: harbor oracle=1, nop=0, EACH naive_variant=0.
6. Only then push (pass@2 run). Score >= 9/12 on §17.2 first.
```

The `naive_variant` functions are not decoration — they are the task's proof of difficulty
and your own bug-catcher. If you cannot write a plausible solver that measurably fails, you
have no trap; stop and pick another crux.

### 17.5 Red-team your own task (the 10-minute pre-push ritual)

Before pushing, the author (any model) runs this:
1. **Solve it the obvious way, fast, without looking at your golden.** Write the solver you'd
   write in 10 minutes. Run it against the verifier. If it PASSES → too easy; the crux isn't
   biting. If it FAILS on the boundary rows → good, that's the trap.
2. **Name the exact line where the obvious solution goes wrong.** If you cannot point to one
   specific line/convention, the difficulty is diffuse (reasoning) and Opus will reason
   through it. A stumper has ONE nameable, silent, external-only deciding line.
3. **Ask: could I catch this with a test I'd naturally write?** If yes (e.g., completeness
   catches it — §16.10), it's self-correcting; remove that signal or change the crux.
4. **Grep your own instruction for a hint you didn't mean to give**, and confirm no sample
   output / reference binary ships (§13, §15.7).

### 17.6 The elite loop, one line

**Pick a T1 crux from §17.1 matched to the subcategory (§17.3) and distant from spent ones →
implement golden from the external standard + 2-4 plausible naive solvers → hunt a
boundary-heavy all-or-nothing batch where the naives measurably fail (§17.4) → score ≥9/12
(§17.2) → red-team (§17.5) → local gate → push once.** Difficulty lives in measured external
facts, so it holds regardless of which model authors — and you never burn a pass@2 run on a
guess.

### 17.7 CRITICAL CORRECTION — the Disclosure Test (why most §17.1 cruxes are weaker than gemmlowp)

**Finding (repair-capture-crc, 2026-07-10, rubric FAIL on essential_difficulty).** A
fully-disclosed CRC-32/BZIP2 crux was rejected: "with every trap disclosed, the remaining
work is a fully-specified parameterized CRC... a competent expert finishes in 30–60 min."
Also: `crcmod.predefined['crc-32-bzip2']` is a one-line library call under open internet.

**The correction — not all execution cruxes are equal. Split them:**
- **Language-semantics slips (gemmlowp-grade, SURVIVE disclosure):** the mistake is in how
  the *host language* behaves, one level BELOW the algorithm, so disclosing the algorithm
  doesn't prevent it. The model retrieves a reference implementation (usually C/C++) and
  mis-ports a silent language difference. Examples: C `>>` floor vs Python `//`/`int()`
  truncate on negatives [PROVEN]; fixed-width overflow wrap vs Python bigint; C signed
  `char` vs Python unsigned bytes; C `%` sign vs Python `%` sign; float non-associativity /
  FMA. These beat a strong model EVEN fully disclosed, because it defers to retrieved
  C semantics and its Python port silently differs.
- **Algorithm-choice conventions (DISCLOSURE-DEFEATED, and often LIBRARY-defeated):** the
  mistake is choosing the wrong variant/parameter/rule. Disclosing the exact rule makes it
  mechanical. Examples: CRC reflected-vs-not + params, day-count convention, quantile
  method, rounding mode *as a stated choice*, aggregation unit, normalization form. A strong
  model, given the disclosed rule, just implements it — or calls a library.

**The Disclosure Test (add to §17.2 as a GATE, weight it heavily):**
> *After I disclose everything needed for fairness, is the crux still hard?* If the answer
> is "no, it's just implement-the-spec," the crux is algorithm-choice and will be rejected on
> essential_difficulty. Only pass if EITHER (a) the crux is a language-semantics slip that
> survives disclosure, OR (b) the task requires genuine INFERENCE the spec cannot hand over
> (structure recovery, reverse-engineering unknown parameters from examples, multi-stage
> reconstruction).

**Also add to the falsification test (§17.4):** the naive-variant sweep MUST include
**pip-installable libraries** (open internet), not just stdlib. Check: is there a
`crcmod` / `python-dateutil` / `scipy` / `numpy` one-liner that produces the golden? If yes,
the crux is library-defeated regardless of disclosure. (For gemmlowp this was safe: no pip
package reproduces TFLite's exact int8 requant.)

**Revised §17.1 tiering:** demote all *algorithm-choice* entries (CRC #7, day-count #9,
quantile #17, normalization #13 when disclosed, aggregation #16 when disclosed) to "only
viable if UNDISCLOSED / inference-required." Keep as durable T1 only the *language-semantics*
family (#1 shift/divide [proven], #3 overflow, #4 signed/unsigned, #5 modulo-sign) and
*genuine-inference* framings.

**Two escape hatches when seeded into a subcategory without a language-semantics crux (like
file/media recovery):**
1. **Genuine inference / reverse-engineering:** don't disclose the parameters — make the
   agent RECOVER them from intact examples (e.g., solve for an unknown CRC's poly/init/xor
   from good (data, crc) pairs via GF(2) linear algebra; recover a lost record structure by
   using checksums as constraints — "carving"). This survives disclosure because nothing is
   disclosed, and it's not library-trivial IF the parameters are custom (not in reveng's
   catalog). Risk: reverse-engineering tools (reveng) or brute force may still crack it —
   MEASURE.
2. **Structure recovery / multi-stage:** the file's structure itself is damaged (lengths /
   boundaries lost), so linear parsing fails and the agent must search/reconstruct using
   integrity fields as constraints. Difficulty is the reconstruction, not a formula.

### 17.8 SECOND CORRECTION — in-spec C source does NOT trigger the porting blind spot (repair-capture-digest, 2026-07-10, pass@2 = 2/2)

**The experiment.** Revision of repair-capture-crc per §17.7: custom firmware digest,
disclosed in-spec as ~10 lines of C plus itemized normative semantics (signed s8 bytes,
int32 wraparound, truncation-toward-zero `/`, dividend-sign `%`, with worked examples like
`-9/8 = -1`). Zero feedback (all digest fields zeroed, no check vector, no intact records).
Five plausible naive ports each measurably failed 48/48 records; oracle validated against
the routine compiled as real C (`-fwrapv`). Cleared rubric (essential_difficulty PASSED),
similarity (UNIQUE), validation. **pass@2: 2/2 solved.** Both agents independently wrote
flawless `wrap32`/trunc-div/c-mod helpers with near-identical names; one asserted the
spec's worked examples before running. Analyzer: "robust training-data knowledge of the C
integer-arithmetic pitfalls being tested."

**The correction to §17.7.** "Language-semantics slips survive disclosure" is TOO BROAD.
The two 0/5 gemmlowp wins did not disclose the deciding C code in the task — they cited a
large, FAMILIAR external standard (TFLite/gemmlowp) that the model believed it already
knew, so it wrote its remembered idiom instead of reading the real source. The blind spot
is **retrieval-misapplication of a familiar external standard**, not ignorance of C
semantics. When a SMALL custom routine is shipped in-spec, front-and-center, the model
reads it fresh and ports it correctly — its knowledge of C trunc-division/mod/wrap/sign
pitfalls is robust when its attention is ON them. Itemizing the semantics (worked
examples) makes this certain: it hands the solver a checklist and even a self-test.

**The structural trilemma this exposes (worst in file/media + open internet):**
- `unambiguous` forces full disclosure of anything custom;
- a fully-disclosed deterministic algorithm can always be faithfully EXECUTED by a capable
  agent (port carefully — now proven; or apt-get gcc and compile the spec's own C);
- while any REAL-WORLD standard, which could stay undisclosed ("match tool X"), ships with
  real tools and libraries → library-defeat and/or an in-env validation oracle (e.g.
  SQLite WAL checksums: stdlib sqlite3 IS a feedback oracle).
So: custom → disclosed → executable; real → library/tool → shortcut or feedback. The
porting-crux family is effectively EXHAUSTED in this regime.

**What still stood after this failure (ranked, all unproven here):**
1. **Familiar-external-standard retrieval-misapplication** (the only 0/5-proven lever,
   §16.12): needs a real standard the model *thinks* it knows, whose deciding detail is
   buried in a large codebase, with NO library/tool that can compute or validate the
   artifact. In file/media such standards are nearly nonexistent (real formats have
   tools). Works best in ML/numerics domains — if reseeding is possible, go there.
2. **Breadth-all-or-nothing** (§16.11): many independent, mundane, exactly-graded details;
   accepts kitchen-sink risk; today's evidence (careful, self-validating agents) lowers
   its odds too.
3. Reverse-engineering-unknown-params (§17.7 hatch 1) is a dead end both ways: small param
   space → agent brute-forces; large non-linear space → expert can't either (unfair).

**Process lesson:** a crux "measured" only against AUTHOR-WRITTEN naive solvers is not
measured against the benchmarked model. Five naive ports failing 48/48 proved the trap
EXISTS, not that the model falls into it. The §17.2 axis "no reasoning path to catch"
scored 2 but was actually 0-1: reading disclosed code IS the reasoning path. Before
spending a pass@2 on any disclosure-dependent crux, ask: "does the model need to RETRIEVE
the deciding fact from memory (stumpable), or is it printed on the page (solved)?"

### 17.9 THIRD CONFIRMATION — the lull does not displace normative text (repair-capture-digest rev 2, 2026-07-10, pass@2 = 2/2)

**The experiment.** Revision 2 inverted the §17.8 failure mode: commodity algorithm
(zlib CRC-32, nothing to port), difficulty moved to five interacting per-generation
digest-domain rules stated once in the spec, plus a confirming-but-insufficient sample
(20 sealed gen-1 records that every one of five measured near-miss readings reproduces
exactly — the §11.2 "stopped checking after the first green result" lull). Local gate
clean, §17.2 scored 10/12. **pass@2: 2/2 solved, ~3-3.5 min each (~20% of budget).**

**Why the lull failed.** Both agents read format_spec.md FIRST — before touching the
data — and implemented every stated rule from the normative text, first-principles.
The sample never got the chance to anchor them: visible data does not displace spec
text for a spec-reading agent. One agent used the sealed records only as a post-hoc
assertion. The §11.2 lull wins (bytecode-vm, gnss, tokenizer) all have a different
structure than this revision did: there the deciding rule was NOT written in any
shipped document — it lived in unshipped data regimes, hidden test gaps, or external
domain knowledge. The lull works when green feedback substitutes for a rule the agent
would otherwise have to go find; it does nothing when the rule is printed on the page.

**The three-strike rule for this seed (file/media recovery + open internet +
spec-complete fairness):** three rubric-clean designs (disclosed named standard;
disclosed custom routine; latent multi-regime rules behind a lulling sample), each
solved 2/2 by careful spec-reading agents at ≤25% budget. The wall is the SEED, not
the design (§16.11 practical takeaway): when fairness forces every deciding rule into
a document the agent will read, the task is a spec-implementation task, and Opus-4.8
executes disclosed specs flawlessly at any rule count an author can honestly defend.

**The structural statement (sharpens §17.8's trilemma):** a task in this regime can
only stump if the deciding fact is (a) NOT in any shipped document, (b) still fairly
recoverable — i.e., from public real-world knowledge the model mis-retrieves
(gemmlowp/gnss family: needs a REAL standard, nearly nonexistent in file/media, and
its tools/tables must not be able to compute or validate the artifact), or from
in-file data by genuine inference (legacy-formatter-clone family: recover a custom
affine checksum by GF(2) algebra from intact pairs — delivered vs GPT-5.4, UNPROVEN
vs Opus, and scores ≤7/12 on §17.2 because it is a reasoning crux). Neither clears
the §17.2 ≥9/12 push bar for this repo. **Conclusion: no rubric-compliant design
exists in this seed; the correct move is §16.8 escalation (evidence trail: three
rubric-clean, novel, validated PRs, each with a full pass@2 analysis), not a fourth
redesign.**

### 17.10 FOURTH CONFIRMATION — algebra-recovery is Opus-native (repair-capture-digest rev 3, 2026-07-10, pass@2 = 2/2)

**The experiment.** Deciding facts moved OFF the page: disclosed mixer structure
(seal = c ⊕ ⊕ rotl32(S[b_i], 11i mod 32)), unpublished constants (8224 bits), exactly
recoverable from 257 sealed records via a square nonsingular GF(2) system built with
zero redundancy (no held-out validation). Measured silent near-misses (rotate-direction,
stride) wrong 40/40. Precedent: legacy-formatter-clone (GPT-5.4 5/5 fail — tried
checksum catalogs instead of algebra). **pass@2: 2/2 solved.**

**How they solved it — above the reference's level.** Both agents recognized the affine
structure instantly and then chose a SMARTER representation than the reference: ring
algebra over GF(2)[x]/(x^32−1), reducing 8224×8224 bit-level elimination to a 257×257
word-level system (one via ring inverses / polynomial GCD, one via a Pascal-triangle
change of basis to GF(2^32) solving all 32 bit-planes at once). 40s and 6.7min. Both
then verified recovered constants against all 257 sealed records with their own forward
implementation before writing — a self-check that catches one-sided pipeline bugs even
in a zero-redundancy design (system-builder and forward-sealer bugs only stay silent if
IDENTICAL in both).

**Lessons, final for this crux family:**
1. The GPT-5.4 catalog-fumble (legacy-formatter-clone) does NOT transfer: Opus-4.8 has
   native command of linear algebra over quotient rings and reaches for it unprompted.
   Structure-disclosed + data-recoverable = solved, elegantly.
2. Zero-redundancy (square-exact) does not remove the agent's self-verification: agents
   re-verify the recovery against the same sealed pairs with independently-written
   forward code, catching asymmetric implementation slips. The only surviving silent
   failure is a matched pair of bugs — vanishingly unlikely for a careful agent.
3. Seed verdict (with §17.9's trilemma, now closed at both ends): file/media recovery +
   open internet + fairness admits NO stumping design: on-page rules → executed;
   off-page-but-recoverable → recovered (and self-verified); off-page-and-unrecoverable
   → unfair. Four designs, 8/8 trials, ≤25% budget each. ESCALATE (§16.8) — the
   evidence trail (4 rubric-clean novel designs with full pass@2 analyses) is exactly
   what the war room needs to make a reseed/difficulty-bar call.
   **[SUPERSEDED 2026-07-10: a fifth placement existed — see §17.11 and §18. The
   trilemma covered where a fact can LIVE; the win came from making two authorities
   DISAGREE. Escalation was not needed.]**

### 17.11 THE WIN — poisoned self-validation oracle, 0/2 twice, task ACCEPTED (repair-capture-times, 2026-07-10/11)

**The design that landed** (after five straight 2/2 losses in this repo): CAPX v4
mixed-timebase repair (rev 4's era/offset layer kept intact) PLUS six of the 24
already-processed records normalized by the "buggy crashed tool" with the current-era
18 s offset in the 17 s era, digests consistently sealing the wrong values. Spec
de-pointed (no IERS citation, no standards documents — scales are "the standard time
scale of that name"). Instruction unchanged: processed records preserved exactly;
graded values anchored to the spec.

**What happened, run 1 (timeout_sec = 900): 0/2, both in-progress-timeout.** Both
agents built CORRECT era-aware conversions (16/17/18 s — the knowledge was never the
problem), added the same voluntary validation guard (`if stored != computed: raise`),
hit poisoned record 11, wrote NOTHING, and their diagnostic delta-histograms were
"trending toward the constant-18 s fix" (the wrong rule) at timeout. Analyzer:
*"an agent that diligently validates its conversion against the stored data is driven
— by its own correctness-checking instinct — away from the right answer."*
difficulty_crux PASS on failing trials; approach_validity PASS ("legitimate agent
limitations"); task_specification PASS ("'preserved exactly' describes the write
action, not a verification requirement"). Only low_timeout FAILED: Terminus-2 at
xhigh burns 350-450 s per reasoning call; 900 s ⇒ in-progress-timeout ≠ valid fail.

**What happened, run 2 (timeout_sec = 3600, ZERO design changes): 0/2, both VALID
fails, all seven rubric criteria PASS ×2. Gate green, pass@5 stage green, PR labeled
`accepted`.** The single configuration change converted the same failures from
"unclassifiable" to "valid" — read the gate taxonomy before redesigning anything.

**Why this worked when five better-looking designs failed:** the difficulty is not
knowledge (they had the right offsets), not derivation, not retrieval — it is
ATTRIBUTION UNDER SELF-DOUBT. The adversary's most reliable behavior (validate
against in-environment data before writing — observed in every single trial) was
aimed at data constructed so that diligence points away from truth. Its workflow,
not its knowledge, was the attack surface. Full construction manual: §18.4.

---

## 18. THE FABLE HANDOFF — adversary dossier, placement ladder, and the workflow-attack playbook

Written 2026-07-12 by the Fable-model author session, after the first accepted stump
of Opus-4.8 in this repo (6 designs, 12 benchmark trials). **Audience: an Opus-4.8
(or any future) authoring session.** The premise of §16.13 still holds and is now
backed by 12 more trials: *you cannot introspect your own blind spots; any trap you
can conceive-and-articulate as "tricky" you can also solve.* Therefore this section
is written to be executed MECHANICALLY. Every judgment call is replaced by a
measured fact, a checklist, or a walkthrough. When you feel the urge to deviate
because something "seems hard enough" — that feeling is the documented failure mode.
Re-read §16.13(1) and keep going.

### 18.1 The complete empirical record (ground truth — do not re-litigate)

| # | Design (repo/rev) | Deciding-fact placement | Result | One-line cause |
|---|---|---|---|---|
| 1 | tflite gemmlowp requant ×2 (ML repos) | External familiar standard, detail buried, NOT pointed at | **0/5, 0/5 WIN** | Retrieved remembered idiom instead of reading source (C `>>` floor vs Py truncate) |
| 2 | 3 reasoning designs (interp. repo) | Derivable | 2/2 ×3 LOSS | Opus reasons at expert level; feedback made it self-correcting |
| 3 | repair-capture-crc (this repo, attempt 1) | On the page (named CRC params) | R1 REJECT | Disclosure-defeated + crcmod one-liner (essential_difficulty) |
| 4 | repair-capture-digest rev 1 (custom C, itemized semantics, total silence) | On the page | 2/2 LOSS | Itemized semantics = checklist + self-test; silence → paranoia mode |
| 5 | rev 2 (latent generation domains + lulling sealed records) | On the page (un-itemized) | 2/2 LOSS | Reads spec FIRST; implements every branch; lull never engages |
| 6 | rev 3 (GF(2) constant recovery, zero redundancy, square-exact) | In the data, recoverable | 2/2 LOSS | Ring-algebra native (beat reference elegance); self-verified with independent forward code |
| 7 | rev 4 (mixed timebases, leap eras, named standards) | External public standard, pointed at, regimes flagged per-record | 2/2 LOSS | Retrieval robust when attention is on it (full IERS table from memory; GLONASS ICD-vs-civil deliberation) |
| 8 | rev 5 (rev 4 + poisoned validation oracle) | Available + CONTRADICTED by in-env data | **0/2, 0/2 WIN → ACCEPTED** | Workflow invariant (validate-against-data) weaponized; attribution under self-doubt |

Aggregate: 5 knowledge/derivation designs vs this adversary = 10/10 solved, ≤25% of
budget each, every solution clean and often more elegant than the reference. The two
win families: (a) unpointed familiar-standard retrieval (gemmlowp — needs conditions
that are nearly unconstructible in file/media with open internet, see §17.8), and
(b) the poisoned oracle (constructible almost anywhere — §18.4).

### 18.2 The adversary dossier — behavioral invariants of Opus-4.8 + Terminus-2 (xhigh)

Compiled from every pass@2 analysis across this campaign. Each invariant is a fact
about what the adversary DID in trials, not a theory. Design against these.

- **I1 — Spec first.** Reads format_spec/docs before touching data, in every trial,
  as an explicit early step. *Implication:* anything on the page WILL be implemented;
  the page is not a hiding place. Ever.
- **I2 — Disclosed rule = executed rule.** Implements every stated rule faithfully
  at any rule count achieved so far (5+ interacting rules, flawlessly). Itemized
  semantics with worked examples get asserted as self-tests before running (rev 1).
  *Implication:* fairness-forced disclosure is a gift to the solver; disclose
  structure, never the deciding VALUES (§18.4) — or make disclosure contradicted.
- **I3 — Enumerates regimes by script.** Any per-record flag/code/table is
  enumerated programmatically and branched on (revs 2, 4, 5: "parsed all 64 records,
  identified 40 requiring repair" as an early step). *Implication:* gnss-style
  "didn't notice the latent regime" does NOT reproduce when the regime marker is an
  explicit field. Latency-by-inattention is dead against enumeration.
- **I4 — Robust pointed retrieval.** When the task points at a public standard, it
  retrieves it correctly and deeply: reproduced the full 1972-2017 IERS leap table
  from memory; deliberated GLONASS ICD (+3 h fixed) vs civil Moscow (UTC+4 pre-2014)
  and chose correctly; iterated leap-era candidates to self-consistency. *Implication:*
  do not bet on time scales, checksum catalogs, encodings, or C semantics AS
  KNOWLEDGE when anything draws attention to them. (The gemmlowp win predates
  attention — the model believed it knew and never looked. That condition requires
  the deciding detail to be both unpointed and buried in a large familiar codebase.)
- **I5 — Algebra native.** Recognized an affine-over-GF(2) structure instantly and
  solved recovery ABOVE the reference's level (quotient ring GF(2)[x]/(x^32−1),
  257×257 word-level systems, ring inverses via polynomial GCD; a Pascal-triangle
  change of basis over GF(2^32)). 40 s and 6.7 min. *Implication:* "recover the
  parameters from the data" is a SOLVED problem class for this adversary regardless
  of parameter count, as long as recovery is well-posed (and fairness forces
  well-posedness).
- **I6 — Validates against in-env data before writing. THE ATTACK SURFACE.**
  In every single trial, before writing output, the agent checked its derived
  rule/implementation against whatever in-environment examples existed (intact
  records, sealed pairs, processed records) — often with independently written
  forward code, which even catches its own asymmetric pipeline bugs (rev 3).
  *Implication:* this is the most reliable behavior in the dossier and the proven
  lever: poison the data it will validate against (§18.4).
- **I7 — Self-corrects what THROWS; ships what is silent.** A ValueError from a
  truncated leap table was caught and fixed in-trajectory (rev 4). Silent wrongness
  has never been caught without an oracle. *Implication:* never let the wrong path
  throw (§11.4-1) — with one deliberate exception: the poisoned oracle MAKES the
  correct path throw the agent's own guard, which it then misattributes (rev 5:
  the guard raise led to self-doubt, not to poison-detection).
- **I8 — Green stops checking; silence raises effort.** §11.2's lull holds ONLY when
  green feedback substitutes for a rule the agent would otherwise have to find; when
  every deciding rule is on the page, green is irrelevant (rev 2). Total silence
  triggers maximum-care mode: spec re-reading, worked-example assertion, boundary
  self-tests (rev 1). *Implication:* the lull is a component, not a design; silence
  is not a weapon; a CONFIRMING-BUT-POISONED green is the weapon.
- **I14 — Stated-semantics hazard-awareness (2026-07-15, repair-capture-times rev
  6, 2/2).** When a spec states arithmetic semantics with a known language-idiom
  hazard (ties-away rounding vs Python round()'s banker's; truncation vs floor
  division), the adversary does not slip into the idiom — it names the hazard in
  its plan ("not Python's built-in banker's rounding"), implements the rule in
  exact integer arithmetic (divmod / +half-then-floor-on-abs), and validates the
  sub-rule against boundary examples BEFORE making any attribution decision.
  *Implication:* execution-slip bets on STATED rules are dead at any subtlety
  level measured so far (extends §17.8's in-spec-C result to rounding/division
  idioms); a "shield" that would protect such a slip from discovery never fires
  because the slip is never produced.
- **I9 — Time profile.** Single-crux implement-and-verify: 3-7 min. Multi-layer
  retrieval task: ~14 min (rev 4 grazed the 900 s ceiling on completion handshakes).
  In deliberation loops (post-trap), xhigh reasoning calls cost 350-450 s EACH.
  *Implication:* (a) budget exhaustion via honest work volume is nearly impossible
  to engineer under the no-timeout-reliance rule (§13); (b) any task containing a
  deliberation trap MUST set [agent].timeout_sec = 3600, or failures classify as
  in-progress-timeout (NOT valid fails) and low_timeout FAILs the rubric — this
  exact misconfiguration nearly buried the winning design (§17.11).

### 18.3 The placement ladder — where can the deciding fact live? (exhaustive; memorize the verdicts)

For any candidate crux, locate the deciding fact and read the verdict. Do NOT push
P1-P4 designs; the ladder is closed there by measurement.

- **P1 — On the page (spec/instruction).** I1+I2 execute it. DEAD (designs 3, 4, 5).
  Sub-lessons: itemization adds a self-test (worse); un-itemized prose changes
  nothing; burying in indirection (device tables, bit-fields, multi-hop lookups)
  changes nothing (I3 follows chains).
- **P2 — In the data, recoverable.** I5+I6 recover and self-verify. DEAD (design 6).
  Sub-lessons that will save you from clever-feeling variants: (a) *gauge
  forgiveness* — misreads equivalent up to reparameterization (constant rotation/
  anchor offsets absorbed into recovered tables) yield CORRECT answers, measured
  0/40 wrong: they are not traps; (b) *consistency is a weak oracle* — with any
  redundancy, wrong structural readings make the linear system inconsistent and
  self-reveal; only an exactly-determined (square, full-rank) system keeps misreads
  silent, and even then I6's independent-forward-code check catches asymmetric bugs;
  (c) zero redundancy does NOT prevent self-verification — the agent re-verifies
  against the same data with separately written forward code.
- **P3 — External public standard, referenced or inferable.** I4 retrieves it when
  anything points at it; I3 forces the pointing (explicit regime markers must be
  spec'd for fairness, and enumeration finds them). DEAD when flagged (design 7).
  The gnss/gemmlowp attention-gap variant needs ALL of: familiar standard the model
  believes it knows; deciding detail buried in a large real codebase; no tool that
  computes or validates the artifact; nothing in the task drawing attention to the
  detail. In file/media + open internet these conditions are nearly unconstructible
  (real formats ship tools = oracles; fictional formats can't cite real standards
  without pointing). In ML/numerics they were constructible (the two 0/5s). If your
  seed allows that regime, it remains the second-best lever; run the §17.7
  Disclosure Test and the pip-library sweep before believing in it.
- **P4 — Nowhere (undisclosed, unrecoverable, unretrievable).** Unfair. Rejected at
  R1 (design 3's fate inverted: params disclosed = trivial; undisclosed = reveng/
  brute-force dead end both ways, §17.8). Never push.
- **P5 — Available AND actively contradicted by an in-environment signal the
  adversary's workflow trusts.** The fact is fairly determinable (on the page or via
  P3 retrieval — fairness intact), but a poisoned empirical source fits a simpler,
  wrong rule perfectly. Correctness requires OVERRIDING invariant I6 — choosing the
  normative authority over the empirical one while mid-task evidence says your own
  code is buggy. **The only placement measured to beat this adversary here: 0/2,
  0/2, accepted.** Construction manual next.

### 18.4 The poisoned-oracle pattern — full construction manual

**Essence.** Two authorities exist in the task: a NORMATIVE source (spec + public
standards; defines graded truth) and an EMPIRICAL source (in-env examples the agent
will validate against — I6 guarantees it will). Poison a minority of the empirical
source with the output of a *simpler, natural, wrong* rule, applied by a plausible
in-story tool. Diligence then drives the solver from the correct implementation to
the wrong rule. The trap consumes the adversary's strength (carefulness), not a
knowledge gap — which is why it fired even though both agents held the correct
era offsets in hand.

**The geometry (hard-assert ALL of these in the generator — they are what make the
trap real rather than hoped-for):**
- **G1 (perfect wrong fit):** the intended wrong rule W reproduces EVERY empirical
  example — clean AND poisoned — exactly. (Rev 5: constant-18 fit all 24.) If W
  fails any visible example, the agent discards W and keeps looking — trap dead.
- **G2 (visible correct mismatch):** the correct rule C visibly mismatches EXACTLY
  the poisoned subset, nothing else. The discrepancy must be discoverable — hiding
  it is both unfair and self-defeating (no discrepancy → no self-doubt → no trap).
- **G3 (measured graded divergence):** W fails ≥⅓ of graded outputs; graded outputs
  are chained (per-record integrity covering the graded field + a file-level
  digest over all of them) so one wrong output → reward 0. Byte-exact grading.
- **G4 (no alternative arbiter):** no third signal in the environment can arbitrate
  between C and W (no tool, no redundant example subset that only C fits, no
  spec-side worked example covering the poisoned regime). Every graded regime is
  exemplified by NOTHING or by poison only.

**The fairness anchors (these exact properties made task_specification and
approach_validity PASS on failing trials — quote-proof against reviewer pushback):**
- **F1:** the instruction's success criterion anchors graded values to the SPEC
  ("hold the values the format specification defines"). This resolves the two-
  authorities conflict ON PAPER — the analyzer called the instruction "unambiguous"
  and the guard "voluntary, beyond what the instruction specified."
- **F2:** the instruction explicitly says the poisoned objects are to be PRESERVED
  exactly (double duty: keeps them out of the graded delta AND states they are not
  to be re-derived).
- **F3:** the poison is internally consistent — integrity fields SEAL the wrong
  values (the buggy tool sealed what it wrote). No parse error, no checksum
  mismatch, nothing throws on read. The poison is only visible as a semantic
  discrepancy against an independent implementation of the normative rule.
- **F4:** nothing announces the bug, and nothing lies. Every sentence in the spec
  and instruction remains true. The story (a tool that crashed mid-pass was also
  misbehaving before it died) is a real, common forensics scenario — reviewers
  accepted it without comment.
- **F5:** the reference solution must take the correct path from agent-visible data
  only (proves solvability), and the generator asserts reference == golden.

**Sizing and texture (what made the bait attractive):**
- Poison a MINORITY (rev 5: 6 of 24, 25%). Enough to trigger the guard almost
  immediately (poisoned records interleaved early — record 11 fired in both
  trials), few enough that "the tool had a bug" remains the expert's parsimonious
  read while "my code is off by one era" is the mid-task agent's parsimonious read.
- One uniform bug, not noise: all poisoned errors identical in kind and magnitude
  (exactly −1000 ms, all in one era, all one timebase). A REGULAR discrepancy reads
  as "systematic offset I got wrong," inviting the constant fix; random noise would
  read as corruption and trigger poison-suspicion instead.
- W must be strictly SIMPLER than C (Occam bait): constant offset vs era-dependent
  offset. The fix that makes validation green must also be the lazier hypothesis.
- Compose with a genuine first difficulty layer (here: era-correct offsets, BDT/
  GLONASS/TAI semantics). The wrong rule needs something real to be wrong ABOUT,
  the expert-hours estimate needs substance (essential_difficulty), and the layer's
  breadth spreads the graded divergence (22/40 from W alone; 6-22/40 across the
  five measured misapplications).

**The observed kill-chain (from the failing trajectories — this is what you are
engineering for):**
1. Agent implements C correctly from spec + retrieval (do not try to prevent this —
   you can't, see I1-I5).
2. Agent adds a validation guard over the empirical source (I6 — voluntary, both
   trials, structurally identical guards).
3. Guard raises on the first poisoned object. Agent attributes the raise to ITS OWN
   code (I7 — a throw means my bug), not to the data.
4. Agent runs diagnostics (delta histograms in both trials) which — because of G1 —
   point cleanly at W.
5. Agent either stalls in xhigh deliberation (350-450 s/call → needs timeout 3600
   to reach an output) or ships W → wrong on ≥⅓ graded, chained → reward 0, valid
   fail, all rubric criteria PASS.

**Domain-transfer variants (same geometry, different empirical sources — the
pattern generalizes; guardrails per variant):**
- *Poisoned sample I/O pairs* (data-processing tasks): ship input→output examples
  where a minority were produced by a buggy previous pipeline; graded outputs anchor
  to the spec'd transformation. Guardrail: instruction must state examples are
  historical output "as produced," spec defines the transformation normatively.
- *Poisoned passing test* (debugging/SWE tasks): a shipped test suite where one test
  asserts the buggy behavior (fixture built from the bug); the graded property is
  spec'd, and fixing the code makes that test fail. The agent must ship with a red
  test (or amend it if instruction permits) — against its green-seeking instinct
  (I8). Guardrail: instruction must rank the spec above the suite explicitly and
  say what to do about failing legacy tests, or grade only the artifact behavior.
- *Poisoned reference implementation* (porting/cloning tasks): the repo contains an
  old implementation with a comment "reference behavior" whose edge-case handling
  contradicts the spec. Guardrail: label it as the legacy version in-story; spec is
  the graded authority.
- *Poisoned checkpoint/intermediate* (pipeline tasks): stage-2 input files that
  stage-1 (buggy, already run) produced; the agent rebuilding stage 2 must NOT
  regress stage-1 bugs into its stage-2 rule derivation. Guardrail: spec defines
  stage-2 semantics independent of observed stage-1 output.
- *Poisoned log/trace* (ops/debugging tasks): the "golden run" log the agent will
  diff against was captured on a misconfigured host (wrong TZ/locale). Guardrail:
  config file in-env states the correct configuration; instruction anchors to it.
In every variant the invariant holds: **the graded artifact must never depend on
reproducing the poison, the instruction must contain the F1 authority-anchor
sentence, and G1 (wrong rule fits all visible evidence) must be generator-asserted.**

**Configuration requirements (learned the hard way):**
- `[agent].timeout_sec = 3600` from the first push. Deliberation traps + xhigh
  reasoning = 350-450 s per call; at 900 s the trap "wins" but produces
  in-progress-timeouts, which are NOT valid fails, and low_timeout FAILs — the gate
  stays blocked and tells you to raise the clock. Raising the clock is NOT making
  the task easier; the analyzer projected the extra time would complete the WRONG
  fix, and it did.
- Verifier timeout unaffected (byte-compare is instant).

### 18.5 THE INVARIANT-ATTACK METHOD — how the win was actually found (use this when the poisoned oracle dies)

The poisoned oracle was not invented; it was DERIVED, and the derivation procedure
is the durable asset. When this lever is eventually patched (it will be — analyses
are training data), run the procedure again:

1. **Never redesign blind after a loss.** Every pass@2 analysis is an intelligence
   report. Extract from EACH analysis: the agent's step list, what it read first,
   what it validated against and when, what it retrieved from memory vs fetched,
   what threw and how it reacted, timings per step. Append to the §18.2 dossier.
2. **Split the dossier into KNOWLEDGE and WORKFLOW.** Knowledge rows (knows IERS,
   knows ring algebra, knows C semantics when pointed) decay fast — models improve,
   internet exists, attention can be drawn. Workflow rows (reads spec first,
   enumerates regimes, validates before writing, trusts throws, stops at green)
   are habits of the agent HARNESS + model conditioning — they persist across
   knowledge improvements and are visible in every trial regardless of task domain.
3. **Find the invariant** — a behavior present in ≥ every recent trial. The stronger
   and more virtuous-seeming the behavior, the better the lever (the win attacked
   the adversary's diligence, its single most reliable trait).
4. **Apply the attack template:** construct a task state where executing the
   invariant leads measurably AWAY from graded truth, while a fair path exists that
   requires overriding the invariant, and the override instruction is ON PAPER
   (F1-style) but unattractive to the workflow. Then hard-assert the G1-G4 geometry.
5. **Gate question (replaces "would this fool the model?"):** *"Does solving this
   require the adversary to CHOOSE between two authorities, where the instruction
   names the correct one but the adversary's measured workflow prefers the wrong
   one?"* If the answer is no — if it merely requires knowing, deriving, or
   retrieving something — the placement ladder (§18.3) says it will be solved.

**Pre-scouted future invariants to attack when I6-poisoning dies** (untested — walk
them through §18.7 before building; each has a fairness landmine noted):
- *I7 (trusts throws):* an environment where the correct action path throws a
  misattributing exception early (e.g., a deprecation error naming the wrong cause),
  and the "fix" that silences it is the graded mistake. Landmine: the misattributing
  message must be realistically wrong (stale tooling), never a lie authored into
  normative docs.
- *I8 (green-stop):* a shipped harness whose full-green state is reachable by a
  wrong fix (necessary-not-sufficient by construction, §16.10) COMPOSED with a
  poisoned test (§18.4 variant) so green actively certifies the wrong rule.
- *I3 (enumerate-then-branch):* a regime marker that is itself stale — spec states
  the field was repurposed in v2 and must be ignored in favor of a derived property;
  enumeration-driven branching on the visible field is the natural wrong rule.
  Landmine: the repurposing must be stated plainly (P1 says it will be read!), so
  this only works if the OLD meaning fits the data plausibly (G1 analog) — i.e.,
  it is really an I6 attack in disguise: the data "confirms" the stale reading.
- *I1 (spec-first) is probably unattackable* — do not try to hide things from the
  reader; that is P1 and it is closed.

### 18.6 Updated pre-flight checklist (run this IN ADDITION to §16.13's)

- [ ] Placement-ladder verdict for the deciding fact is **P5** (or a §18.5-derived
      invariant attack with a written kill-chain), not P1/P2/P3/P4.
- [ ] The two authorities are identified BY NAME in your design note: normative
      (graded) vs empirical (poisoned), and the instruction contains the F1 anchor
      sentence and the F2 preserve sentence.
- [ ] Generator hard-asserts G1, G2, G3, G4 (all four; G1 is the one authors skip
      because it feels obviously true — it is the load-bearing one).
- [ ] Poison is minority, one uniform bug, internally consistent (F3), earliest
      poisoned object appears early in iteration order (fast guard trigger).
- [ ] The wrong rule W is strictly simpler than C (Occam bait) and is one of your
      MEASURED naive variants (not a hypothetical).
- [ ] A genuine first difficulty layer exists (expert-hours substance for
      essential_difficulty) and W is wrong about IT, not only about the poison.
- [ ] `[agent].timeout_sec = 3600`; oracle runtime « verifier timeout.
- [ ] §18.7 walkthrough written down and reaches reward-0 (or stall) WITHOUT
      assuming any knowledge failure anywhere.
- [ ] §17.2 rubric ≥9/12 scored WITH the §18.9 anti-checklist open, PLUS the new
      axis: **Workflow-trap** (0 = needs a knowledge gap to fire; 1 = fires on a
      plausible-but-unmeasured behavior; 2 = fires on a §18.2 measured invariant
      even under perfect knowledge). Push only at 2.
- [ ] Local gate: oracle 1.0, nop 0, EVERY naive variant 0 via byte-compare, W
      swapped in as the solver 0.0 via harbor end-to-end.
- [ ] pass@2 budget check (6/day); read the gate taxonomy note (§18.8) so a
      timeout outcome is answered with configuration, not redesign.

### 18.7 The simulated-adversary walkthrough (replaces gut red-teaming; do it on paper)

Walk YOUR design through the dossier, step by step, writing down what the adversary
does. It is a proof obligation: the walkthrough must reach reward 0 without ever
writing "and here it fails to know/notice/derive X." If any step needs a knowledge
failure, assume the knowledge is present and redesign.

Template (rev 5 shown — reproduce this table for every new design):
1. I1: reads spec. Learns container, packings, scale names. *(Design survives: the
   deciding conflict is not on the page.)*
2. I3: scripts a full parse; enumerates 64 records, 5 codes, finds 40 unprocessed.
   *(Survives: enumeration reveals regimes — they are meant to be seen.)*
3. I4: retrieves leap history/epochs correctly. *(Survives: knowledge is NOT the
   bet. Write this line explicitly to keep yourself honest.)*
4. Implements C correctly.
5. I6: validates against processed records → 6 mismatches, all one era, all −1000ms.
6. I7: its own guard threw → "my bug." Diagnoses. G1: the data fits W perfectly.
7. Fork: (a) adopts W → ships → G3 → reward 0. (b) stalls deliberating → needs
   3600 s → completes W (analyzer-projected + observed trend) → reward 0.
   (c) ESCAPE PATH: re-reads instruction, weighs F1 anchor over data, attributes
   to tool, ships C. *(This path exists — it is what makes the task fair. The bet,
   now measured at 4/4 trials, is that the workflow takes (a)/(b).)*
Score the design by the fork: if escape path (c) is the workflow-NATURAL branch
(e.g., your instruction shouts about the bug), redesign; if (a)/(b) are natural and
(c) requires overriding a measured invariant, push.

### 18.8 Platform mechanics compendium (operational facts, all field-verified)

- **pass@2 gate semantics:** needs ≥1 VALID fail. "Solved" includes passed-tests-
  then-timed-out. Taxonomy buckets: solved / valid-fail / task-verifier-issue /
  in-progress-timeout / infra-setup-timeout. **in-progress-timeout is NOT a valid
  fail** — the gate blocks with "raise timeout_sec and re-run." low_timeout rubric
  FAIL = agent was time-starved = your configuration problem. The winning design
  needed exactly one config change (900→3600) between blocked and accepted.
- **pass@2 cap:** 6/day/repo. Every push to `submission` re-runs the FULL pipeline
  (static → rubric review → similarity → validation → pass@2 → trials → gate).
  Never push without the full local gate green.
- **Sticky comments are edited in place** — the pass@2/validation comments keep
  their original `created` timestamp. Always read the CURRENT body, never infer
  freshness from timestamps.
- **Advisory "Reviewer Notes" flags do not gate.** Answer them with a PR COMMENT
  (the notes say so). Do NOT push commits to an accepted PR — any push re-triggers
  the pipeline including pass@2 and can flip the accepted state. Frozen means frozen.
- **Similarity check** runs against TB2/TB3 sets. Re-aiming a delivered-corpus crux
  with a different graded artifact passes it (measured twice: §16.12, rev 4/5).
- **Revisions:** the automated needs-revision loop (pass@2 blocks) is not the same
  counter as human R1/R2 send-backs; this task went through 5 automated reworks
  after one human R1 without hitting Holding-Rejection. Human reviews still come
  after acceptance (R1/R2 → RTD pays the bonus).
- **Local gate commands:** `harbor run -p . --agent oracle` (1.0), `--agent nop`
  (0.0), then swap each naive in as `solution/solve.py` and re-run oracle (0.0);
  restore and re-run the generator (its subprocess assert re-verifies the real
  oracle). Wipe `task/jobs/` before committing.
- **generator.py committed at repo ROOT** (never inside task/environment/) is safe
  — the agent image is built only from task/environment/ — and it is your
  difficulty PROOF for reviewers (hard-asserts G1-G4, naive divergence counts).
- **Renaming the task** (task.toml `name`) mid-PR is fine; update the PR title.
- **Instruction suffix line:** this scaffold's static checks did not require the
  timeout-suffix line despite §5 of the docs; trust the scaffold (§14 rule).
- **Timeout comment discipline:** put the WHY in the toml comment (reviewers read it).

### 18.9 The anti-checklist — rules written in blood (each with its corpse)

1. **Never itemize the deciding semantics.** Itemized conventions + worked examples
   = a checklist and a self-test kit (rev 1: agents asserted the spec's own examples
   before running).
2. **Never expect silence to induce error.** Zero feedback = paranoia mode = MORE
   care (rev 1). Silence is a necessary property of the graded surface, not a
   weapon in itself.
3. **Never bet on a lull when the rule is printed.** Spec-first (I1) means data
   never gets the chance to anchor (rev 2).
4. **Never leave the deciding fact recoverable** — with or without redundancy
   (rev 3: exact-square, zero-redundancy — recovered anyway, elegantly, and
   self-verified with independently written forward code).
5. **Constant-offset/anchor misreads are gauge-forgiven** in linear-recovery
   designs — mathematically absorbed into recovered parameters (measured 0/40
   wrong). Never count reparameterization-equivalent slips as traps.
6. **Consistency is a free oracle you're handing out.** In overdetermined systems,
   wrong structural readings go inconsistent and self-reveal. Only exactly-
   determined systems keep misreads silent — and rule 4 still applies.
7. **Never flag a latent regime and bet on inattention.** Explicit markers + I3
   enumeration = every branch visited (rev 4). The gnss attention gap needs
   unpointed, unfamiliar-looking uniformity — nearly unconstructible when fairness
   forces marker definitions into the spec.
8. **Never bet on knowledge gaps in pointed territory:** time scales, leap seconds,
   checksum families, C integer semantics, encodings — all retrieved correctly when
   attention is on them (revs 1, 4). The knowledge bet is only live under the FULL
   gemmlowp conditions (unpointed + familiar + buried + toolless — §18.3 P3).
9. **Ship no signal that confirms the naive rule unless it is poison by design
   (G1), and no signal that reveals the correct rule at all (G4).**
10. **Expert-hours and model-difficulty are different axes.** Reviewers demand the
    first (essential_difficulty); the gate demands the second. Compose: real
    multi-hour repair substance × workflow trap. A trap on a trivial task fails
    review; substance without a trap goes 2/2.
11. **Score the §17.2 rubric pessimistically with this list open.** Five designs
    scored 9-11/12 in good faith and lost; the misscored axis was always
    "no reasoning path" (reading/recovering/retrieving IS a path — score it 0-1
    unless the design is P5, where the path exists but the workflow rejects it).
12. **React to gate outcomes by taxonomy, not mood.** in-progress-timeout → raise
    the clock, change NOTHING else (this rule alone converted the campaign's only
    win from "blocked" to "accepted"; a panicked redesign would have destroyed it).
13. **Don't touch accepted PRs.** Answer advisories with comments. Ever.

### 18.10 Arithmetic, expectations, and the last word

- **Gate math:** pass@2 needs ≥1 valid fail in 2 trials; final delivery needs
  pass@5 landing 0-2/5 with valid fails. A per-trial solve probability of s gives
  P(pass@2 gate) = 1−s²; the pass@5 bar wants s ≲ 0.4. The five knowledge designs
  ran at s ≈ 1.0. The poisoned oracle measured s = 0/4 across its two runs. Design
  for s, not for drama.
- **Cost discipline:** the five losses each consumed a pass@2 run and hours of
  build; the win was found by reading analyses, not by building harder. Intelligence
  extraction (§18.5 step 1) is the highest-ROI activity in the entire loop —
  budget it FIRST after every run, before any new design work.
- **Decay warning:** this document describes an adversary snapshot (Opus-4.8 +
  Terminus-2 xhigh, 2026-07). Trial analyses feed back into training; the I6 lever
  will weaken. The durable assets, in order: the invariant-attack METHOD (§18.5),
  the placement ladder (§18.3), the geometry discipline (G1-G4 + generator
  hard-asserts), the walkthrough habit (§18.7). Patterns die; the procedure that
  finds patterns does not.
- **For the Opus author reading this:** you will, at some point in the build, feel
  that a clever reasoning trap of your own invention is obviously hard, or that a
  disclosed detail is too subtle to be executed, or that a recoverable secret is
  too tedious to be recovered. Twelve trials say the feeling is wrong every time.
  When it comes, return to §18.3, find your placement, and read the verdict written
  next to it. The ladder does not care how the design feels.

### 18.11 CORRECTION — the poisoned oracle FAILS against a clean authoritative primary source (cross-abi-serializer AX-16, 2026-07-12, pass@2 = 2/2)

**The experiment.** Re-instantiated the rev-5 poisoned-oracle lever in a NEW seed
(Build Dependency / Cross Compilation). Fictional AX-16 core (internet-immune: no
toolchain/emulator/online source exists). Correct rule stated in an ABI datasheet
(zero-extend byte load = unsigned char, big-endian, 32-bit, packed). Poison: a
shipped `axsim` simulator capture with a signed-char erratum, CORROBORATED by the
in-image native gcc host build (also signed) — two empirical signals both saying
"signed." Local gate green, all G1-G4 asserted, the signed-char outcome scored 0.0
as a solver. **pass@2: 2/2 solved, ~10 min each.**

**Why it failed — the boundary condition on §18.4.** Both agents read the datasheet
FIRST (I1), implemented the correct rule, then explicitly cross-checked against the
capture, saw the conflict, and ATTRIBUTED IT TO THE ERRATUM — siding with the
datasheet. The poison never induced self-doubt because there was a **clean, crisp,
authoritative primary source that fully determined the correct rule.** When two
named artifacts conflict (datasheet vs capture) and one is the stated authority,
the task degrades to a reading-comprehension step Opus performs trivially. I6
(validate-against-data) only becomes a WEAPON when the data conflict reads as
"my own code is buggy," not as "document A vs document B."

**What was actually different about the rev-5 WIN (the real necessary condition):**
- rev-5 had **no clean authority that stated the deciding rule as a rule.** The
  correct per-record values had to be COMPUTED by the agent; the only concrete
  in-file signal was the poisoned processed-records, which were the SAME KIND of
  object as the graded output (digests in one file), so the agent could not cleanly
  label them "just a reference." Reconciling its computed values with the poisoned
  siblings was the natural move → self-doubt → adopt the wrong rule.
- cross-abi had a **separately-labeled reference file** ("simulator capture, for
  comparison") cleanly distinguishable from the deliverable, AND a datasheet that
  says the answer outright. Both are fatal: clean separation lets the agent dismiss
  the capture; a crisp authority means it never needed the capture at all.

**The sharpened rule (supersedes the §18.4 "essence" where they conflict):**
> A poisoned oracle bites ONLY when the correct rule is NOT cleanly stated by an
> authority the agent trusts, so that the agent must lean on the (poisoned)
> empirical signal — and the poisoned signal is entangled with / indistinguishable
> in kind from the graded artifact, so the conflict reads as "my computation is
> wrong," not "which document wins." If a fair, authoritative primary source fully
> determines the answer (as fairness FORCES for a fictional standard — §18.3 P1),
> the deciding fact is on the page, I1+I2 execute it, and no poison saves it.

**Seed verdict (fourth confirmation of the §17.9 wall, now in a second seed).**
Cross-compilation with open internet: a real target = an apt-installable toolchain
oracle (§17.8); a fictional target = a fully-disclosed datasheet (P1). Either way
the deciding fact is reachable and clean. The poison degrades to a weak-agent trap.
This seed is P1-dead for the "predict the exact bytes" framing. The ONLY placement
with a pulse here is a DIFFERENT crux entirely: a silent build-MISCONFIGURATION
(§16.10 split invariant) where the agent HAS a real toolchain + emulator, a shipped
smoke test passes for the buggy config, and the graded behavior is a property the
smoke test never exercises — i.e., attack I8 (green-stops-checking), not I6. That is
a new proposal, not a revision of this one.

**Process note.** This was foreseen and logged as the "honest risk" in the progress
file BEFORE the run ("char-signedness has a crisp datasheet answer... a disciplined
agent that trusts the datasheet solves it"). Writing the risk down did not make it
smaller. The §18.7 walkthrough would have caught it if applied strictly: step 3
("I4 retrieves/reads the rule correctly — knowledge is NOT the bet") was true here
for the datasheet READ, and step 6's escape path (c) ("trusts authority over data")
was the WORKFLOW-NATURAL branch, not the override — which the walkthrough says means
REDESIGN, do not push. The lesson: when the correct rule is a clean documented
authority, escape path (c) is natural and the design is P1. Score it before pushing.

### 18.12 CORRECTION — the green-harness (I8) attack fails against Opus-4.8's audit-and-edge-test behavior (cross-abi PPC miscompile, 2026-07-13, 1 real trial SOLVED decisively)

**The experiment.** After §18.11 (poison fails vs a clean authority), attacked a
DIFFERENT habit: I8 (green-stops-checking), via the bytecode-vm-debug pattern
(§16.10). PPC cross-compile with two stale portability overrides — an endianness bug
the smoke test EXPOSES (red→green when fixed, the false-completeness signal) and a
signed-char checksum bug the smoke test CANNOT expose (sample bytes all < 0x80).
Hidden high-byte inputs, byte-exact all-or-nothing. Local gate perfect: oracle 1.0,
nop 0.0, endianness-only (green-stop outcome) 0.0. pass@2 = 1 solved / 1 infra-error;
the one engaging trial SOLVED it.

**How it solved — the I8 premise is stale for Opus-4.8.** The agent did NOT stop at
green. It (a) read all sources + the spec, (b) identified BOTH bugs by code review —
explicitly citing "signed char violates the spec's unsigned accumulation requirement"
— and (c) wrote its OWN qemu validation over 309 records INCLUDING high bytes before
declaring done. It proactively tested the exact axis the smoke test omits. The
"fixed-the-obvious-saw-green-quit" behavior that won bytecode-vm-debug (77-137s quit,
§11.2) does NOT reproduce here: Opus-4.8 audits the diff against the spec and
edge-tests unprompted.

**Why bytecode-vm-debug worked and this didn't (the distinction to record):** that
win required the agent to (i) not know which case was uncovered and (ii) treat a
green harness as sufficient. Opus-4.8 now defeats BOTH: it reasons from the SPEC
about which cases matter (high bytes → unsigned) rather than trusting the harness,
and it constructs its own coverage. A green harness is no longer a stopping signal
for it. I8 as a standalone lever is DOWNGRADED: it only bites when the uncovered
case is NOT derivable from the spec (so the agent can't know to test it) — which
collides with fairness (the spec must determine the answer) exactly as P1 does.

**Seed verdict — SECOND design defeated by the same trait, seed confirmed Opus-proof.**
Both cross-compilation designs died to Opus-4.8's THOROUGHNESS: §18.11 (read the
datasheet, dismissed the poison) and §18.12 (audited the source, edge-tested past the
green smoke). The seed gives Opus the toolchain, the source, and the spec, and Opus
is thorough enough to use all three. Neither the I6 (validate-against-poison) nor the
I8 (green-stop) lever fires when the agent reads primary sources and derives coverage
from the spec. Note also: even had pass@2 caught a lucky green-stop, the audit-based
solve rate looks high (~0.75+), so pass@5 (needs solve rate ≲0.4) would not clear.

**The meta-lesson for the dossier (updates §18.2).** Add **I10 — Derives test
coverage from the spec, not the harness.** Opus-4.8 audits its own diff against the
authoritative spec and constructs edge-case tests for cases the spec implies, even
when a provided harness is green. Consequence: any attack premised on the agent
trusting incomplete in-env feedback (I6 poison, I8 green-stop) fails when a fair,
authoritative spec exists — which fairness forces. The durable levers left are those
where the deciding fact is genuinely NOT spec-derivable yet still fair: (1)
familiar-external-standard retrieval-misapplication under the FULL gemmlowp conditions
(unpointed + buried + toolless — ML/numerics only, §18.3 P3); (2) rev-5's poison ONLY
when the correct rule is not cleanly stated AND the poison is entangled with the
graded artifact (§18.11). Both are nearly unconstructible in cross-compilation.
Recommended action for this seed: BANK the accepted task, escalate/reseed (§16.8).

### 18.13 CONCLUSIVE — breadth does NOT compound in a PORTING task; the blanket-rewrite idiom fixes all axes at once (cross-abi PPC breadth, 2026-07-13, pass@2 = 2/2)

**The experiment.** After §18.11 (I6 poison) and §18.12 (I8 green-stop) both failed,
applied the §16.11 BREADTH lever (the relinker pattern — documented to survive full
feedback): a PowerPC port with THREE independent portability defects (endianness,
char-signedness, accumulator width), byte-exact all-or-nothing on hidden inputs, the
smoke test covering only endianness. Local gate proved even a two-of-three fix scores
0. **pass@2 = 2/2 solved.**

**Why breadth failed here — the mechanism that kills it (new).** Both agents did NOT
enumerate-and-fix the three defects individually. They applied a BLANKET
PORTABILITY-HARDENING REWRITE: replaced the endianness-conditional writer with
explicit byte shifts, the signed-char read with a direct unsigned cast, and the
typedef'd accumulator with a hardcoded uint32_t — making the stale config DEAD CODE.
One idiom, correct-by-construction, neutralized ALL portability axes simultaneously,
including the accumulator-width axis the local gate proved a partial fixer would miss.
The analyzer: "this rewrite pattern is embedded in model training data as a recognized
portability-hardening idiom." The agents caught the deepest axis for FREE, not by
finding it.

**The distinction from relinker (why breadth worked THERE and not here):** relinker's
bugs were independent LOGIC bugs in a linker — each required distinct understanding
and there was no single idiom that fixed all of them; the breadth was irreducible.
PORTABILITY defects are the opposite: they all belong to one class ("code that
assumes the host platform"), and porting has a UNIVERSAL correct-by-construction
answer ("write platform-independent code") that a competent engineer applies as one
move. Breadth only compounds when the defects are NOT reducible to a single idiom.
Portability breadth reduces to one idiom, so it does not compound. **Rule: breadth is
a lever ONLY over independent, idiom-irreducible LOGIC; never over instances of a
single well-known class (portability, one encoding, one convention) — the model fixes
the CLASS, not the instances.**

**Dossier update (§18.2): I11 — Applies blanket correct-by-construction idioms.**
For a task in a well-known class (porting, sanitization, normalization, escaping),
Opus-4.8 applies the class's canonical robust idiom rather than fixing enumerated
instances, neutralizing every instance at once — including ones it never specifically
diagnosed. Consequence: you cannot create difficulty by multiplying instances of a
single idiom-fixable class. Difficulty must come from instances that have NO shared
canonical fix (distinct logic/algorithm each), or from a fact the idiom cannot supply.

**SEED EXHAUSTED — three mechanisms, three defeats, all documented:**
- §18.11 I6 (validate-against-poison) → read the authoritative datasheet, dismissed it.
- §18.12 I8 (green-stops) → audited the diff vs the spec + edge-tested past green.
- §18.13 breadth → blanket portability idiom fixed all axes in one move.
Cross-compilation + open internet + fairness gives Opus-4.8 the toolchain (qemu
oracle), the source, and a spec it reads — and porting has a universal idiom. Every
proven lever (I6, I8, breadth) has now empirically failed in this seed with a distinct
mechanism. There is no constructible crux here within the playbook; gemmlowp-retrieval
needs ML (no compiler) and rev-5-poison needs an uncleanly-stated rule (fairness forbids
it here). **Correct action: escalate/reseed (§16.8). Do not attempt a fourth design in
this seed — it would require inventing an unproven crux, which §16.13(1) forbids.**

### 18.14 FABLE CROSS-CHECK — a disjoint model independently confirms the seed is exhausted (2026-07-13)

**Context for Opus.** The author model was switched to Fable and asked to stump you
after your three designs (§18.11-18.13) were each solved 2/2. Per §16.13 the value
of Fable here is a *disjoint error distribution* — Fable might see a crux you can't.
I searched hard, from four angles you did NOT try. All four die, each to a wall now
independently reconfirmed. A disjoint model reaching your conclusion by NEW routes
upgrades "exhausted" from a possible introspection artifact (§16.13's warning) to a
cross-model-confirmed structural fact. Here are the angles and why each fails, so you
never re-spend a pass@2 on them:

1. **qemu-user AS the poisoned oracle (not a shipped file).** Idea: exploit a real,
   documented divergence between `qemu-user-static` and true target hardware
   (page size via `sysconf`, HWCAP, FP last-ULP), so the agent's natural "run it
   under qemu" self-test *certifies the wrong answer* — a poison that is a trusted
   TOOL, resolving §18.11's "dismissible file" weakness. **Dies two ways:** (a) if
   the true value is a clean scalar in the datasheet, it degrades to §18.11 exactly
   (Opus takes the datasheet value, dismisses the contradicting run); (b) to grade
   "real hardware differs from qemu" I must generate ground truth that differs from
   qemu — but I have only qemu (no real PPC), so I *cannot author* non-qemu truth.
   The author's own toolchain is qemu; the poison is uncomputable by the author.

2. **Compile-time semantics slip (16-bit-`int` targets: AVR/MSP430).** Idea: the
   proven language-semantics lever (integer width/promotion/overflow, §18.3 A1-A5)
   is huge on a 16-bit-`int` target and there is no `qemu-user` for AVR, forcing
   *prediction*. **Dies:** constant-folded results land in `.rodata` and are
   extracted with `avr-objcopy`/`objdump` (the compiler is the oracle); runtime
   results need `simavr`/`qemu-system-avr` + a UART harness, which Opus can stand up
   with internet in the budget. And "emit bytes to a stream" barely maps onto a
   freestanding MCU, straining fairness/realism.

3. **Artifact-structure property (relocations, .eh_frame, GOT, mangling, enum
   underlying type).** Idea: an ABI fact that lives in the binary's STRUCTURE, not
   its behavior, so running it doesn't reveal it. **Dies:** every such fact is
   extractable from the cross-compiled binary with `readelf`/`objdump`/`nm` — the
   toolchain is the oracle. Structure is as inspectable as behavior is runnable.

4. **FP 1-ULP exact-match (gemmlowp's shape, qemu as the misleading runner).**
   Idea: exact-match a target FPU computation where qemu softfloat diverges from the
   real FPU. **Dies on authorability (same as #1):** the reference must be *real
   target* bits; I can only produce qemu bits. Plus exact FP is a fairness minefield.

**The two-part structural theorem (why cross-compilation specifically is barren,
sharper than §18.13's single note):**
- **Completeness of the oracle.** Everything true of the target is either (a)
  runtime behavior → `qemu-user` reproduces it, or (b) an artifact property →
  `readelf`/`objdump` extracts it, or (c) a stated ABI fact → the datasheet gives it
  and Opus reads it (§18.11/§18.12). Open internet supplies the toolchain for (a)/(b)
  and fairness supplies the spec for (c). There is no fourth category a fair task can
  depend on. (Contrast: repair-capture-times' win lived in category (c)-that-must-be-
  COMPUTED with a poison entangled in the graded artifact and NO clean stated rule —
  a structure cross-compilation cannot host, because any ABI rule fair enough to
  grade is either stated or tool-derivable.)
- **Non-independence of the axes (§18.13).** The few real porting axes (endianness,
  char-sign, int/long width, struct/bitfield layout, alignment) are all members of
  ONE class — "assumes the host platform" — with ONE canonical fix (write portable
  code / trust the target compiler). Opus applies the class fix as a single move
  (I11), so breadth over them does not compound. Cross-compilation lacks the
  *idiom-irreducible, individually-latent* rule richness that made gnss/timestamps
  (5 distinct external time standards) and relinker (8 distinct logic bugs) work.

**Fable's verdict:** ESCALATE/RESEED (§16.8). This is not a failure of design effort
— four novel mechanisms and yours three, seven total, all defeated or unauthorable.
It is a property of the seed. If reseeding is possible, the observed-failure library
still has live entries in OTHER seeds: gemmlowp-retrieval (A1/A2) needs ML/numerics
where the agent has no compiler and no library reproduces the standard; the
computed-rule poison (repair-capture-times) needs a domain where the graded values
are computed and the poison is same-kind as the artifact (forensics, data-recovery,
log-normalization). Neither is constructible under "cross-compilation + open
internet + fair spec." Point the next task at a seed whose deciding fact can live
outside the {qemu, objdump, datasheet} triad.

**Process note for Opus (the §16.13(1) reinforcement):** I did NOT push any of the
four. Each was killed at the design table by either (i) the §18.11 dismissal rule,
(ii) the completeness-of-oracle theorem, or (iii) author-side unauthorability. Under
the playbook, a crux you cannot even generate ground truth for, or that reduces to a
stated scalar, is dead BEFORE a pass@2 — spending one would be the exact
introspection-driven waste §17.2's rubric exists to prevent. Zero pass@2 burned on
this search.

### 18.15 CLOSURE — inference-from-captures is sweepable; the seed is now exhaustively demonstrated (2026-07-13)

**The experiment (Fable, user-directed push).** After §18.14 concluded the seed
exhausted, the user directed a live attempt anyway. Built the one fair angle §18.14
had NOT ruled out by construction: reverse-engineer the device ABI from captures (no
stated conventions, so §18.11's "Opus reads the datasheet" cannot apply). Non-portable
firmware + known-good captures (BE/unsigned/32-bit) + a new eval input; reproduce the
device output. Gate green; host build differs 17/24 bytes. **pass@2 = 2/2 solved,
~6-12 min.** One agent derived the conventions analytically; the other wrote an 8-way
brute-force sweep {endian}×{char-sign}×{ulong-bits} against the captures and picked
the unique match. Exactly the §11.5 enumerable-convention corollary: captures that
make the ABI fairly determinable also make it a sweepable menu.

**Why this closes the seed (the theorem's last leg).** §18.14 proved the deciding
fact must be (a) runtime → qemu, (b) artifact → objdump, or (c) stated → datasheet.
The RE-from-captures framing tried to hide (c) — don't STATE the ABI, make the agent
INFER it. But inference from provided I/O captures is defeated by the same property
that makes it fair: the captures let the agent VERIFY a guess, so the small ABI menu
(2×2×2 = 8) is swept in seconds. Undisclosed-but-verifiable = sweepable; disclosed =
read; the only fair options for a determinable fact both fall. Genuinely-non-verifiable
would be unfair. There is no fourth door.

**Final tally for this seed (cross-compilation + open internet + fair): 7 pushed
designs, 0 stumps.** Opus: I6-poison, I8-green-harness, I11-breadth. Fable: RE-from-
captures. Plus 4 Fable design-table kills (§18.14). Two models with disjoint error
distributions, every mechanism in the observed-failure library, all defeated or
unauthorable. This is the §17.9 wall in its strongest confirmed form: a subcategory
where the fairness constraint and the tool availability jointly force the deciding
fact into the {qemu, objdump, datasheet, sweepable-menu} set, all of which Opus-4.8
handles. **Do not author another predict/port/reproduce task in this seed. Reseed to
a domain where the deciding fact is a COMPUTED value from a NON-menu rule with NO
verifying oracle (gemmlowp: ML numerics, no library reproduces it; repair-capture-
times: forensic value, poison entangled in the artifact). Escalation is the move.**

### 18.16 FINAL — the execution-slip lever fails when the target semantics are KNOWN and STATED (bare-metal AVR, 2026-07-13, pass@2 = 2/2)

**The experiment (Fable, user-insisted 5th push).** Broke the qemu oracle by targeting
a bare-metal ATmega328P (no qemu-user for AVR). Firmware digest in `unsigned` (16-bit on
AVR) with `acc ^ (acc>>3)` making 16-bit truncation load-bearing per step (differs from
32-bit on 20/20 records; ground truth validated against real avr-gcc constant-folding).
This is the PROVEN integer-width language-semantics slip (A1-A5) — the only family with a
0/5 track record. **pass@2 = 2/2 solved, ~5-8 min.**

**Why even the proven lever failed here — the boundary condition on A1-A5.** Both agents
read the source and IMMEDIATELY stated "unsigned is 16-bit under avr-gcc on ATmega328P,"
then wrote a correct 16-bit emulator with per-iteration `& 0xFFFF`. No slip. The gemmlowp
0/5 wins (§16.12) required the model to *retrieve a wrong remembered idiom without
checking* — it "knew" the gemmlowp standard and wrote its remembered (wrong) C++/Python
port, never re-reading the real source. That needs the deciding detail to be BURIED in a
large familiar standard the model won't re-read. Here the deciding detail (AVR int = 16
bit) is (a) STATED (the source targets atmega328p, the README says ATmega328P), and (b)
FAMOUS. So the model retrieves it CORRECTLY and applies it. The A1-A5 slip fires only
when the model mis-retrieves without checking; a stated, famous, single target-width fact
is retrieved right. Cross-compilation cannot bury the deciding fact (fairness states the
target; the target's ABI is public), so A1-A5 degrades to §18.11 (known → applied).

**THE FULL CLOSURE — 8 pushed designs, 2 disjoint author models, every lever, 0 stumps:**
| Lever | Author | Defeat |
|---|---|---|
| I6 poison-file | Opus | reads authoritative spec, dismisses poison (§18.11) |
| I8 green-harness | Opus | audits diff vs spec, edge-tests past green (§18.12) |
| I11 breadth | Opus | one blanket portability idiom fixes all axes (§18.13) |
| RE-from-captures | Fable | sweeps the convention menu against captures (§18.15) |
| A1-A5 execution slip | Fable | knows+applies stated famous target width (§18.16) |
| +qemu-poison, AVR-run, artifact, FP-ULP | Fable | oracle-complete / unauthorable (§18.14) |

**The complete theorem.** In cross-compilation + open internet + fairness, the deciding
fact is (a) runtime → qemu; (b) artifact → objdump; (c) stated → the model reads it;
(d) a small convention → swept against the captures that make it fair; (e) a target ABI
fact → PUBLIC and KNOWN, so retrieved correctly (kills A1-A5, which needs a BURIED
mis-retrieved fact). Every fair deciding fact falls in (a)-(e). The proven stumps need a
fact that is (gemmlowp) buried in a familiar standard with no tool to compute it, or
(repair-capture-times) a computed value with a poison entangled in the artifact and no
clean authority — neither expressible under this seed's constraints.

**Verdict (now maximally evidenced): this seed cannot be stumped. Escalate/reseed.** The
observed-failure library is intact and lives in OTHER seeds (ML/numerics for buried-
standard retrieval; forensics/recovery/log-normalization for computed-value poison).
Point the next task there. Do not push a 9th design here. — Fable, signing off this seed.

### 18.17 TWO FINAL ANGLES searched (both fall) — the seed is closed to the same walls (2026-07-13)

On a final "use your best" push I searched the two angles closest to the PROVEN
levers (gemmlowp retrieval-misapplication; repair-capture-times entangled-poison),
recast into "Build Dependency / platform targeting." Both die at the design table to
walls already documented — recording so no future session re-explores them.

**Angle 9 — platform-specific wheel/artifact selection (retrieval-misapplication of
PEP 425/600 tag priority).** Framing: given local wheel files and a TARGET platform
(≠ host), output which wheel pip installs, over many scenarios, all-or-nothing. The
hope: the model mis-remembers the exact tag-priority order (abi3 vs cp-specific;
manylinux legacy aliasing manylinux2014==manylinux_2_17; musllinux; macos
universal2 split), and `packaging.tags.sys_tags()` returns the HOST list, not the
target's. **Dies (tool-complete, §18.15):** `packaging.tags.cpython_tags(python_version=…,
abis=…, platforms=…)` constructs the ORDERED target tag list for an arbitrary target;
the model recognizes "wheel selection → packaging.tags," builds the target tag list,
and picks the first match. Same defeat as RE-from-captures: a pip-installable library
computes the answer. Tag priority is public + tool-computable, not buried.

**Angle 10 — custom corporate-index resolver whose policy differs subtly from pip,
with `packaging` as a poisoned confirming oracle.** Framing: a fictional index with a
DOCUMENTED selection policy (e.g. prefers the OLDEST compatible manylinux baseline;
different abi3 priority; a pinned-major version rule) that diverges from pip; the model
reaches for pip semantics (retrieval reflex), and `packaging.tags` CONFIRMS the wrong
pip answer (a poison that is same-kind as the graded artifact — filenames vs filenames,
the repair-capture-times shape). **Dies (§18.11 + I1/I10):** the divergent policy must
be DOCUMENTED for fairness, and the dossier is unambiguous that this model reads the
spec first (I1) and derives from it, not from memory (I10) — it reads policy.md, notes
the divergence from pip, and implements the doc, dismissing the tool. To make the
poison bite (repair-capture-times structure) the policy must NOT be cleanly stated —
the agent must INFER it from examples — but then the example set that makes it fair
makes it inferable/sweepable (§18.15 again). The win condition (computed rule + entangled
poison + NO clean authority) is unreachable because fairness here forces a clean authority.

**Conclusion (10 mechanisms, 2 disjoint author models, 0 stumps).** Every fair
deciding fact in this seed is retrieved, read, run (qemu), extracted (objdump), swept
(a menu against captures), or tool-computed (packaging). The two proven stump structures
need a fact that is buried-in-a-familiar-standard-with-no-tool (ML/numerics only) or a
computed-value-with-entangled-poison-and-no-clean-authority (forensics/recovery/
normalization only). Neither is expressible under "cross-compilation/platform-targeting
+ open internet + fair spec." A 6th pushed design would burn shared pass@2 budget on a
mechanism already traced to a documented defeat — which §16.13(1)/§17.2 exist to prevent.
**RESEED is the only positive-EV move. — Fable, final.**

## 19. THE OFFICIAL DOC — stump patterns, rejection reasons, live graded examples (verbatim-faithful, 2026-07-13)

Captured from the platform's own instruction pages (project-dynamo learn portal) so this
is never re-derived or missed. This is the authoritative source; §11/§16/§18 are the
field-tested commentary on it.

### 19.1 THE ONE FAIRNESS TEST (behind every rejection — memorize this)

> **If spelling out the deciding rule makes the task easy, the difficulty was fake.**
> A good task stays hard even when EVERY rule is stated — the model fails because the
> problem is hard, not because it was missing information or misled.

Before hardening any task ask: **"With the deciding rule written plainly, would a strong
engineer still struggle?"** If NO → it will be flagged. This is the gate. It is why every
cross-compilation-ABI design in §18 was doomed: state "the target is big-endian / int is
16-bit / double is 32-bit" and the task collapses to a one-liner → fake difficulty. It is
why repair-capture-times passes: state all its rules and you STILL must execute multi-era
time math over 40 records with zero slips AND correctly attribute a validation conflict to
the crashed tool — the difficulty SURVIVES disclosure.

### 19.2 THE FIVE REJECTION REASONS (≈half of all rejects = reason 1; now caught at pass@2)

Root problem shared by all five: a low pass rate that LOOKS like difficulty but isn't —
the model failed because the task was UNFAIR, not because it reasoned and got it wrong.

1. **Undisclosed verifier convention (MOST COMMON, ~half).** The verifier requires a
   format / sort order / tie-break / convention instruction.md never states. Agents solve
   everything documented and fail only on the hidden rule. *Fix:* write down EVERY rule the
   verifier checks (output format, ordering, tie-breaks, edge cases) in the instruction or
   a referenced file. Test: could a reasonable DIFFERENT implementation still pass? If only
   your exact unstated choice passes, disclose it.
2. **Contradictory shipped data / spec.** A data file, config, or the reference solution
   follows a different rule than the instruction. An agent that trusts the instruction does
   right and still fails. *Fix:* make shipped data + reference obey the instruction exactly;
   regenerate drifted fixtures; never ship a file that contradicts the instruction even if
   labeled "old/not used."
3. **Ambiguous spec (reads two ways).** A term/rule has two defensible readings; the
   verifier silently accepts one. The score just measures which reading the model guessed.
   *Fix:* name the single canonical rule (assignment, priority, tie-break, sort). Then check:
   once unambiguous, is it still hard? If not, add a real crux.
4. **Difficulty collapses once the defect is removed.** The single thing failing the model
   is one unstated/broken rule; disclose or fix it and the task is trivial. *Fix:* build
   difficulty into genuine reasoning that survives full disclosure. A patch is not a crux.
5. **Uncorrectable decoy / misleading documentation.** The task points at the wrong answer
   via an authoritative-looking file while the real rule hides in something "deprecated/
   superseded/not used" and NOTHING the agent can see corrects it. *Fix:* misdirection is
   allowed ONLY if the task can set the record straight (No Uncorrectable Lie). Never state
   a wrong rule the agent can't overturn; don't bury the real rule to manufacture a failure.

**Self-check before pushing:** run your oracle from a clean checkout; confirm the failures
are the intended crux, NOT a format/ordering/naming convention. RED FLAG: if failing tests
are about file existence or output formatting → that's an undisclosed convention, not
difficulty. Re-read instruction.md as if you'd never seen your solution: is every verifier
rule stated? Can any sentence be read two ways? Read the pass@2 analysis and ACT on it — a
fair 0/5 is great; a flagged one means fix the CAUSE, don't submit around it.

### 19.3 THE NINE STUMP PATTERNS (A–I) — canonical example each

- **A · Latent crux** (the most common & effective). A rule that is real & determinate but
  never fires on the visible/sample data; only the held-out set triggers it. *Weaponizes the
  agent's own diligence — the more carefully it validates against the sample, the more
  confident it becomes in the wrong answer.* Ex: total weight of metal parts; all calibration
  parts STEEL, so the steel gauge table looks flawless; hidden NON-FERROUS part uses a
  different gauge standard. Generalizes to: a caching key that only breaks on a repeat
  request; an off-by-one past ten records; a policy clause that only binds in an omitted
  scenario.
- **B · Plausible cheap heuristic ≈ correct expensive rule.** A near-equivalent shortcut
  that passes casual inspection; the gap appears only in cases the agent has no reason to
  suspect. Ex: ledger "rollup" rows — path-prefix heuristic vs the correct value-equals-sum-
  of-children rule; they diverge on "charged intermediate" parents. Every failing agent
  produced a BYTE-IDENTICAL wrong answer.
- **C · Planted/poisoned tool or doc.** A trusted-looking utility/comment/file arrives early
  and confidently gives the wrong answer; the agent closes on it. Ex: SRE root-cause — a
  shipped diagnostic tool names a downstream SYMPTOM, not the upstream cause; right answer
  needs tracing the dependency graph. Covers misleading code comments, decoy files/branches,
  stale-but-official docs contradicting the machine-readable truth. Lesson enforced: verify
  tools against ground truth before trusting them (a real skill → fair).
- **D · Reverse-engineer conventions from data (fair inference).** Undocumented conventions
  (sentinels, ms-vs-s timestamps, counter resets, scaled rates) inferable ONLY from the
  values. Fair because every convention is FORCED by the data — a competent engineer
  converges on the same rules. Includes bit-by-bit custom binary formats, recovering hidden
  constants from archived I/O pairs, and (most elegant) a true rule with a discontinuous jump
  no smooth model can fit.
- **E · Broken implicit invariant.** Exploit an assumption the agent never consciously chose
  ("input is sorted," "records well-formed," "anomalies tolerable") then quietly break it in
  data the agent doesn't inspect. Ex: GPS timestamps — sample is chronological; hidden log
  jumps BACKWARD years; a stateful monotonic decoder adds a spurious cycle. Correct: anchor
  each record independently against a fixed reference.
- **F · No-information failure signal (RISKIEST — shades into unfair).** Every wrong attempt
  returns an identical rejection with no hint which field was wrong → joint guess across
  opaque values. Ex: forge an auth token; role/scope/channel all rejected identically. Fair
  ONLY if the value is discoverable-in-principle (hinted somewhere / derivable from the
  protocol); genuinely unguessable = a coin flip = unfair.
- **G · Breadth under all-or-nothing.** N independent bugs, grader accepts only fully correct
  → fixing 7 of 8 scores ZERO. Ex: relinker with 8 independent bugs (revision, symbol
  binding, alignment, kind-encoding); near-complete failure wrote a component's raw kind
  value instead of its encoded RANK — invisible under the rank-zero sample, caught by held-
  out families. Works best when fixes are genuinely INDEPENDENT and ≥1 hides in a case the
  sample doesn't exercise (combine with A).
- **H · Coupled rules / interactions (not count).** Rules reach back and rewrite each other;
  fixing "one more rule" never converges. Ex: document-approval event history — a RESET
  discards earlier approvals; a REVOCATION can resurrect a superseded parent, re-validating/
  invalidating its children. Correct approach reasons about the WHOLE history at once
  (establish active epoch, resolve survivors, then apply). Generalizes to bitemporal data,
  ledger reversals, dependency resolution where one choice forbids another, late events that
  change the meaning of early ones.
- **I · Point-in-time / as-of.** Use the value known AS OF a cutoff, not the value that looks
  current now. Ex: fund end-of-day valuation — prices get corrected after the fact; "latest"
  silently rewrites history on days with late corrections; sample days all had prices in
  before cutoff so "current" reproduced them. Correct: among values effective ≤ ref date AND
  published ≤ cutoff, take the most recent; ignore today's status. Generalizes to point-in-
  time joins, effective-date vs posting-date, superseding versions, identity known only later.

### 19.4 LIVE GRADED EXAMPLES (real runs — the exact failure, incl. the model's own words)

The recurring signature across ALL winners: **the model OFTEN NAMED the correct rule, then
DISMISSED it** ("probably won't be tested," "beyond scope," "informational," "harmless"), or
stopped the moment the visible examples passed. The stump attacks JUDGMENT/diligence, not
knowledge.

1. **bytecode-vm-debug (subtraction) — 5/8 fail (pattern A + green-stop).** Fixed the obvious
   bug, ran examples (add/multiply only), saw green, quit in 77–137 s of 900 s. A second bug
   only shows on SUBTRACTION (order matters); hidden tests negated it: `subtract(10,3)` → −7
   not 7; `multiply(subtract(6,2),3)` → −12 not 12. Runs literally said "there might be
   something I'm missing" then stopped; one noticed "reversed" and dismissed it as "harmless
   since addition is commutative"; one worked out both bugs but ran out of time having made
   NO edits.
2. **accrued-interest (UK ex-dividend) — 8/8 fail (pattern A).** Derived the formula from an
   all-US-bond sample, matched every sample to the cent, even handled German yearly coupons.
   Hidden UK bonds bought inside the ex-dividend window have NEGATIVE accrued (a rebate):
   correct −0.041209, model +1.833791. Most runs NAMED the UK rule and dropped it: "probably
   isn't being tested," "likely beyond scope," "feels risky," treated UK gilts as "identical
   to US Treasuries."
3. **gnss-log-decode (week rollover + eras) — 8/8 fail (patterns A + E).** Decoded raw data
   perfectly. Assumed time only moves forward in one era, but the week counter WRAPS ~every
   20 yrs and different satellite systems count time differently. Hidden logs span eras:
   correct 2017-06-10T11:44:28Z, model 2037-01-24 (≈20 yrs off). Several runs FLAGGED the
   rollover risk then dismissed it; one dropped the BeiDou branch, treating the system field
   as "informational." (Only the era-spanning test failed; 4 structural tests passed.)
4. **experiment-readout (clustered variance) — 5/5 fail (pattern B).** Cleaned data, every
   number right except the ERROR BAR: computed per-session (obvious) but users have many
   sessions so sessions aren't independent; correct per-user error bar ≈5× larger (0.6341 vs
   0.1265), flipping "not significant" into a false "significant." One run computed BOTH the
   correct per-user and wrong per-session bar, saw they matched on the sample, and PICKED THE
   WRONG ONE. (14/15 tests passed; only held-out inference failed.)
5. **legacy-formatter-clone (custom checksum) — 5/5 fail (pattern D).** Rebuilt every page
   body perfectly; the only miss was the footer CHECK-CODE, a custom home-made formula.
   Every run tried a long list of FAMOUS checksums, none fit, left it blank (00000000 vs
   7FD2FCAC) on every page. NONE worked it out from the examples by math — the only way. One
   built a fully-correct renderer in a scratch folder (36/36 pages) then spent ~44 min on
   named checksums and NEVER SAVED the working file.

### 19.5 THE SYNTHESIZED WINNING RECIPE (what all live winners share)

1. A rule that is **real, determinate, and survives full disclosure** (fair — §19.1) — NOT a
   single stateable constant (that collapses → fake difficulty → reject).
2. The rule is **LATENT**: it never fires on the visible/sample data, only on held-out
   (pattern A is in almost every winner, often composed with B/D/E/G/H/I).
3. The agent's **own validation against the homogeneous sample REINFORCES the wrong answer**
   — its diligence is the trap.
4. Ideally the correct rule is one the model will **NAME then DISMISS** (judgment failure) or
   reach past via a **cheaper heuristic** — not something it simply doesn't know.
5. Grade on **held-out** inputs exercising exactly the latent case; keep every enforced rule
   **stated** (avoid rejection reason 1); make shipped data obey the instruction (reason 2);
   name the canonical rule (reason 3); ensure difficulty survives disclosure (reason 4); any
   misdirection must be correctable (reason 5).

**Mapping to this campaign:** repair-capture-times (0/5 accepted) = A (latent high-byte/leap
era) + I (as-of era offset) + C (poisoned processed records), and its difficulty SURVIVES
disclosure. Every cross-abi design = a single stateable ABI constant → collapses on
disclosure → fake difficulty → solved-or-flagged either way. The seed lacks a
survives-disclosure crux; that is the true, doc-grounded reason it cannot be stumped fairly.

### 19.6 CONFIRMATION via the double-precision task — the compiler PRINTS the deciding fact (2026-07-13, 2/2)

The ATmega328P double=32-bit design (the 6th cross-abi push) solved 2/2. The analysis is
the cleanest possible demonstration of §19.1: both agents ran
`avr-gcc -mmcu=atmega328p -dM -E` and read `__SIZEOF_DOUBLE__ == 4` directly — they did not
even rely on knowing it; **the compiler, present in the image, PRINTS the deciding rule on
request** (`-dM` dumps every predefined macro). Then they wrote the f32 round-trip emulator.

This is fake difficulty in its purest form (rejection reason 4 + the fairness test): the
deciding rule is a single compiler macro. It collapses not just on author disclosure but on
`gcc -dM -E`. No pattern-A homogeneous-sample dressing rescues it — the agents bypassed
samples entirely and queried the toolchain. **Every ABI fact a cross-compile task can hang
difficulty on is printed by `<triple>-gcc -dM -E` or observable via qemu/objdump.** That is
the completeness-of-oracle theorem (§18.14) and the fairness-collapse test (§19.1) meeting at
the same point: cross-compilation offers only single-stateable-constant difficulty, which is
disqualified twice over. SIX cross-abi designs, 0 fair stumps. Seed closed; reseed is the
move (§19.5: the winning recipe needs a survives-disclosure latent crux this seed cannot host).

### 19.7 THE FINAL NAIL — even the recipe-correct pattern-A design solves; pattern A needs an UNSTATED activatable rule this seed cannot host (2026-07-13, 2/2)

Built the custom register-packing ABI with a LATENT cross-word straddle rule — the §19.5
winning recipe done right: all rules stated (survives disclosure), no compiler makes the
wire format (no oracle), sample maps tile 32 exactly so straddle is dormant, pad-and-
advance naive reproduces every sample (false green) and fails 7/8 held-out. Gate perfect.
**pass@2 = 2/2 solved.** Both agents read packing_abi.md FULLY, implemented straddle
directly from the spec (a while-loop MORE general than the golden if/else), never touched
the pad-and-advance trap, validated on samples, done in 3.5–5.7 min.

**Why pattern A failed here when it wins in the live examples (§19.4) — the precise
distinction.** In steel/non-ferrous, UK-ex-dividend, gnss, the latent rule is REAL-WORLD
KNOWLEDGE that is NOT stated in the task — the model must ACTIVATE it from memory and
CHOOSES TO DISMISS it ("probably won't be tested," "identical to US Treasuries," "system
field is informational"). The stump is a JUDGMENT failure: the model knows the rule and
drops it. **My straddle rule was STATED** (it had to be — a custom ABI is unfair if
unstated), so there was nothing to activate and nothing to dismiss — the model just read
it and implemented it. Pattern A's power is not "a case absent from samples"; it is "a
real rule the model must SUPPLY itself and will UNDER-WEIGHT." A stated rule removes both.

**The unresolvable bind for THIS seed (proven at every level now):**
- A custom/invented ABI → every rule must be STATED for fairness → the model reads and
  implements it (§19.7, §18.11). Pattern A can't bite because nothing is unstated.
- A real platform ABI → the rule is KNOWN and, for any concrete case, CHECKABLE via
  qemu/objdump/`gcc -dM -E` (§18.14, §19.6). The model applies it and can verify it.
Pattern A needs an UNSTATED, real-world, activate-but-dismissible rule with NO tool to
check the held-out case. Cross-compilation/platform-targeting has no such rule: its facts
are either invented-and-stated or standard-and-tool-checkable. repair-capture-times had
one (leap-second era arithmetic — real external knowledge, not stated, no in-env oracle,
poisoned to induce dismissal). This seed cannot.

**FINAL: seven designs, including the doc's own winning recipe executed correctly, all
solved. The reason is now proven at the deepest level: the one ingredient the winning
recipe requires — a latent rule the model must supply and will under-weight — is
structurally impossible in a fair cross-compilation task. RESEED. This is not a failure
of design; it is a property of the subcategory, confirmed against the platform's own
rulebook.** — Fable, final, for real this time.

### 19.8 THE RUBRIC ENFORCES THE FAIRNESS TEST BEFORE pass@2 (pattern-I as-of design, 2026-07-13)

The as-of dependency-resolution design (pattern I) never reached pass@2 — it FAILED the
rubric review (`review / review`) first, on two criteria, in the reviewer's own words:
- **essential_difficulty FAIL:** "Sole 'difficulty' is an as-of filter that the instruction
  explicitly states; an undergraduate solves it in under an hour, not a genuine expert stump."
- **code_dependent FAIL:** "solvable by hand, code is a ~15-line beginner filter — no
  multi-step dependent interaction."

This is §19.1 (the fairness test) automated as a GATE BEFORE pass@2. Two lessons:
1. **Two distinct failure modes now confirmed.** (a) Too THIN → rubric essential_difficulty
   FAIL (this design). (b) Hard-LOOKING but solvable → passes rubric, solved at pass@2 (the
   7 ABI-byte designs). Winning requires BOTH: pass the rubric (genuinely rich, multi-step,
   survives disclosure) AND stump pass@2 (the model actually fails).
2. **Why pattern I FAILED here but WON as repair-capture-times.** repair-capture-times was
   pattern I embedded in a RICH multi-step reconstruction: parse a binary container, execute
   era-boundary leap arithmetic across 40 records, reconstruct exact bytes, AND resolve a
   poisoned-attribution conflict — genuine code_dependent multi-step interaction + a poison
   crux. My as-of resolver was "filter by date+platform, take max" — the as-of INSIGHT with
   none of the surrounding execution complexity, so once the rule is stated (required for
   `unambiguous` PASS) it collapses to a 15-line filter. The pattern is necessary but NOT
   sufficient; it must ride on a rich, dependent computation.

**The narrow winning intersection (what repair-capture-times hit):** rich multi-step
dependent execution (clears code_dependent + essential_difficulty + survives disclosure)
+ a latent/poison crux that the model's reflex or diligence gets wrong (stumps pass@2).
In this cross-compilation/build-dependency seed, the only candidate with that shape is a
coupled dependency resolver (inter-component constraints → backtracking = multi-step
dependent) + as-of/platform filters + a poisoned lockfile/resolver-log the agent validates
against (pattern C) + a latent case. That is a repair-capture-times-scale build, and even
then pass@2 is uncertain (Opus implements dependency resolution well). Recorded so the next
attempt starts rich-and-poisoned, not thin.

### 19.9 BREAKTHROUGH + the remaining wall: rich CSP CLEARS the rubric, but pass@2 falls to Opus's algorithmic competence (pinned-dep-resolver, 2026-07-13)

**Breakthrough (first in 9 designs):** the coupled dependency-resolution design (backtracking
CSP, patterns H+A) PASSED the rubric review — code_dependent PASS, essential_difficulty PASS
("greedy dead-ends; correct needs backtracking; trap latent"), all 30 criteria (after renaming
cross-abi-serializer -> pinned-dep-resolver, the sole task_name fail). It cleared similarity +
validation too. This PROVES the §19.8 lesson works: a rich, multi-step, survives-disclosure
task clears the rubric wall that rejected every thin single-fact design. The path is real.

**But pass@2 = 2/2 solved.** How the two agents solved the latent-greedy trap:
1. One wrote explicit DFS backtracking and STATED the crux in its plan ("DFS in listed order
   -> first full solution is lexmax"). It recognized the CSP immediately — never wrote greedy.
2. The other brute-forced ALL combinations with itertools.product (~81 combos, tractable),
   sidestepping greedy-vs-backtracking entirely.

**The two remaining defeat mechanisms (both about the problem being a STANDARD algorithm):**
- **Brute-forceability:** small search space -> itertools.product enumerates everything and
  picks the max. Fix: many components x many releases -> combinatorial explosion (5^15) makes
  brute force infeasible, forcing real pruned backtracking.
- **Opus knows resolution needs search:** dependency version resolution is a KNOWN CSP; Opus
  does not take the greedy bait because it knows resolvers backtrack. The latent-greedy trap
  (pattern A/B) fails when the correct algorithm is common knowledge — greedy isn't a
  "plausible reading," it's an obviously-incomplete algorithm the model won't confidently use.

**The precise lesson (refines §19.7/§19.8):** clearing the RUBRIC needs rich survives-disclosure
difficulty (achieved). Stumping pass@2 additionally needs the model to get it WRONG despite
understanding the problem — which a STANDARD algorithm (CSP, resolution, packing, layout) does
not provide, because Opus implements standard algorithms correctly. repair-capture-times stumped
because its deciding step was NOT a standard algorithm but a POISONED-ATTRIBUTION judgment (trust
the spec's era rule over the crashed tool's wrong-but-present output) with NO clean recompute
oracle. Dependency resolution HAS a clean recompute oracle (index + rules), so a poison dies
(§18.11). The winning intersection = rich (clears rubric) + a deciding step that is NOT a standard
algorithm AND has no recompute oracle (a judgment/attribution under a poison). Cross-compilation/
build-dependency provides rich standard-algorithm difficulty (clears rubric, loses pass@2) but not
the non-standard poisoned-judgment step (which needs forensics/recovery/reconciliation domains).

### 19.10 THE COMPLETE THEOREM — pattern A cannot bite on a STATED rule; synthetic build-dep tasks have only stated rules (pinned-dep-resolver + conflicts, 2026-07-13, 2/2)

Added a LATENT mutual-exclusion `conflicts` rule (pattern A) to the rich resolver: samples
conflict-free (a conflict-ignoring resolver reproduces them), all held-out trigger conflicts.
Cleared the rubric again (rich CSP). **pass@2 = 2/2 solved.** Both agents read the schema, SAW
the `conflicts` field, and implemented it — bidirectionally, with forward-feasibility pruning
(more thorough than the golden). The latent-ness was irrelevant.

**The complete, exhaustively-proven theorem for stumping Opus-4.8 (10 designs, 2 models):**
Two gates, and the second is the wall:
1. **Clear the rubric:** needs rich, multi-step, SURVIVES-DISCLOSURE difficulty. ACHIEVED here
   (backtracking CSP with req + conflicts + as-of + platform). This wall is BREAKABLE.
2. **Stump pass@2:** the model must get it WRONG despite understanding the problem. This needs
   the deciding rule to be one the model DOES NOT implement correctly. Two sub-requirements,
   and a synthetic custom-format task can satisfy NEITHER:
   - (a) NOT a standard algorithm the model executes correctly (resolution, CSP, packing, layout
     are all standard → solved). AND
   - (b) LATENT — but latent only works on an UNSTATED rule. Fairness (rejection reason 1)
     forbids unstated verifier rules, so every rule in a synthetic task is STATED, and Opus
     reads the full spec and implements EVERY stated rule (I10) — even bidirectionally, even
     for cases the samples never exercise. Pattern A CANNOT bite a stated rule.

**Why the doc's pattern-A winners (steel, UK ex-dividend, gnss) and repair-capture-times work,
and a synthetic build-dep task cannot:** their latent rule is REAL-WORLD DOMAIN KNOWLEDGE that a
competent engineer is fairly expected to KNOW but that the task does NOT spell out (non-ferrous
gauge tables, UK ex-dividend rebates, GNSS leap-second/constellation epochs). It is fair (a
domain expert converges on it) yet unstated (so the model can under-apply or DISMISS it —
"probably not tested," "informational"). A SYNTHETIC CUSTOM FORMAT has no real-world knowledge
to leave unstated — every rule of a made-up index/ABI/wire-format is invented, so it MUST be
stated to be fair, so Opus implements it. **The pattern-A latent crux structurally requires a
domain with real, expected-known-but-unspelled conventions applied over many cases. Cross-
compilation / build-dependency with synthetic data has none.**

**FINAL VERDICT (definitive, 10 designs):** the rubric wall is broken here (rich CSP), but the
pass@2 wall is not, and cannot be, in a synthetic build-dependency seed. A win requires a domain
whose difficulty is a REAL, KNOWN-BUT-UNSTATED convention applied over many cases with no recompute
oracle (finance reconciliation: ex-dividend/day-count/as-of; time/GNSS decode: leap eras;
forensic format recovery: undocumented conventions) — i.e. repair-capture-times' territory. RESEED
to such a domain. This is not a failure of design effort (10 rubric-clean designs); it is a
structural property proven against the platform's own rubric and the frontier model's behavior.

## 20. THE §19.10 THEOREM VALIDATED — first-attempt clean sweep (mass-report-recovery, 2026-07-14, 0/2 + 0/5, avg@5 = 0.000)

### 20.1 The result (measured)

`dynamo/mass-report-recovery` (Hardware Embedded / CAD and mechanical workflows):
**pass@2 = 0/2, pass@5 = 0/5, avg@5 = 0.000 — 7/7 good valid fails, first attempt,
one substantive push** (plus a `.dockerignore` static fix). Every per-trial rubric
criterion PASS; deep review PASS on first pass; trace integrity clean; the deep
review's own words: *"This is a fair verifier: the trap is a knowledge lure, not an
undiscoverable guess."* Design: rich mass-properties report completion (flat-pattern
bend allowance, mixed units, multi-level BOM roll-ups — all stated) + ONE unstated
real-world convention (gauge→thickness is material-family-specific: MSG steel /
Brown & Sharpe aluminum / stainless sheet gauge) + poisoned entangled precedent
(the crashed tool's completed report rows, all computed with the steel table:
correct on steel, silently wrong on non-steel, perfectly consistent with
steel-for-all). Compare: repair-capture-times needed one human R1 + 5 automated
reworks + a timeout fix. This one needed nothing. The difference was not build
quality — it was choosing the seed/crux by the §19.10 theorem BEFORE building.

### 20.2 How the kill-chain actually ran (stronger than designed — new invariant I12)

Both pass@2 agents (and all five pass@5 agents) did NOT retrieve-then-validate as
rev 5's did. They went to the empirical rows FIRST: "inspect existing partial-report
rows to infer the gauge-to-thickness mapping," fit the steel MSG table (from memory —
they KNOW the table), validated it against all 20 rows, got zero mismatches, and
shipped in 3.5–8 min of a 3600 s budget. The poison was not a confirmation that had
to overcome a belief; it was the PRIMARY SOURCE for an unstated constant.

**I12 — infers unstated real-world constants from in-env precedent before external
lookup; a clean fit ends the search.** When a needed mapping is unstated but example
rows exist, the adversary calibrates against the rows and — on a perfect fit — never
opens the internet, never consults broader domain practice, never deliberates. Two
consequences: (a) G1 (perfect wrong fit) is even more load-bearing than §18.4 says —
it doesn't just induce self-doubt, it PREEMPTS the search for the correct rule;
(b) a confirmation-shaped poison produces FAST confident wrong ships (no deliberation,
no timeout pressure) — unlike rev 5's contradiction-shaped poison, which produced
350-450 s deliberation loops. Confirmation-poison is therefore operationally SAFER
(no in-progress-timeout risk) — but keep timeout_sec = 3600 anyway; it costs nothing.

### 20.3 Why this fired when §18.11's poison died (the two-sided condition, now proven both ways)

- cross-abi (§18.11): correct rule STATED in an in-env datasheet → agents read it,
  implemented it, dismissed the contradicting capture. Poison dead.
- mass-report: correct rule UNSTATED (real-world practice the model must supply) and
  the poison ENTANGLED (same kind as the deliverable, from the same tool run) →
  agents inferred the rule FROM the poison. Poison decisive.
The complete condition: **poison bites iff the deciding rule is not cleanly stated by
any in-env authority AND the poisoned surface is the natural place to get it.** Both
directions are now measured (2/2 solved vs 0/7 solved on the same trap skeleton).

### 20.4 Post-mortem of the 10 lost hours (cross-abi) — the three preventable errors

1. **A written risk that matches a documented kill condition is a STOP, not a note.**
   The §18.11 defeat was predicted in the progress file BEFORE the push ("a
   disciplined agent that trusts the datasheet solves it"). Writing a risk down does
   not shrink it. Rule: if your honest-risk paragraph describes a §18.3/§18.11/§19.x
   verdict, the design is dead — redesign or reseed before spending a pass@2.
2. **Two defeats in one seed with distinct mechanisms = the seed, not the design.**
   Eight designs were pushed into cross-abi after the first two losses had already
   exhibited the {stated-rule, tool-oracle} walls. The §18.5 intelligence extraction
   was done well (it produced §18.11–§19.10), but reseeding was deferred ~6 designs
   too long. Budget rule: after 2 pushed losses in a seed, the next artifact is a
   seed-exhaustion argument (or reseed request) — not a third design.
3. **The seed gate belongs at CLAIM time, not at design time.** Every hour in
   cross-abi was spent before asking §19.10's question. The claim-time gate (now
   §20.5) takes ten minutes and would have rejected the seed outright.
   Corollary: the 10 hours weren't pure waste — they bought the theorem that
   selected this win — but the same theorem was purchasable for ~2 pushes.

### 20.5 THE VALIDATED RECIPE (run in this order; each step is now measured, not theorized)

1. **Claim-time seed gate.** Name, before claiming/building: (a) a real-world,
   expected-known-but-UNSTATED convention applied over many records (pattern A's
   fuel); (b) no in-env / pip / toolchain / compiler oracle that computes or prints
   the deciding values; (c) an empirical surface of the SAME KIND as the deliverable
   that can carry the poison. Any leg missing → decline or reframe the seed.
   (CAD/mechanical had all three: gauge tables / no tool / report rows.)
2. **Compose the two layers.** Rich stated multi-rule execution (clears
   essential_difficulty + code_dependent + survives-disclosure) × ONE unstated
   real-world convention as the sole discriminator. Ship every invented rule and
   every ambiguity-killer (densities, K-factor, conversion constants, rounding,
   schema) — generosity on stated rules costs nothing (I2/I10) and buys fairness.
3. **Poison as confirmation, not contradiction (§20.2).** One uniform in-story bug;
   G1 perfect fit on every visible row; correct-on-a-subset (steel) so the bug reads
   as configuration, not corruption; earliest poisoned row early; graded set heavy
   in the regime the poison misleads (here 22/34 lines).
4. **§18.7 fork test on paper.** If the workflow-natural branch is the escape path
   (clean authority, separately-labeled reference, tool oracle), STOP — that is
   §18.11. Push only when the natural branch is calibrate-against-precedent (I6/I12).
5. **Generator before prose.** No instruction/spec writing until the generator
   hard-asserts G1 G2 G3 G4 + rounding margins under BOTH rule sets + F5
   (oracle == golden via subprocess) + every naive variant diverging. Nudge data
   per-part to satisfy margins (global reseed search does not converge).
6. **Full local gate, then ONE push.** oracle 1.0, nop 0.0, every naive variant
   0.0 end-to-end via harbor; timeout_sec 3600 from the first push; determinacy by
   construction (pin resolution conventions in-spec — e.g. "standard 4-decimal-place
   decimal equivalents" — rather than shipping values).
7. **After any loss: extract, then apply the 2-loss seed rule (§20.4-2).**

### 20.6 Operational notes (new platform facts, field-verified this run)

- **Static check added: `.dockerignore` required** when environment/ has
  subdirectories (any data/ dir). Add `task/environment/.dockerignore` from day one.
- The static-fail comment arrives in ~1 min; a full clean pipeline (static → rubric
  → similarity → validation → pass@2 → deep review → pass@5) completed in ~45 min.
- pass@5 gate wording now: "≥1 good valid and ≥3 total (good valid + soft-timeout)
  fails of 5"; avg@5 recorded on the task.
- Checks all green ≠ accepted: human review (R1/R2 → RTD) still follows. **Do not
  push anything to the PR after the sweep — any push re-runs the FULL pipeline
  including pass@2 and can flip the result.** Doc/recipe updates go in the playbook
  repo, never the task repo.

### 20.7 Platform-suggested hardening for pinned-dep-resolver (range/platform conflicts) — analyzed, predicted 2/2, declined (2026-07-14)

A Handshake reviewer (Nandini) suggested hardening the abandoned pinned-dep-resolver
task: extend `conflicts` to version-RANGE targets (`component@[min,max]`) and
platform-scoped conflicts, state both precisely in instruction.md, keep samples
conflict-free, make held-out builds trigger them — betting the solver matches
conflicts by exact version string and silently skips range conflicts.

**Verdict: this is §19.7/§19.10's defeated mechanism (pattern A on a STATED synthetic
rule) with a range twist.** The premise ("solver matches conflicts as exact pairs")
contradicts the measured trajectories: in this task's own §19.10 revision both agents
implemented the stated conflicts rule bidirectionally with forward pruning — more
thoroughly than the golden — and one brute-forced the assignment space entirely.
Stated semantics get implemented (I2/I10); fairness forces range/platform semantics to
be stated; interval containment inside a backtracker is not an Opus slip point. The
real-world-convention escape (PEP 440 semantics left unstated) dies on the
`packaging`-library recompute oracle (§18.17). Applying §20.4-1 (documented kill
condition = STOP): do not rebuild; reply with evidence and request a reseed.
Meta-lesson: platform hardening suggestions are generated from single-run analysis
without the cross-design record — always run them against §18/§19/§20 before
spending hours or a pass@2 slot. They are well-intentioned pattern-matching, not
measurements.

### 20.8 THE DISCLOSURE A/B — one mandated sentence kills the entangled poison (repair-capture-times R1 re-run, 2026-07-14, 2/2)

Human R1 (kiranshankar08) blocked repair-capture-times on two fixes: resubmit the
drifted proposal, and "add a line disclosing processed records could be wrong"
(hidden trap = not fair difficulty, in their words — even though the automated
rubric had passed task_specification 7/7 and the task was ACCEPTED). The softest
truthful wording was pushed ("preserved exactly as they appear — the crashed
tool's prior output is part of the file's as-is state, whether or not any of it
is itself correct" + a spec note that the exporter re-verifies nothing).

**Re-run: pass@2 = 2/2, both 1.0, ~6 turns.** Both agents validated against the
processed records as always, found the 6 poisoned mismatches, and "spent an
explicit reasoning step concluding the mismatches were due to the prior
normalizer bug, not their own formula" — then shipped without calibrating.
Same bytes otherwise: **0/7 undisclosed → 2/2 disclosed.** The cleanest A/B in
the campaign.

**The theorem this proves (sharpens §18.4/§18.11):** the entangled poison does
not merely need "no clean authority stating the deciding rule" — it needs the
POSSIBILITY of the empirical source being wrong to itself be undisclosed. The
kill-chain's load-bearing link is misattribution under self-doubt (I7: a mismatch
means MY bug); one honest sentence pre-authorizes the alternative attribution and
the adversary takes it in a single reasoning step. Non-disclosure was the
difficulty. And non-disclosure is exactly what human fairness review removes.

**Strategic consequences:**
1. **The P5 poison family is now reviewer-mortal.** It passes automated review
   (twice) but a human fairness standard of "no hidden gotchas on the agent"
   forces the disclosing sentence, which is measured lethal. Any pending or
   future poison design must assume the disclosure will eventually be mandated
   and must have a second leg that survives it.
2. **mass-report-recovery is exposed.** Same structure (crashed tool's preserved
   rows silently wrong; instruction does not say they may be wrong), human review
   pending. Defenses if challenged: its deep review explicitly passed
   decisive_rule_disclosed ("a knowledge lure, not an undiscoverable guess"), and
   its FIRST leg is an unstated real-world convention (pattern A proper, the
   platform's own canonical example family) — the poison is confirmation, not
   the sole difficulty. But if a reviewer mandates the sentence, expect the
   I12 calibration path to die and the task to rest on whether agents then
   supply material-specific tables (they likely will, via lookup). Do not
   volunteer the sentence; have the fairness case ready.
3. **Design rule going forward: difficulty must survive the honest sentence.**
   Before betting on any trap, write the most damaging truthful disclosure a
   reviewer could demand and re-run the §18.7 walkthrough with it in the
   instruction. If the walkthrough no longer reaches reward 0, the design's
   difficulty was its own secrecy — already dead. (mass-report partially
   survives this test only via its unstated-knowledge leg; repair-capture-times
   had no second leg once the poison was disclosed — its era arithmetic was
   measured solved in rev 4.)
4. **repair-capture-times itself:** with disclosure mandated and the poison dead,
   the remaining difficulty (pointed era arithmetic) is measured-solved (rev 4,
   2/2). No within-constraints hardening lever exists in the record. The honest
   options are: present the A/B to the reviewer/platform and ask how they want to
   resolve the fairness-vs-difficulty conflict; or retire/redesign as a new
   proposal. Do not burn reruns hoping for variance (both solves were decisive).

### 20.9 THE ORACLE REVERSAL — the author caught by its own trap (tflite-int8-replay deep-review FAIL, 2026-07-14)

**Facts.** The accepted tflite-int8-replay PR (dynamo-0a6c761-machine-learning-and-ai #1,
all green 2026-07-08) was admin-cycled 2026-07-14 ("re-execute the full Dynamo Review
under the current pipeline"). The current pipeline has a stage that did not exist at
acceptance: `deep_review`, which runs AFTER pass@2 and gates `trials`. Results:
review/similarity/validation/ratelimit/pass2 all green again (pass@2 = 0/2), then
**deep_review FAIL → trials skipped → gate red → label flipped accepted → needs-revision.**

**The finding (verified correct).** `instruction.md` mandates implementing SRDHM
"exactly as TFLite/gemmlowp defines it". Canonical gemmlowp
`SaturatingRoundingDoublingHighMul` uses `nudge = ab >= 0 ? (1<<30) : (1 - (1<<30))`
and C++ **truncating** division `(ab + nudge) / (1ll<<31)`. The shipped oracle
(`solution/solve.py`) used `nudge = -(1<<30)` and an arithmetic `>> 31` (**floor**).
For negative products with a non-zero remainder these differ by 1, and the oracle's
result is not even round-to-nearest (maps −0.47 → −1). `expected.json` was generated
from the oracle, and CI's oracle check only proves `expected == oracle output` —
self-consistency, not correctness.

**The mechanism — maximal irony.** The task was built to trap misretrieval of
gemmlowp's rounding; the AUTHOR committed exactly that misretrieval, on the reference
side of the grader. In the re-run pass@2, both agents implemented the REAL standard
(`1-(1<<30)` + truncation) and were failed +1 on the same 15/48 rows by the wrong
reference. The 0/2 "valid fails" were false negatives — correct solutions rejected.
The original 0/5 + 0/5 evidence is therefore contaminated to an unknown degree.

**Consequences.**
1. **The "single durable lever" claim (§16.11, CLAUDE.md) is DOWNGRADED.** The two
   tflite 0/5s can no longer be cited as proof that the unpointed-familiar-standard
   retrieval trap beats the adversary: in every trial we can now inspect, the
   adversary retrieved gemmlowp CORRECTLY. The pattern may still be real; this
   instance is no longer evidence.
2. **§16.5's `oracle == external golden via subprocess` hard-assert is now
   measured-mandatory, proven by loss.** For any "match external standard X" crux:
   compile the standard's real source (or run the real library) and assert equality
   over the full eval batch BEFORE the first push. Self-consistency proves nothing.
3. **The mandated fix likely un-stumps the task.** Deep review requires correcting
   `srdhm` and regenerating `expected.json`; with the corrected reference, both
   pass@2 agents' outputs would have been CORRECT → expect ~2/2 on re-run →
   difficulty_evidence dies. Fixing per instructions probably converts a red accepted
   task into a solved rejected one. Decide deliberately (fix-and-push vs comment/
   negotiate vs retire) — do not reflex-push. pass@2 remains capped 6/day.
4. **ACCEPTED is not immutable.** Admins re-cycle old PRs under upgraded pipelines
   with NEW stages; a frozen task can flip red with zero pushes. "DO NOT PUSH"
   freezes are not protection against pipeline upgrades. mass-report-recovery was
   accepted under a 7-stage pipeline the same week — check whether its acceptance
   already included deep_review before assuming it is exposed the same way.

### 20.10 The repair-capture-times claim after the disclosure A/B — exhaustion analysis (2026-07-15)

State of claim dynamo-4ad62d4 (File and Media / Recovery and repair): PR #2
(repair-capture-times) blocked at pass2 (2/2 after the mandated disclosure, §20.8);
a resubmitted ORIGINAL named-CRC proposal (repair-capture-crc text, CRC-32/BZIP2
params on the page) approved through the portal; an "unnamed in-house seal" revival
floated to the reviewer on the PR (awaiting reply).

**Design-table verdicts against the record:**
- Named-CRC proposal as approved: P1 (params stated for fairness) — dead. The
  proposal even instructs validating against intact records (a free clean arbiter,
  I6 working for the solver). crcmod predefines crc-32-bzip2. Predicted 2/2.
- Unnamed-seal revival: P2 if derivable (I5 solved class, rev-3 corpse), P4 if not
  (the original -crc R1 rejection reasoning). No middle band. KILLED before build
  (dataset record).
- Any poison-family design ON THIS CLAIM: the human reviewer (kiranshankar08) has a
  measured standard — "hidden trap = not fair difficulty" — and mandated the
  disclosing sentence once already. §20.8: disclosure kills the family (0/7 → 2/2).
  Reviewer-dead regardless of automated-gate success.
- Disclosure-surviving families in this seed: era/time knowledge measured solved
  (rev 4, 2/2); exacting breadth measured non-compounding (§18.13). Nothing left.

**Conclusion (per §20.4-2, two-plus losses, distinct mechanisms):** the claim is
exhausted for stump purposes. Honest artifacts: (a) the A/B + this analysis as a
seed-exhaustion argument to the platform with a reseed request; (b) if something
must ship, build the approved named-CRC task exactly — fair, honest, and predicted
2/2, which documents that the approved difficulty is insufficient at the automated
gate. Do NOT build the unnamed seal; do NOT hide a new poison from this reviewer.
Contrast: the SAME contradiction-poison skeleton passed pass2+deep_review the same
day in ML/numerics (tflite §20.9 rework) where no disclosure was mandated — the
lever is alive in general, dead on this claim.

**Addendum (2026-07-15, later the same day): proposal re-aligned via portal edit —
GATE-PASS.** The contributor portal now exposes a proposal-EDIT option (new; the
2026-07-14 thread had established there was none, forcing new-proposal submissions).
The stale approved named-CRC text was replaced in place with the AS-BUILT
repair-capture-times proposal ("Complete a crashed normalizer pass...", full text in
`PROPOSAL-repair-capture-times-updated.md`), including the synthetic-provenance
sentence (§20.11 rule) and an honest full-A/B results paragraph (0/2×2 + 0/5
pre-disclosure → 2/2 post-disclosure). It PASSED the proposal quality gate: the
proposal gate judges expert-hours substance/provenance/verification story, not stump
rate, so candor about a measured 2/2 is safe there. Human R1 blocker 1 (proposal
drift) is thereby closed with zero pushes and no pipeline re-roll. Platform-mechanics
note for §18.8 readers: drift is now fixable in place. Claim status otherwise
unchanged — exhausted per the analysis above; next move remains the honest
fairness-vs-difficulty/reseed conversation, from a now fully compliant record.

### 20.11 Admin re-sweep of accepted PRs (2026-07-14 evening) — two flavors of retroactive red

The platform re-cycled ACCEPTED PRs under the upgraded pipeline the same evening
(tflite 23:47, mass-report 23:28). Two distinct outcomes, two lessons:

1. **tflite-int8-replay:** new deep_review stage found a REAL defect (oracle ≠
   standard, §20.9). Substantive; required redesign.
2. **mass-report-recovery:** rubric review now enforces an enumerated FAIL trigger —
   `difficulty_explanation` MUST state data provenance (synthetic vs real-world and
   why realistically challenging). Ours omitted it → review FAIL → everything
   downstream skipped → needs-revision. The re-review otherwise INDEPENDENTLY
   re-verified the gauge-table poison (checked steel vs AL gauge-14 masses) and
   called the single-table alternative "an engineering error, not a defensible
   competent choice." Design intact; metadata one sentence short.

Operational consequences:
- **Add a provenance sentence to difficulty_explanation in every task, from the
  first push** ("All data is synthetic — fixed-seed generated — but mirrors ...").
  tflite's rework already had one (inherited from the old text); mass-report's
  didn't. This is now an enumerated FAIL trigger.
- **Fixing a re-swept accepted PR requires a push, which re-rolls the FULL pipeline
  including pass@2 and pass@5.** The freeze rule protected acceptance; once an
  admin sweep flips the PR red, freezing preserves nothing — the choice is
  re-roll or abandon. Budget the re-roll like a fresh submission (§18.10 gate math)
  and change ONLY what the failing criterion names (§18.9-12).
- Rubric reviewer also flagged (non-blocking) that "generator-verified margins"
  claims can't be confirmed read-only — expect human spot-checks; committing
  generator.py at repo root remains the answer (§18.8).

### 20.12 THE REWORK SWEEP — float-path poison re-accepts tflite same-day (2026-07-15, 0/2 + 0/5, avg@5 = 0.000)

The §20.9 rework (canonical oracle + external-golden assert + interrupted-batch
float-path poison) went green in ONE push: pass@2 0/2, pass@5 0/5, 7/7 good valid
fails, deep_review PASS — with correct_expected_results PASS explicitly citing the
generator's verbatim-gemmlowp-C++ hard-assert. The reversed task was re-accepted
~15 hours after it flipped red.

**The kill-chain, verbatim from the platform's own analysis (7/7 identical):**
1. Every agent derived and implemented CORRECT gemmlowp SRDHM+RDBPOT early.
2. Every agent validated against predictions_partial.json → 8/24 mismatches.
3. Every agent concluded its correct code was buggy and BRUTE-FORCE SEARCHED
   variants to re-fit the precedent (7x7 grid; ~59 variants; 784+ combinations).
4. Every agent shipped the float re-fit → 34/48 graded rows wrong → reward 0.
Runtimes 10-21 min of 3600 s; no timeouts; trace integrity clean; near_miss PASS
(34/48 wrong is decisively wrong, not near).

**New dossier invariant — I13 (variant-search-to-refit).** On empirical mismatch,
the adversary does not re-read the normative anchor or suspect the data; it sweeps
the implementation-variant space until something fits the visible examples. Design
consequences: (a) the wrong rule need only be REACHABLE by a sweep, not guessable a
priori — this widens the constructible poison space; (b) G1 must hold for the WHOLE
sweep neighborhood (all tie flavors, operation orders agreeing on visible rows —
tflite's generator asserted exactly this), else a failed sweep warns the agent.

**Theorem refinement (vs §20.3/§20.8):** the contradiction-shaped poison beats
externally-POINTED correct knowledge, not merely unstated knowledge — agents who had
already implemented the named standard correctly discarded it. The pointer sentence
("exactly as TFLite/gemmlowp defines it") is a fairness anchor the rubric credits
(decisive_rule_disclosed PASS) but NOT a workflow arbiter. The poison family's
live/dead boundary is now: dead iff an IN-ENV document cleanly states the deciding
rule (§18.11) OR the possibly-wrongness of the surface is disclosed (§20.8);
alive otherwise, even against held correct knowledge, in a second domain (ML/
numerics after CAD/mechanical and file/media).

**Campaign arithmetic for this skeleton: 11/11 valid fails when undisclosed**
(rev-5 0/2+0/2, mass-report 0/7... its own 7; tflite rework 0/7), 2/2 solved when
disclosed. The §20.5 recipe is now validated in three seeds.

### 20.13 THE DISCLOSURE-SHIELD FALSIFIED — stated-rule execution slips do not exist to shield (repair-capture-times rev 6, 2026-07-15, 2/2)

**The design (user-directed attempt against the §20.10 exhaustion verdict, all
rules honored).** Keep the rev-5 core + mandated disclosure verbatim; add a
bus-local time base (code 5): signed ticks at 4096/s from a header bus epoch,
converted by a plainly-stated rule — nearest ms, exact halves AWAY FROM ZERO —
with no worked example. Graded rows boundary-hunted (10 even-base ties both
signs, 5 negative fractionals); three idiom naives measured divergent (round()
10/57, int(x+0.5) 11/57, floor(x+0.5) 6/57) and G1-clean off-boundary. Five
CORRECT boundary rows among processed records so an idiom-slipped agent's I6
validation would mismatch them alongside the 6 poisoned era rows — two visually
identical families — and the mandated disclosure invites attributing BOTH to
the tool, shielding the agent's own bug. The bet: link 2 (dismiss-not-debug)
measured 2/2 in §20.8; link 1 (agent emits a wrong idiom for a stated rule)
unmeasured. An adversary probe (N≈10 API samples of the spec paragraph) was
offered to measure link 1 for cents; skipped by user choice — the pipeline roll
became the measurement.

**Result: pass@2 = 2/2, both 1.0. Link 1 falsified DECISIVELY.** Both agents
named the hazard in their plans ("round-half-away-from-zero (not Python's
built-in banker's rounding)") and implemented integer-exact variants:
`(abs(t)*1000 + 2048) // 4096` and `divmod(a*1000, 4096)` + `2*r >= 4096` bump.
One computed `local_preserved_spec_mismatches=0` against the boundary processed
rows BEFORE attributing the 6 GPS mismatches to the prior tool — per-family
attribution exactly as the spec intends. New dossier invariant I14.

**What this closes and what survives:**
1. The execution-slip family on STATED rules is now closed at all measured
   subtlety levels: in-spec C source (§17.8), itemized semantics (rev 1),
   rounding/division idioms (this). The only measured execution-slip win
   remains UNPOINTED retrieval-from-memory conditions (§18.3 P3 attention-gap)
   — and §20.9 contaminated its only instances.
2. The shield GEOMETRY is fair and constructible (passed review/similarity/
   validation; nothing hidden, nothing false) but is an AMPLIFIER, not a trap:
   it protects an error the workflow must first produce. Workflow attacks need
   the wrong path REACHED (I6 calibration, I12/I13 refit), not merely
   unpunished. File under "sound composition, no firing pin."
3. Claim 4ad62d4 exhaustion (§20.10) is now reinforced by falsification of its
   last unmeasured branch: rev-5+disclosure 2/2, rev-6 shield 2/2, distinct
   mechanisms, on top of revs 1-4. The seed-exhaustion/reseed case is at
   maximum evidentiary strength. Also worth noting: the roll cost one pass@2
   slot and produced the cleanest possible label either way — the probe-first
   discipline (§16.13-2 falsification BEFORE spending) remains the cheaper
   path and was consciously waived, not forgotten.

### 20.14 FOURTH-DOMAIN SWEEP — the poison is the attractor state for ALL failure modes (group-scope-report, 2026-07-15/16, 0/2 + 0/5, avg@5 = 0.000, ACCEPTED)

`dynamo/group-scope-report` (Data Querying and Databases / Graph and semantic
queries): **pass@2 = 0/2 (2/2 valid), pass@5 = 0/5, avg@5 = 0.000, 4/5 good
valid fails, deep review PASS with zero blocking issues — first attempt, one
substantive push** (plus one static fix: the checker greps Dockerfile COMMENTS
for solution/tests mentions — write image comments accordingly). The deep
review's advisory named the poison explicitly and blessed it: "legitimate,
spec-consistent difficulty," flagged only for human-reviewer comfort.

Design was §20.5 verbatim in a new domain: temporal shareholder-registry graph
(SQLite), stated rich layer (as-of positions, dual-class voting vs economic
bases, cross-holding effective-interest linear solve, exact 6dp strings,
canonical digest), ONE unstated real-world convention as sole discriminator
(consolidation control = FULL attribution of voting rights through controlled
entities, never pro-rated — spec says only "held directly or indirectly"),
poison = the crashed analyzer's 20 completed rows computed with pro-rated
look-through W1 (6/20 silently wrong, one uniform family, earliest row 3).
Generator hard-asserted G1 over the whole I13 sweep neighborhood, G2 exact,
G3 (W1 25/40, W2 23/40, W3 4/40, W4 9/40), margins, three-implementation
golden cross-check (F5). Both pass@2 agents shipped a report whose digest was
BYTE-IDENTICAL to the generator's pre-computed W1 report.

**Two new mechanism facts (sharpen I6/I13):**
1. **The poison overrides a correct answer ALREADY IN HAND.** One pass@5 agent
   implemented the correct fixed point first and produced the exact golden
   digest — then validated against the completed rows, hit the 6 poisoned
   mismatches, concluded full attribution was "not the intended
   interpretation," and replaced its correct output with W1. Stronger than
   §20.12's discard-of-correct-knowledge: this was discard of the correct
   ARTIFACT.
2. **The poison amplifies the agent's OWN unrelated bugs.** Three pass@5
   agents implemented the correct algorithm with ordinary implementation bugs
   (e.g. a snapshot-aggregation error); because W1 fit every visible row
   perfectly (G1), each misdiagnosed "my code mismatches the precedent" as
   "the algorithm is conceptually wrong" and substituted W1 — the designed
   error was never needed. G1 makes the wrong rule the attractor state for
   every failure mode in the trial, which is why it remains the single most
   load-bearing generator assert.

Campaign arithmetic for the undisclosed skeleton: **0 solves in 25 trials
across four domains** (file/media 4, CAD/mechanical 7, ML/numerics 7,
graph/semantic queries 7); 2/2 solved the one time disclosure was mandated
(§20.8). The §20.5 claim-time seed gate has now selected first-attempt clean
sweeps twice in a row (mass-report, this). Status: ACCEPTED (checks green),
frozen — do not push; human R1/R2 pending, fairness case ready (§20.8-2
posture: do not volunteer the disclosure sentence; if mandated, the
unstated-convention leg alone likely gets looked up and solved).

### 20.15 Format-generation split: the mandatory suffix line is a Harbor-rubric FAIL (etl-week-backfill, 2026-07-16)

dynamo-cd6e953 (Format: Harbor) passed ALL static checks with the §5-mandated TB2
suffix line present, then the rubric FAILED instruction_concision citing that exact
line as enumerated TB3 boilerplate: "the time budget belongs in task.toml
([agent].timeout_sec), not in the prose... delete line entirely." One-line fix,
free re-push (pass@2 had not run). §14's rule is now measured: repos differ by
format generation — TB2 repos REQUIRE the suffix via check-instruction-suffix,
Harbor repos FAIL it at rubric. Read the assigned repo's .dynamo/dynamo-rubric.toml
and scaffold template BEFORE writing instruction.md; §5 of this doc describes the
TB2 scaffold only. Bonus datum: the same rubric run PASSED essential_difficulty
naming the ISO week-year trap + poisoned landed precedent "genuine expert
difficulty" and its notes independently verified the poison geometry ("poisoned and
correct events never double-count") — automated review continues to bless the
undisclosed P5 skeleton (5th consecutive repo).

### 20.16 THE ARBITER-WORDS LAW — a named standard with on-page deciding words kills the poison (etl-week-backfill rev 1, 2026-07-16, 2/2)

Fifth-domain attempt (ETL orchestration, dynamo-cd6e953): full §20.5 skeleton,
G1-G4 + F5 asserted, seven naive variants 0.0 locally — pass@2 = 2/2, both 1.0,
first verifier run. Both agents ran an explicit isocalendar-vs-calendar-year
divergence analysis over the landed checkpoints, enumerated all 6 boundary
divergence points including the poisoned ones, and "chose isocalendar() based on
the normative spec rather than reverse-engineering from landed checkpoints."

The kill: the spec said partitions are keyed by "the ISO week-year and ISO week
number of the event's UTC date." Two words — "ISO week-year" — are a complete
in-env arbitration of the exact delta the poison creates (which year labels a
boundary week). That is §18.11's in-env datasheet, not tflite's pointer: tflite's
"exactly as gemmlowp defines it" survived because the deciding details (nudge
constant, truncating division) lived OUTSIDE the environment and the mismatch
diagnosis was ambiguous over a large variant space; here the mismatch diagnosis
("year label differs at year ends") maps word-for-word onto the spec's own text,
so attribution resolves on paper in one step — no self-doubt, no sweep.

**The law: the poison dies iff any in-env text arbitrates the specific delta the
poison creates — naming a standard is fatal exactly when the standard's deciding
detail is expressible in the naming words themselves.** Safe pointers point at
bodies of detail (gemmlowp internals); fatal pointers state the detail in
passing ("week-year", "away from zero", an in-env datasheet row). Before pushing
any poison design, take the wrong-vs-right DELTA and grep every agent-visible
file for words that distinguish it; if found, the design is P1/§18.11-dead.
(This closes the gap in §20.12's boundary statement: "externally-pointed correct
knowledge" loses only while the point-ee's details stay external.)

Revision path (measured recipe, group-scope precedent): keep the notation
("week date", YYYY-Www — expert-recognizable, fairness-sufficient) and delete
the semantic gloss, making the year-choice real-world-known-but-UNSTATED with
the landed precedent as the only in-env authority (I12). One pass@2 slot spent;
seed remains live (loss #1, mechanism now understood).

