---
name: log-outcome
description: Log a Dynamo task outcome (pass@ result, rubric verdict, review reply, design-table kill) into the training dataset and playbook. Use IMMEDIATELY whenever a new outcome is learned — a pass@2/pass@5 comment, a rubric PASS/FAIL, a human review verdict, or a design killed at the design table.
---

# Log a Dynamo outcome

Every outcome is a labeled training example measured against the frontier model —
the campaign's most valuable asset. Log it the moment it is known.

## Steps

1. **Gather the facts** (from the current conversation, or `gh pr view <n> --json comments`
   on the task repo): design description (as proposed, no outcome leakage), seed,
   measured outcome (numbers: pass@2 x/2, pass@5 x/5, avg@5, rubric criteria), the
   MECHANISM from the platform's trajectory analysis (what the agents actually did,
   step by step), and the transferable lesson.

2. **Append a `DesignRecord`** to `~/Work/dynamo-log-report-task/training-data/build_dataset.py`
   (RECORDS list, keep the existing style: proposal fresh-voice, mechanism grounded in
   observed behavior, lesson transferable). If the outcome taught a NEW rule not already
   in PRINCIPLES, add a `Principle` too — check for duplicates first.

3. **Regenerate + validate:**
   ```bash
   cd ~/Work/dynamo-log-report-task/training-data && python3 build_dataset.py
   python3 -c "import json; [json.loads(l) for l in open('all.jsonl')]"
   ```

4. **Update the playbook** if the outcome is novel: new §20.x subsection in
   `DYNAMO-REFERENCE.md` (mechanism + verdict), new dossier invariant if a new
   behavior was observed, PROGRESS-<task>.md status line, memory MEMORY.md flag.

5. **Commit** in `~/Work/dynamo-log-report-task` as the user (no AI trailers):
   `git add -A && git commit -m "Log outcome: <task> <result>"`.

## Rules

- Never log an outcome twice — grep RECORDS for the task name first.
- Record LOSSES and kills with the same care as wins; they are the rarer labels.
- If the outcome is a pass@ LOSS: extract trajectory intelligence into the record's
  mechanism field BEFORE any redesign discussion (§18.5 step 1), and check the
  2-loss seed rule (§20.4-2).
- Do NOT push anything to task PRs from this skill; it only touches the playbook repo.
