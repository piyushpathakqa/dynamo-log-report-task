#!/usr/bin/env python3
"""Reference completion of audit AR-2025-Q2.

Works from the agent-visible capture only: passwd/group snapshot, object
manifest, nfs4_getfacl dump, and the partial review CSV. Evaluates every
pending request exactly as the filer enforces NFSv4 ACLs (RFC 8881
access-check algorithm) and preserves the issued rows verbatim.
"""

import os

APP = os.environ.get("APP_ROOT", "/app")
DATA = os.path.join(APP, "data")
DOMAIN = "corp.example.com"

BIT = {
    "r": 0x00000008, "w": 0x00000010, "a": 0x00000020, "x": 0x00000001,
    "d": 0x00000800, "D": 0x00000100, "t": 0x00000200, "T": 0x00000400,
    "n": 0x00000040, "N": 0x00000080, "c": 0x00001000, "C": 0x00002000,
    "o": 0x00004000, "y": 0x00008000,
}

OP_BITS = {
    "read": BIT["r"], "modify": BIT["w"], "readwrite": BIT["r"] | BIT["w"],
    "list": BIT["r"], "create": BIT["w"],
}
XBIT = BIT["x"]


def load_identity():
    uid_of, gid_of_user_primary = {}, {}
    with open(os.path.join(DATA, "passwd.snapshot")) as f:
        for line in f:
            if not line.strip():
                continue
            name, _, uid, gid = line.split(":")[:4]
            uid_of[name] = int(uid)
            gid_of_user_primary[name] = int(gid)
    gid_of, member_gids = {}, {u: set() for u in uid_of}
    with open(os.path.join(DATA, "group.snapshot")) as f:
        for line in f:
            if not line.strip():
                continue
            name, _, gid, members = line.rstrip("\n").split(":")
            gid_of[name] = int(gid)
            for m in members.split(","):
                if m:
                    member_gids[m].add(int(gid))
    groups_of = {}
    for u in uid_of:
        groups_of[u] = {gid_of_user_primary[u]} | member_gids[u]
    return uid_of, gid_of, groups_of


def load_manifest():
    meta = {}
    with open(os.path.join(DATA, "object_manifest.csv")) as f:
        next(f)
        for line in f:
            path, otype, owner, group = line.rstrip("\n").split(",")
            meta[path] = (otype, owner, group)
    return meta


def load_acls():
    acls, cur = {}, None
    with open(os.path.join(DATA, "acl_dump.txt")) as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                cur = None
                continue
            if line.startswith("# file: "):
                cur = line[len("# file: "):]
                acls[cur] = []
                continue
            etype, flags, principal, perms = line.split(":")
            mask = 0
            for ch in perms:
                mask |= BIT[ch]
            acls[cur].append((etype, flags, principal, mask))
    return acls


UID_OF, GID_OF, GROUPS_OF = load_identity()
META = load_manifest()
ACLS = load_acls()


def entry_applies(entry, user, path):
    etype, flags, principal, mask = entry
    if "i" in flags:
        return False          # inherit-only: no effect on the object itself
    if principal == "OWNER@":
        return UID_OF[user] == UID_OF[META[path][1]]
    if principal == "GROUP@":
        return GID_OF[META[path][2]] in GROUPS_OF[user]
    if principal == "EVERYONE@":
        return True
    name = principal.split("@", 1)[0]
    if "g" in flags:
        return GID_OF[name] in GROUPS_OF[user]
    return name in UID_OF and UID_OF[name] == UID_OF[user]


def granted(user, path, needed):
    """RFC 8881 access check: walk the ACL; an ALLOW entry satisfies the
    requested bits it carries; a DENY entry rejects the request iff it
    covers a requested bit that is still unsatisfied when it is reached."""
    for entry in ACLS[path]:
        if not entry_applies(entry, user, path):
            continue
        etype, _, _, mask = entry
        if etype == "D" and (mask & needed):
            return False
        if etype == "A":
            needed &= ~mask
        if needed == 0:
            return True
    return needed == 0


def decide(user, path, op):
    parts = path.split("/")[1:]
    for i in range(1, len(parts)):
        anc = "/" + "/".join(parts[:i])
        if anc in ACLS and not granted(user, anc, XBIT):
            return "DENY"
    return "PERMIT" if granted(user, path, OP_BITS[op]) else "DENY"


def main():
    out = []
    with open(os.path.join(DATA, "access_review_partial.csv")) as f:
        out.append(f.readline().rstrip("\n"))
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            row_id, user, path, op, decision = line.split(",")
            if decision:
                out.append(line)                       # issued rows: verbatim
            else:
                out.append(f"{row_id},{user},{path},{op},{decide(user, path, op)}")
    with open(os.path.join(APP, "access_review.csv"), "w") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
