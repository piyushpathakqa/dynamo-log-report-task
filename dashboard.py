#!/usr/bin/env python3
"""Dynamo campaign dashboard — collects live PR/check status across all claim
repos via `gh` and renders a self-contained dashboard.html snapshot.

Usage:  python3 dashboard.py           # writes dashboard.html next to this file
"""
import html
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ORG = "handshake-project-dynamo"
REPOS = [  # (repo, task display name, campaign note)
    ("dynamo-b2f7712-debugging-and-repair", "thread-gauge-codegen",
     "8th-domain build win — FROZEN, do not push; human R1/R2 pending"),
    ("dynamo-e0ab8e2-data-querying-and-databases", "group-scope-report",
     "4th-domain win; AVA re-sweep flipped accepted→needs-revision; re-rolled 07-21"),
    ("dynamo-cd6e953-debugging-and-repair", "etl-week-backfill",
     "6th-domain win; AVA re-sweep flipped accepted→needs-revision; re-rolled 07-21"),
    ("dynamo-7ad3d51-regulated-knowledge-work-and-business-operations", "docket-deadline-backfill",
     "rev 2 (true 6(d) + backward-continuation poison); re-rolled 07-21"),
    ("dynamo-0a6c761-machine-learning-and-ai", "tflite-int8-replay",
     "reworked + re-accepted 07-15 — FROZEN, do not push"),
    ("dynamo-48e280f-hardware-embedded-and-low-level-systems", "mass-report-recovery",
     "first §20.5 sweep — do not push without sign-off"),
    ("dynamo-4ad62d4-file-and-media-operations", "repair-capture-times / adpcm",
     "claim EXHAUSTED (§20.10) — needs-revision is a content fail; no re-trigger"),
]

# CI job name -> (display label, order)
STAGES = [
    ("review / review", "rubric"),
    ("review / similarity", "similar"),
    ("review / validation", "validate"),
    ("review / pass2", "pass@2"),
    ("review / deep_review", "deep rev"),
    ("review / adversarial_review", "cheat"),
    ("review / ava_review", "AVA"),
    ("review / gate", "gate"),
    ("review / trials", "pass@5"),
]


def gh(*args):
    r = subprocess.run(["gh", *args], capture_output=True, text=True)
    return r.stdout


def collect():
    rows = []
    for repo, task, note in REPOS:
        prs = gh("pr", "list", "-R", f"{ORG}/{repo}", "--state", "all",
                 "--json", "number,title,state,labels,updatedAt,url,headRefOid")
        try:
            prs = json.loads(prs or "[]")
        except json.JSONDecodeError:
            continue
        for pr in prs:
            checks = {}
            out = gh("pr", "checks", str(pr["number"]), "-R", f"{ORG}/{repo}")
            for line in out.splitlines():
                f = line.split("\t")
                if len(f) >= 3:
                    checks[f[0]] = {"state": f[1], "dur": f[2]}
            rows.append({
                "repo": repo, "task": task, "note": note,
                "pr": pr["number"], "url": pr["url"], "state": pr["state"],
                "labels": [l["name"] for l in pr["labels"]],
                "updated": pr["updatedAt"], "head": pr["headRefOid"][:7],
                "checks": checks,
            })
    return rows


def classify(row):
    """(status key, human line). Keys: accepted running blocked content closed idle"""
    c = row["checks"]
    if row["state"] == "CLOSED":
        return "closed", "closed / superseded"
    if any(v["state"] == "pending" for v in c.values()):
        cur = [lbl for job, lbl in STAGES
               if c.get(job, {}).get("state") == "pending"]
        return "running", f"pipeline running — at {', '.join(cur) or 'startup'}"
    if "accepted" in row["labels"]:
        return "accepted", "ACCEPTED — frozen, human R1/R2 pending"
    ava = c.get("review / ava_review", {})
    p2 = c.get("review / pass2", {})
    if ava.get("state") == "fail" and _secs(ava.get("dur")) < 60:
        return "blocked", "infra-blocked: AVA died in seconds (missing secret) — re-trigger"
    if p2.get("state") == "fail":
        return "content", "pass@2 failed (task solved / too easy) — content, not infra"
    if any(v["state"] == "fail" for v in c.values()):
        bad = [j.split(" / ")[-1] for j, v in c.items() if v["state"] == "fail"]
        return "content", f"failed: {', '.join(bad)}"
    if not c:
        return "idle", "no pipeline runs"
    return "content", "needs revision"


def _secs(dur):
    if not dur:
        return 0
    t = 0
    for part in str(dur).split():
        for suf, mul in (("h", 3600), ("m", 60), ("s", 1)):
            if part.endswith(suf) and part[:-1].isdigit():
                t += int(part[:-1]) * mul
    return t


ORDER = {"running": 0, "blocked": 1, "content": 2, "idle": 3, "accepted": 4, "closed": 5}
STATUS_LABEL = {"running": "RUNNING", "blocked": "INFRA-BLOCKED", "content": "NEEDS REVISION",
                "idle": "IDLE", "accepted": "ACCEPTED", "closed": "CLOSED"}


def render(rows, ts):
    for r in rows:
        r["status"], r["line"] = classify(r)
    rows.sort(key=lambda r: (ORDER[r["status"]], r["task"]))
    counts = {k: sum(1 for r in rows if r["status"] == k) for k in ORDER}

    cards = []
    for r in rows:
        chips = []
        for job, lbl in STAGES:
            st = r["checks"].get(job, {}).get("state", "none")
            dur = r["checks"].get(job, {}).get("dur", "")
            chips.append(
                f'<span class="chip {html.escape(st)}" title="{html.escape(job)} — '
                f'{html.escape(st)} {html.escape(dur)}">{html.escape(lbl)}</span>')
        labels = "".join(f'<span class="lab {html.escape(l)}">{html.escape(l)}</span>'
                         for l in r["labels"]) or '<span class="lab none">no label</span>'
        cards.append(f'''
  <article class="row st-{r["status"]}">
    <div class="head">
      <span class="status">{STATUS_LABEL[r["status"]]}</span>
      <a class="task" href="{html.escape(r["url"])}">{html.escape(r["task"])}</a>
      <span class="meta">PR #{r["pr"]} · <code>{r["head"]}</code> · {html.escape(r["repo"].split("-")[1])}</span>
      {labels}
    </div>
    <div class="rail">{"".join(chips)}</div>
    <p class="line">{html.escape(r["line"])} <span class="note">· {html.escape(r["note"])}</span></p>
  </article>''')

    summary = "".join(
        f'<div class="stat st-{k}"><span class="n">{counts[k]}</span>{STATUS_LABEL[k].lower()}</div>'
        for k in ("running", "blocked", "content", "accepted") )

    return f'''<title>Dynamo campaign board</title>
<style>
:root {{
  --bg:#F4F5F3; --panel:#FFFFFF; --ink:#20262B; --mut:#68737B; --edge:#DDE1DC;
  --accent:#B07F24; --pass:#3E8460; --fail:#C4554D; --run:#4A7FAA; --skip:#9AA3A0;
}}
@media (prefers-color-scheme: dark) {{ :root {{
  --bg:#111417; --panel:#191E22; --ink:#E4E9E6; --mut:#8D989C; --edge:#2A3237;
  --accent:#D9A441; --pass:#57A97C; --fail:#D2685F; --run:#6E9FC7; --skip:#5C6669;
}} }}
:root[data-theme="light"] {{
  --bg:#F4F5F3; --panel:#FFFFFF; --ink:#20262B; --mut:#68737B; --edge:#DDE1DC;
  --accent:#B07F24; --pass:#3E8460; --fail:#C4554D; --run:#4A7FAA; --skip:#9AA3A0;
}}
:root[data-theme="dark"] {{
  --bg:#111417; --panel:#191E22; --ink:#E4E9E6; --mut:#8D989C; --edge:#2A3237;
  --accent:#D9A441; --pass:#57A97C; --fail:#D2685F; --run:#6E9FC7; --skip:#5C6669;
}}
* {{ box-sizing:border-box }}
body {{ background:var(--bg); color:var(--ink); margin:0; padding:28px 20px 60px;
  font:15px/1.5 "Segoe UI Variable","Avenir Next","Helvetica Neue",system-ui,sans-serif; }}
main {{ max-width:880px; margin:0 auto; }}
h1 {{ font-size:19px; letter-spacing:.01em; margin:0; }}
h1 b {{ color:var(--accent); font-weight:700 }}
.gen {{ color:var(--mut); font-size:12.5px; font-family:ui-monospace,SFMono-Regular,Menlo,monospace; }}
header {{ display:flex; justify-content:space-between; align-items:baseline; gap:16px;
  border-bottom:2px solid var(--accent); padding-bottom:12px; margin-bottom:16px; flex-wrap:wrap }}
.stats {{ display:flex; gap:10px; margin:0 0 22px; flex-wrap:wrap }}
.stat {{ background:var(--panel); border:1px solid var(--edge); border-radius:6px;
  padding:8px 14px; font-size:12px; color:var(--mut); letter-spacing:.04em; }}
.stat .n {{ display:block; font:600 22px/1.1 ui-monospace,Menlo,monospace; color:var(--ink);
  font-variant-numeric:tabular-nums }}
.stat.st-running .n {{ color:var(--run) }} .stat.st-blocked .n {{ color:var(--fail) }}
.stat.st-accepted .n {{ color:var(--pass) }} .stat.st-content .n {{ color:var(--accent) }}
.row {{ background:var(--panel); border:1px solid var(--edge); border-left:4px solid var(--edge);
  border-radius:6px; padding:13px 16px 11px; margin-bottom:12px; }}
.row.st-running {{ border-left-color:var(--run) }}
.row.st-blocked {{ border-left-color:var(--fail) }}
.row.st-content {{ border-left-color:var(--accent) }}
.row.st-accepted {{ border-left-color:var(--pass) }}
.head {{ display:flex; align-items:baseline; gap:10px; flex-wrap:wrap }}
.status {{ font:600 10.5px/1 ui-monospace,Menlo,monospace; letter-spacing:.08em; color:var(--mut) }}
.st-running .status {{ color:var(--run) }} .st-blocked .status {{ color:var(--fail) }}
.st-accepted .status {{ color:var(--pass) }} .st-content .status {{ color:var(--accent) }}
.task {{ font-weight:650; color:var(--ink); text-decoration:none; font-size:15.5px }}
.task:hover, .task:focus-visible {{ color:var(--accent); outline:none; text-decoration:underline }}
.meta {{ color:var(--mut); font-size:12px; font-family:ui-monospace,Menlo,monospace }}
.meta code {{ background:transparent }}
.lab {{ font-size:10.5px; padding:2px 8px; border-radius:99px; border:1px solid var(--edge);
  color:var(--mut); letter-spacing:.03em }}
.lab.accepted {{ color:var(--pass); border-color:var(--pass) }}
.lab.needs-revision {{ color:var(--fail); border-color:var(--fail) }}
.rail {{ display:flex; gap:4px; margin:10px 0 6px; flex-wrap:wrap }}
.chip {{ font:11px/1 ui-monospace,Menlo,monospace; padding:5px 8px; border-radius:4px;
  border:1px solid var(--edge); color:var(--mut); background:transparent }}
.chip.pass {{ color:var(--pass); border-color:color-mix(in srgb,var(--pass) 45%,transparent) }}
.chip.fail {{ color:#fff; background:var(--fail); border-color:var(--fail) }}
.chip.pending {{ color:var(--run); border-color:var(--run); animation:pulse 1.6s ease-in-out infinite }}
.chip.skipping, .chip.none {{ color:var(--skip); border-style:dashed }}
@keyframes pulse {{ 50% {{ opacity:.45 }} }}
@media (prefers-reduced-motion: reduce) {{ .chip.pending {{ animation:none }} }}
.line {{ margin:4px 0 0; font-size:13px; color:var(--ink) }}
.note {{ color:var(--mut) }}
footer {{ color:var(--mut); font-size:12px; margin-top:26px }}
</style>
<main>
<header><h1><b>Dynamo</b> campaign board</h1><span class="gen">snapshot {ts}</span></header>
<div class="stats">{summary}</div>
{"".join(cards)}
<footer>Snapshot generated by <code>dashboard.py</code> — rerun it (and republish) to refresh.
Chips follow CI order; dashed = not run. Rule of the campaign: never push to an accepted/frozen PR.</footer>
</main>
'''


def main():
    rows = collect()
    if not rows:
        sys.exit("no PR data collected — is gh authenticated?")
    ts = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    out = Path(__file__).parent / "dashboard.html"
    out.write_text(render(rows, ts))
    print(f"wrote {out} ({len(rows)} PRs)")


if __name__ == "__main__":
    main()
