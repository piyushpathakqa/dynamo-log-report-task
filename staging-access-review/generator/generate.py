#!/usr/bin/env python3
"""
Generator for dynamo/access-review-backfill.

Synthesizes a ZFS-backed NFSv4 filer capture (ACL dump, object manifest,
passwd/group snapshot) plus a partially completed access-recertification
CSV, and hard-asserts the full trap geometry before writing anything:

  G1  the legacy tool's rule W1 (deny-overrides) reproduces EVERY completed
      row of the shipped partial report, clean and poisoned alike;
  G2  the correct rule C mismatches the completed rows on EXACTLY the
      poisoned subset (all C=PERMIT vs tool DENY, all caused by the
      lockdown-script deny family), earliest poisoned row within the
      first 5 completed rows;
  G3  every naive variant diverges from C on a large fraction of the 150
      graded rows (floors asserted); grading is whole-file byte-exact,
      so one wrong row -> reward 0;
  G4  no in-environment arbiter: no ACL tooling in the image, no worked
      evaluation example in the spec, and an arbiter-word scan over every
      agent-visible file;
  F5  the shipped reference solution, run as a subprocess against the
      agent-visible inputs only, reproduces the expected CSV byte-exactly;
  EXT (§20.9) every elementary ACL check that decides the report agrees
      bit-for-bit with FreeBSD's kernel evaluator _acl_denies() from
      sys/kern/subr_acl_nfs4.c, compiled verbatim in freebsd_golden/.

Deterministic: everything derives from SEED.
"""

import os
import random
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "task"))
DATA = os.path.join(TASK, "environment", "data")
TESTS = os.path.join(TASK, "tests")
SEED = 20250630

DOMAIN = "corp.example.com"

# ---------------------------------------------------------------- bits
# Values copied exactly from FreeBSD sys/sys/acl.h.
BIT = {
    "r": 0x00000008,  # READ_DATA / LIST_DIRECTORY
    "w": 0x00000010,  # WRITE_DATA / ADD_FILE
    "a": 0x00000020,  # APPEND_DATA / ADD_SUBDIRECTORY
    "x": 0x00000001,  # EXECUTE
    "d": 0x00000800,  # DELETE
    "D": 0x00000100,  # DELETE_CHILD
    "t": 0x00000200,  # READ_ATTRIBUTES
    "T": 0x00000400,  # WRITE_ATTRIBUTES
    "n": 0x00000040,  # READ_NAMED_ATTRS
    "N": 0x00000080,  # WRITE_NAMED_ATTRS
    "c": 0x00001000,  # READ_ACL
    "C": 0x00002000,  # WRITE_ACL
    "o": 0x00004000,  # WRITE_OWNER
    "y": 0x00008000,  # SYNCHRONIZE
}
LETTER_ORDER = "rwaxdDtTnNcCoy"

def perm_mask(letters):
    m = 0
    for ch in letters:
        m |= BIT[ch]
    return m

def mask_letters(mask):
    return "".join(ch for ch in LETTER_ORDER if BIT[ch] & mask)

OPS = {
    # op -> (target type, required bits on target)
    "read": ("f", perm_mask("r")),
    "modify": ("f", perm_mask("w")),
    "readwrite": ("f", perm_mask("rw")),
    "list": ("d", perm_mask("r")),
    "create": ("d", perm_mask("w")),
}
XBIT = BIT["x"]

# ---------------------------------------------------------------- identity
GROUPS = [
    # (name, gid)
    ("wheel", 0),
    ("eng", 5001), ("qa", 5002), ("ops", 5003), ("platform", 5004),
    ("data", 5005), ("finance", 5006), ("hr", 5007), ("legal", 5008),
    ("secops", 5009), ("marketing", 5010), ("release", 5011),
    ("atlas", 5012), ("borealis", 5013), ("auditors", 5014),
    ("archops", 5015), ("contractors", 5020), ("interns", 5021),
]
GID = {name: gid for name, gid in GROUPS}

# (login, primary group, supplementary groups)
USERS_SPEC = [
    ("root", "wheel", []),
    # --- staff engineers / leads (share owners among them) ---
    ("nvaldez", "eng", ["atlas", "release"]),
    ("mokafor", "eng", ["platform"]),
    ("tsairas", "eng", ["atlas"]),
    ("lgrieve", "eng", ["borealis"]),
    ("pdhawan", "eng", []),
    ("rkellett", "qa", ["release"]),
    ("yfontaine", "qa", []),
    ("hbrandt", "qa", ["atlas"]),
    ("wnakato", "ops", ["platform", "archops"]),
    ("cjivraj", "ops", ["secops"]),
    ("bsalter", "ops", []),
    ("fdrummond", "platform", ["eng"]),
    ("gveras", "platform", ["release"]),
    ("smadsen", "data", ["atlas"]),
    ("kwainai", "data", ["borealis"]),
    ("jhalloran", "data", []),
    ("evasquez", "finance", ["auditors"]),
    ("obrennan", "finance", []),
    ("ltakagi", "finance", ["legal"]),
    ("mreiner", "hr", []),
    ("dcoppola", "hr", ["legal"]),
    ("azhukova", "legal", []),
    ("qfarrow", "legal", ["auditors"]),
    ("uossola", "secops", ["ops", "auditors"]),
    ("vtremblay", "secops", []),
    ("imalouf", "marketing", []),
    ("xberrio", "marketing", []),
    ("zpellerin", "release", ["eng"]),
    ("warchibald", "archops", ["ops"]),
    ("ryamanaka", "auditors", ["finance"]),
    # --- contractors also embedded in delivery teams (crux population) ---
    ("kcasal", "contractors", ["eng"]),
    ("dvirtanen", "contractors", ["eng", "atlas"]),
    ("psoltani", "contractors", ["data"]),
    ("mbelmonte", "contractors", ["data", "borealis"]),
    ("tnorgaard", "contractors", ["platform"]),
    ("aharlow", "contractors", ["atlas"]),
    ("jkovanen", "contractors", ["release", "eng"]),
    ("rdelacroix", "contractors", ["qa", "atlas"]),
    ("speixoto", "contractors", ["platform", "release"]),
    ("ncardona", "contractors", ["borealis"]),
    # --- contractors with no team embed ---
    ("bvanhoute", "contractors", []),
    ("gmarchetti", "contractors", []),
    # --- interns embedded in teams ---
    ("lfarkas", "interns", ["eng"]),
    ("cnwosu", "interns", ["data"]),
    ("tmagnusson", "interns", ["qa"]),
    ("hkeitel", "interns", ["finance"]),
    # --- misc staff, no share team ---
    ("ovillar", "marketing", ["interns"]),
    ("edanailov", "auditors", []),
]

class User:
    def __init__(self, login, uid, primary, supp):
        self.login = login
        self.uid = uid
        self.primary = primary
        self.gids = [GID[primary]] + [GID[g] for g in supp]
        self.groups = {primary, *supp}

USERS = {}
_uid = 4000
for login, prim, supp in USERS_SPEC:
    uid = 0 if login == "root" else (_uid := _uid + 1)
    USERS[login] = User(login, uid, prim, supp)

# ---------------------------------------------------------------- ACEs
class Ace:
    __slots__ = ("etype", "flags", "principal", "perm")
    def __init__(self, etype, flags, principal, letters):
        self.etype = etype            # 'A' | 'D'
        self.flags = flags            # subset of 'gfdi'
        self.principal = principal    # 'OWNER@' | 'GROUP@' | 'EVERYONE@' | name
        self.perm = perm_mask(letters)
    def line(self):
        return f"{self.etype}:{self.flags}:{self.principal}:{mask_letters(self.perm)}"

def A(principal, letters, flags=""):
    return Ace("A", flags, principal, letters)

def D(principal, letters, flags=""):
    return Ace("D", flags, principal, letters)

def qual(name):
    return f"{name}@{DOMAIN}"

class Obj:
    __slots__ = ("path", "type", "owner", "group", "acl")
    def __init__(self, path, otype, owner, group, acl):
        self.path = path
        self.type = otype             # 'f' | 'd'
        self.owner = owner            # login
        self.group = group            # group name
        self.acl = acl                # [Ace]

OBJECTS = {}

def add(path, otype, owner, group, acl):
    assert path not in OBJECTS, path
    OBJECTS[path] = Obj(path, otype, owner, group, acl)

# Standard ACE building blocks (dumps captured on a Linux client via
# nfs4_getfacl look like this).
OWNER_D = A("OWNER@", "rwaxdDtTnNcCy")
OWNER_F = A("OWNER@", "rwadtTnNcCy")

def group_obj(letters):
    return A("GROUP@", letters, "g")

def team_dir(team, letters="rwaxdDtTnNcy"):
    return A(qual(team), letters, "gfd")

def team_file(team, letters="rwatTnNcy"):
    return A(qual(team), letters, "g")

LOCKDOWN = lambda: D(qual("contractors"), "rwa", "g")     # appended last
HARDENING = lambda g: D(qual(g), "rwa", "g")              # placed first

# ---------------------------------------------------------------- tree
rng = random.Random(SEED)

FILE_WORDS = [
    "summary", "notes", "draft", "matrix", "pipeline", "handover", "budget",
    "checklist", "inventory", "review", "playbook", "rollout", "baseline",
    "metrics", "digest", "ledger", "workplan", "postmortem", "capacity",
    "forecast", "runcard", "topology", "manifest", "roster", "briefing",
]
FILE_EXT = [".md", ".csv", ".txt", ".json", ".yaml", ".rst", ".tsv", ".ini"]

_word_i = 0
def fname():
    global _word_i
    w = FILE_WORDS[_word_i % len(FILE_WORDS)]
    n = _word_i // len(FILE_WORDS)
    _word_i += 1
    ext = FILE_EXT[(_word_i * 7 + n) % len(FILE_EXT)]
    return f"{w}{n if n else ''}{ext}"

def build_tree():
    # filer root: everyone may look up and list.
    add("/export", "d", "root", "wheel",
        [OWNER_D, group_obj("rxtncy"), A("EVERYONE@", "rxtncy")])

    # share spec: (name, team, owner, subdirs, nfiles, lockdown, hardening,
    #              extra dir aces, file mix)
    shares = [
        ("eng",      "eng",      "nvaldez",   ["specs", "src", "tools"],   24, True,  None),
        ("qa",       "qa",       "rkellett",  ["plans", "results"],        16, False, None),
        ("ops",      "ops",      "wnakato",   ["runbooks", "scripts"],     18, False, None),
        ("platform", "platform", "fdrummond", ["infra", "images"],         16, True,  None),
        ("data",     "data",     "smadsen",   ["feeds", "models"],         20, True,  None),
        ("finance",  "finance",  "evasquez",  ["close", "fpa"],            18, True,  "interns"),
        ("hr",       "hr",       "mreiner",   ["people", "policies"],      12, False, "contractors"),
        ("legal",    "legal",    "azhukova",  ["contracts", "filings"],    12, False, "interns"),
        ("releases", "release",  "zpellerin", ["v41", "v42"],              14, True,  None),
        ("archive",  "archops",  "warchibald", ["cold", "vault"],          12, False, "interns"),
        ("common",   "marketing", "imalouf",  ["brand", "allhands"],       20, False, None),
    ]
    for name, team, owner, subs, nfiles, lockdown, hardening in shares:
        base = f"/export/{name}"
        dir_acl = []
        if hardening:
            dir_acl.append(HARDENING(hardening))
        dir_acl += [OWNER_D, group_obj("rxaDtTnNcy" if name != "common" else "rxtncy"),
                    team_dir(team)]
        if name == "common":
            dir_acl.append(A("EVERYONE@", "rxtncy"))
        if name == "releases":
            dir_acl.append(A(qual("qa"), "rxtncy", "gfd"))
        if name == "archive":
            dir_acl.append(A(qual("auditors"), "rxtncy", "gfd"))
        if lockdown:
            dir_acl.append(LOCKDOWN())
        add(base, "d", owner, team, dir_acl)

        for sd in subs:
            sd_acl = list(dir_acl)  # subdirs carry the same effective pattern
            add(f"{base}/{sd}", "d", owner, team, sd_acl)

        # distribute files across the share root and subdirs
        spots = [base] + [f"{base}/{sd}" for sd in subs]
        for i in range(nfiles):
            parent = spots[i % len(spots)]
            path = f"{parent}/{fname()}"
            if name == "common":
                # org-wide document: everyone reads, one owning team edits —
                # read and write arrive through different entries.
                wteam = ["marketing", "eng", "release", "ops", "hr"][i % 5]
                add(path, "f", "imalouf", team,
                    [OWNER_F, group_obj("rtncy"), A("EVERYONE@", "rtncy"),
                     A(qual(wteam), "watTnNcy", "g")])
                continue
            facl = []
            if hardening:
                facl.append(HARDENING(hardening))
            writable = (i % 3 != 2)
            facl += [OWNER_F,
                     group_obj("rtncy"),
                     team_file(team, "rwatTnNcy" if writable else "rtncy")]
            if name == "releases":
                facl.append(A(qual("qa"), "rtncy", "g"))
            if name == "archive":
                facl.append(A(qual("auditors"), "rtncy", "g"))
            if lockdown and (i % 10 != 7):   # lockdown pass covered most files
                facl.append(LOCKDOWN())
            add(path, "f", owner, team, facl)

    # projects parent + project shares (collab surface for split allows)
    add("/export/projects", "d", "root", "wheel",
        [OWNER_D, group_obj("rxtncy"), A("EVERYONE@", "rxtncy")])
    projects = [
        ("atlas", "atlas", "tsairas", 16, True),
        ("borealis", "borealis", "lgrieve", 14, False),
    ]
    for name, team, owner, nfiles, lockdown in projects:
        base = f"/export/projects/{name}"
        dir_acl = [OWNER_D, group_obj("rxaDtTnNcy"), team_dir(team),
                   A(qual("eng"), "rxtncy", "gfd")]
        if lockdown:
            dir_acl.append(LOCKDOWN())
        add(base, "d", owner, team, dir_acl)
        add(f"{base}/shared", "d", owner, team, list(dir_acl))
        spots = [base, f"{base}/shared"]
        for i in range(nfiles):
            parent = spots[i % len(spots)]
            path = f"{parent}/{fname()}"
            if i % 4 == 1:
                # split-allow collab file, created by an eng author: read
                # comes from the project group, write from eng — no single
                # entry carries read+write together.
                fowner = "mokafor"
                facl = [OWNER_F, group_obj("rtncy"),
                        A(qual(team), "rtncy", "g"),
                        A(qual("eng"), "watTnNcy", "g")]
            else:
                fowner = owner
                facl = [OWNER_F, group_obj("rtncy"),
                        team_file(team, "rwatTnNcy"),
                        A(qual("eng"), "rtncy", "g")]
            if lockdown and (i % 5 != 3):
                facl.append(LOCKDOWN())
            add(path, "f", fowner, team, facl)

    # cross-team report drops: named-group file grants inside shares whose
    # directory does not give that group lookup (traversal matters).
    add("/export/finance/reports", "d", "evasquez", "finance",
        [HARDENING("interns"), OWNER_D, group_obj("rxaDtTnNcy"),
         team_dir("finance"), LOCKDOWN()])
    for i in range(8):
        facl = [HARDENING("interns"), OWNER_F, group_obj("rtncy"),
                team_file("finance", "rwatTnNcy"),
                A(qual("data"), "rtncy", "g"),
                A(qual("auditors"), "rtncy", "g")]
        if i % 3 != 2:
            facl.append(LOCKDOWN())
        add(f"/export/finance/reports/{fname()}", "f", "evasquez", "finance", facl)

    add("/export/hr/exports", "d", "mreiner", "hr",
        [HARDENING("contractors"), OWNER_D, group_obj("rxaDtTnNcy"),
         team_dir("hr")])
    for i in range(6):
        add(f"/export/hr/exports/{fname()}", "f", "mreiner", "hr",
            [HARDENING("contractors"), OWNER_F, group_obj("rtncy"),
             team_file("hr", "rwatTnNcy"), A(qual("finance"), "rtncy", "g")])

    # a few inherit-only entries on dirs (inert for access, stated in spec)
    OBJECTS["/export/eng/specs"].acl.insert(3, A(qual("eng"), "rwatTnNcy", "gfdi"))
    OBJECTS["/export/data/feeds"].acl.insert(3, A(qual("data"), "rwatTnNcy", "gfdi"))
    OBJECTS["/export/archive/vault"].acl.insert(3, A(qual("auditors"), "rtncy", "gfdi"))

build_tree()

# ---------------------------------------------------------------- semantics
ELEM_LOG = []   # (obj_path, user, mask, denied) for every elementary C check

def ace_matches(ace, user, obj):
    if "i" in ace.flags:
        return None    # inherit-only: not part of the object's own checks
    p = ace.principal
    if p == "OWNER@":
        return user.uid == USERS[obj.owner].uid
    if p == "GROUP@":
        return GID[obj.group] in user.gids
    if p == "EVERYONE@":
        return True
    name = p.split("@", 1)[0]
    if "g" in ace.flags:
        return GID[name] in user.gids
    return name in USERS and USERS[name].uid == user.uid

def acl_denies_C(obj, user, mask, log=True):
    """Mirror of FreeBSD _acl_denies(): walk entries; an allow clears the
    requested bits it carries; a deny fires iff it overlaps a still-needed
    bit."""
    m = mask
    for ace in obj.acl:
        matched = ace_matches(ace, user, obj)
        if not matched:
            continue
        if ace.etype == "D" and (ace.perm & m):
            if log:
                ELEM_LOG.append((obj.path, user.login, mask, 1))
            return True
        m &= ~ace.perm
        if m == 0:
            if log:
                ELEM_LOG.append((obj.path, user.login, mask, 0))
            return False
    denied = m != 0
    if log:
        ELEM_LOG.append((obj.path, user.login, mask, 1 if denied else 0))
    return denied

def eval_w1(obj, user, mask):
    """Deny-overrides: any matching deny overlapping the request denies;
    otherwise the union of matching allows must cover the request."""
    allowed = 0
    for ace in obj.acl:
        if not ace_matches(ace, user, obj):
            continue
        if ace.etype == "D" and (ace.perm & mask):
            return True
        if ace.etype == "A":
            allowed |= ace.perm
    return (mask & ~allowed) != 0

def eval_w2(obj, user, mask):
    """First matching entry that mentions any requested bit decides the
    whole request."""
    for ace in obj.acl:
        if not ace_matches(ace, user, obj):
            continue
        if ace.perm & mask:
            return ace.etype == "D"
    return True

def eval_w3(obj, user, mask):
    """A single allow entry must carry every requested bit; any matching
    deny overlapping the request denies."""
    for ace in obj.acl:
        if not ace_matches(ace, user, obj):
            continue
        if ace.etype == "D" and (ace.perm & mask):
            return True
    for ace in obj.acl:
        if not ace_matches(ace, user, obj):
            continue
        if ace.etype == "A" and (mask & ~ace.perm) == 0:
            return False
    return True

def ancestors(path):
    out = []
    parts = path.split("/")[1:]
    for i in range(1, len(parts)):
        out.append("/" + "/".join(parts[:i]))
    return [p for p in out if p in OBJECTS]

def decide(evaluator, user_login, path, op, traversal=True, log=False):
    user = USERS[user_login]
    obj = OBJECTS[path]
    ttype, mask = OPS[op]
    assert obj.type == ttype, (path, op)
    if traversal:
        for anc in ancestors(path):
            denied = (acl_denies_C(OBJECTS[anc], user, XBIT, log=log)
                      if evaluator is None
                      else evaluator(OBJECTS[anc], user, XBIT))
            if denied:
                return "DENY"
    denied = (acl_denies_C(obj, user, mask, log=log)
              if evaluator is None
              else evaluator(obj, user, mask))
    return "DENY" if denied else "PERMIT"

def decide_all(user, path, op):
    return {
        "C":  decide(None, user, path, op, log=True),
        "W1": decide(eval_w1, user, path, op),
        "W2": decide(eval_w2, user, path, op),
        "W3": decide(eval_w3, user, path, op),
        "W5": decide(None, user, path, op, traversal=False),
    }

# ---------------------------------------------------------------- candidates
def contractor_shadow_deny(obj, user):
    """True iff the only reason W1 denies is the lockdown deny family."""
    trimmed = Obj(obj.path, obj.type, obj.owner, obj.group,
                  [a for a in obj.acl
                   if not (a.etype == "D" and a.principal == qual("contractors"))])
    return trimmed

candidates = {}   # signature -> list of (user, path, op)
AUDIT_USERS = [u for u in USERS if u != "root"]
for login in AUDIT_USERS:
    for path, obj in OBJECTS.items():
        ops = ("read", "modify", "readwrite") if obj.type == "f" else ("list", "create")
        for op in ops:
            d = decide_all(login, path, op)
            sig = (d["C"], d["W1"], d["W2"], d["W3"], d["W5"])
            candidates.setdefault(sig, []).append((login, path, op, d))

def pick(sig_filter, n, taken, spread_key=None):
    pool = []
    for sig, rows in sorted(candidates.items()):
        if sig_filter(sig):
            pool.extend(rows)
    pool = [r for r in pool if (r[0], r[1], r[2]) not in taken]
    pool.sort(key=lambda r: (r[1], r[0], r[2]))
    rng.shuffle(pool)
    if spread_key:
        # round-robin across the spread key so one user/share can't dominate
        buckets = {}
        for r in pool:
            buckets.setdefault(spread_key(r), []).append(r)
        ordered, keys = [], sorted(buckets)
        while len(ordered) < len(pool):
            for k in keys:
                if buckets[k]:
                    ordered.append(buckets[k].pop(0))
        pool = ordered
    out = pool[:n]
    assert len(out) == n, f"needed {n}, pool had {len(out)} for {sig_filter}"
    for r in out:
        taken.add((r[0], r[1], r[2]))
    return out

P, Y = "PERMIT", "DENY"
taken = set()

# --- completed set (90 rows, decisions = W1 = the legacy tool) ---
comp_poison   = pick(lambda s: s[0] == P and s[1] == Y and s[4] == P, 20, taken,
                     spread_key=lambda r: r[1].split("/")[2])
comp_denyfirst = pick(lambda s: s[0] == Y and s[1] == Y and s[4] == Y, 15, taken)
comp_w3disc   = pick(lambda s: s == (P, P, P, Y, P), 8, taken)
comp_w2disc   = pick(lambda s: s[0] == Y and s[1] == Y and s[2] == P and s[4] == Y, 5, taken)
comp_w5disc   = pick(lambda s: s[0] == Y and s[1] == Y and s[4] == P, 6, taken)
comp_plain_p  = pick(lambda s: s == (P, P, P, P, P), 22, taken)
comp_plain_d  = pick(lambda s: s == (Y, Y, Y, Y, Y), 14, taken)

completed_rows = (comp_denyfirst[:2] + [comp_poison[0]] + comp_plain_p[:2]
                  + [comp_poison[1]])
rest = (comp_poison[2:] + comp_denyfirst[2:] + comp_w3disc + comp_w2disc
        + comp_w5disc + comp_plain_p[2:] + comp_plain_d)
rng.shuffle(rest)
completed_rows += rest
assert len(completed_rows) == 90

# --- graded set (150 rows, decisions = C) ---
grad_shadow = pick(lambda s: s[0] == P and s[1] == Y and s[4] == P, 60, taken,
                   spread_key=lambda r: r[1].split("/")[2])
grad_w3     = pick(lambda s: s[0] == P and s[3] == Y and s[1] == P, 22, taken)
grad_w2     = pick(lambda s: s[0] == Y and s[2] == P and s[1] == Y and s[4] == Y, 20, taken)
grad_w5     = pick(lambda s: s[0] == Y and s[4] == P and s[1] == Y, 18, taken)
grad_plain_p = pick(lambda s: s == (P, P, P, P, P), 16, taken)
grad_plain_d = pick(lambda s: s == (Y, Y, Y, Y, Y), 14, taken)

graded_rows = grad_shadow + grad_w3 + grad_w2 + grad_w5 + grad_plain_p + grad_plain_d
rng.shuffle(graded_rows)
assert len(graded_rows) == 150

ALL_ROWS = completed_rows + graded_rows

# ---------------------------------------------------------------- emission
def csv_line(i, row, decision):
    login, path, op, _ = row
    return f"R{i+1:04d},{login},{path},{op},{decision}"

partial_lines = ["row_id,user,path,operation,decision"]
expected_lines = ["row_id,user,path,operation,decision"]
for i, row in enumerate(ALL_ROWS):
    d = row[3]
    if i < 90:
        line = csv_line(i, row, d["W1"])     # the legacy tool's output, as issued
        partial_lines.append(line)
        expected_lines.append(line)          # preserved verbatim
    else:
        partial_lines.append(csv_line(i, row, ""))
        expected_lines.append(csv_line(i, row, d["C"]))

partial_csv = "\n".join(partial_lines) + "\n"
expected_csv = "\n".join(expected_lines) + "\n"

def render_passwd():
    lines = []
    for login, prim, supp in USERS_SPEC:
        u = USERS[login]
        home = "/root" if login == "root" else f"/home/{login}"
        shell = "/bin/sh" if login == "root" else "/bin/bash"
        lines.append(f"{login}:x:{u.uid}:{GID[prim]}::{home}:{shell}")
    return "\n".join(lines) + "\n"

def render_group():
    members = {name: [] for name, _ in GROUPS}
    for login, prim, supp in USERS_SPEC:
        for g in supp:
            members[g].append(login)
    lines = []
    for name, gid in GROUPS:
        lines.append(f"{name}:x:{gid}:{','.join(members[name])}")
    return "\n".join(lines) + "\n"

def render_acl_dump():
    chunks = []
    for path in sorted(OBJECTS):
        obj = OBJECTS[path]
        chunks.append("# file: " + path + "\n"
                      + "\n".join(a.line() for a in obj.acl) + "\n")
    return "\n".join(chunks)

def render_manifest():
    lines = ["path,type,owner,group"]
    for path in sorted(OBJECTS):
        o = OBJECTS[path]
        lines.append(f"{path},{o.type},{o.owner},{o.group}")
    return "\n".join(lines) + "\n"

# ---------------------------------------------------------------- asserts
def check(cond, msg):
    if not cond:
        print("ASSERT FAILED:", msg)
        sys.exit(1)

# G1: the tool's rule reproduces every completed row it shipped.
for i, row in enumerate(completed_rows):
    check(row[3]["W1"] == partial_lines[1 + i].rsplit(",", 1)[1],
          f"G1 broken at completed row {i}")

# G2: C mismatches completed rows on exactly the poisoned subset.
poison_idx = [i for i, row in enumerate(completed_rows) if row[3]["C"] != row[3]["W1"]]
check(len(poison_idx) == 20, f"poison count {len(poison_idx)} != 20")
check(min(poison_idx) <= 4, "earliest poisoned row too late")
for i in poison_idx:
    row = completed_rows[i]
    check(row[3]["C"] == P and row[3]["W1"] == Y, "poison not uniform PERMIT->DENY")
    # the flip must be caused by the lockdown deny family alone, on the
    # TARGET object (ancestor checks agree under both rules)
    login, path, op, d = row
    user, obj = USERS[login], OBJECTS[path]
    for anc in ancestors(path):
        check(acl_denies_C(OBJECTS[anc], user, XBIT, log=False)
              == eval_w1(OBJECTS[anc], user, XBIT),
              f"poison row {i} diverges on ancestor {anc}")
    trimmed = contractor_shadow_deny(obj, user)
    check(eval_w1(trimmed, user, OPS[op][1]) == acl_denies_C(trimmed, user, OPS[op][1], log=False),
          f"poison row {i} not caused by lockdown deny family")

# Uniqueness: no other variant fits the full completed precedent.
for name, ev in (("W2", eval_w2), ("W3", eval_w3)):
    miss = sum(1 for row in completed_rows if row[3][name] != row[3]["W1"])
    check(miss >= 3, f"{name} fits the precedent too well ({miss} misses)")
miss5 = sum(1 for row in completed_rows if row[3]["W5"] != row[3]["W1"])
check(miss5 >= 3, f"W5 fits the precedent too well ({miss5} misses)")

# G3 floors on the graded 150.
floors = {"W1": 50, "W2": 20, "W3": 20, "W5": 15}
for name, floor in floors.items():
    div = sum(1 for row in graded_rows if row[3][name] != row[3]["C"])
    check(div >= floor, f"{name} diverges on only {div} graded rows (< {floor})")
    print(f"  {name}: {div}/150 graded rows wrong")
n_p = sum(1 for row in graded_rows if row[3]["C"] == P)
check(40 <= n_p <= 110, f"graded PERMIT balance off: {n_p}")
print(f"  graded balance: {n_p} PERMIT / {150 - n_p} DENY")

# G4 arbiter-word scan runs after files are written (below).

# ---------------------------------------------------------------- write
os.makedirs(DATA, exist_ok=True)
os.makedirs(TESTS, exist_ok=True)

with open(os.path.join(DATA, "passwd.snapshot"), "w") as f:
    f.write(render_passwd())
with open(os.path.join(DATA, "group.snapshot"), "w") as f:
    f.write(render_group())
with open(os.path.join(DATA, "acl_dump.txt"), "w") as f:
    f.write(render_acl_dump())
with open(os.path.join(DATA, "object_manifest.csv"), "w") as f:
    f.write(render_manifest())
with open(os.path.join(DATA, "access_review_partial.csv"), "w") as f:
    f.write(partial_csv)

with open(os.path.join(TESTS, "expected_access_review.csv"), "w") as f:
    f.write(expected_csv)
with open(os.path.join(TESTS, "partial_snapshot.csv"), "w") as f:
    f.write(partial_csv)

# G4: arbiter-word scan over every agent-visible text file. The wrong-vs-
# right delta is entry ORDER sensitivity; no agent-visible words may
# arbitrate it.
ARBITER_WORDS = [
    "order", "sequen", "preced", "accumul", "overrid", "first", "last",
    "earlier", "later", "before", "after", "prior", "shadow", "append",
    "trailing", "leading", "position", "supersede", "cascade", "canonical",
]
visible = ["acl_dump.txt", "object_manifest.csv", "passwd.snapshot",
           "group.snapshot", "access_review_partial.csv", "audit_spec.md"]
for fn in visible:
    p = os.path.join(DATA, fn)
    if not os.path.exists(p):
        continue
    text = open(p).read().lower()
    for w in ARBITER_WORDS:
        check(w not in text, f"arbiter word '{w}' present in {fn}")
inst = os.path.join(TASK, "instruction.md")
if os.path.exists(inst):
    text = open(inst).read().lower()
    for w in ARBITER_WORDS:
        check(w not in text, f"arbiter word '{w}' present in instruction.md")

# ---------------------------------------------------------------- EXT golden
harness = os.path.join(HERE, "freebsd_golden", "acl_harness")
check(os.path.exists(harness), "compile freebsd_golden/acl_harness first")

TAG = {"OWNER@": 0x1, "USER": 0x2, "GROUP@": 0x4, "GROUP": 0x8, "EVERYONE@": 0x40}
TYPE = {"A": 0x100, "D": 0x200}
INHERIT_ONLY = 0x8

def harness_line(obj_path, login, mask):
    obj, user = OBJECTS[obj_path], USERS[login]
    owner = USERS[obj.owner]
    fields = [str(owner.uid), str(GID[obj.group]), str(mask),
              str(len(user.gids))] + [str(g) for g in user.gids] \
             + [str(user.uid), str(len(obj.acl))]
    for a in obj.acl:
        if a.principal == "OWNER@":
            tag, aid = TAG["OWNER@"], 0
        elif a.principal == "GROUP@":
            tag, aid = TAG["GROUP@"], 0
        elif a.principal == "EVERYONE@":
            tag, aid = TAG["EVERYONE@"], 0
        elif "g" in a.flags:
            tag, aid = TAG["GROUP"], GID[a.principal.split("@", 1)[0]]
        else:
            tag, aid = TAG["USER"], USERS[a.principal.split("@", 1)[0]].uid
        flags = INHERIT_ONLY if "i" in a.flags else 0
        fields.append(f"{tag},{aid},{a.perm},{TYPE[a.etype]},{flags}")
    return " ".join(fields)

elem = list(dict.fromkeys((p, u, m) for p, u, m, _ in ELEM_LOG))
lines_in = "\n".join(harness_line(p, u, m) for p, u, m in elem) + "\n"
res = subprocess.run([harness], input=lines_in, capture_output=True, text=True)
check(res.returncode == 0, f"harness failed: {res.stderr}")
got = res.stdout.split()
check(len(got) == len(elem), "harness output length mismatch")
py = {}
for p, u, m, dnd in ELEM_LOG:
    py[(p, u, m)] = dnd
bad = [(e, g) for e, g in zip(elem, got) if py[e] != int(g)]
check(not bad, f"EXTERNAL GOLDEN MISMATCH on {len(bad)} checks, e.g. {bad[:3]}")
print(f"  external golden: {len(elem)} elementary checks agree with FreeBSD _acl_denies")

# ---------------------------------------------------------------- F5 oracle
solve = os.path.join(TASK, "solution", "solve.py")
check(os.path.exists(solve), "solution/solve.py missing")
with tempfile.TemporaryDirectory() as tmp:
    app = os.path.join(tmp, "app")
    shutil.copytree(DATA, os.path.join(app, "data"))
    res = subprocess.run([sys.executable, solve], cwd=tmp,
                         env={**os.environ, "APP_ROOT": app},
                         capture_output=True, text=True)
    check(res.returncode == 0, f"solve.py failed: {res.stderr[-2000:]}")
    out = open(os.path.join(app, "access_review.csv")).read()
    check(out == expected_csv, "F5: oracle output != expected golden CSV")
print("  F5: solution/solve.py reproduces the expected CSV byte-exactly")

# naive-variant CSVs for the end-to-end harbor gate
NAIVE_DIR = os.path.join(HERE, "naive_outputs")
os.makedirs(NAIVE_DIR, exist_ok=True)
for name in ("W1", "W2", "W3", "W5"):
    lines = ["row_id,user,path,operation,decision"]
    for i, row in enumerate(ALL_ROWS):
        if i < 90:
            lines.append(partial_lines[1 + i])
        else:
            lines.append(csv_line(i, row, row[3][name]))
    naive_csv = "\n".join(lines) + "\n"
    check(naive_csv != expected_csv, f"naive {name} equals expected?!")
    with open(os.path.join(NAIVE_DIR, f"access_review_{name}.csv"), "w") as f:
        f.write(naive_csv)

print("GENERATION OK: 240 rows (90 completed / 150 graded), "
      f"{len(OBJECTS)} objects, {len(USERS)} users")
