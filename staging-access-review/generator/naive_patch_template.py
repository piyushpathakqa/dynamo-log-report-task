#!/usr/bin/env python3
"""Runs the shipped reference solver with its ACL evaluation swapped for a
plausible-but-wrong convention. Used ONLY for the local pre-push gate: each
variant must score 0.0 end-to-end."""

import importlib.util

VARIANT = "__VARIANT__"

spec = importlib.util.spec_from_file_location("solve", "/solution/solve.py")
s = importlib.util.module_from_spec(spec)
# __name__ is "solve", not "__main__", so import does not trigger main()
spec.loader.exec_module(s)


def granted_w1(user, path, needed):
    """Deny-overrides: any matching deny touching the request denies."""
    allowed = 0
    for entry in s.ACLS[path]:
        if not s.entry_applies(entry, user, path):
            continue
        etype, _, _, mask = entry
        if etype == "D" and (mask & needed):
            return False
        if etype == "A":
            allowed |= mask
    return (needed & ~allowed) == 0


def granted_w2(user, path, needed):
    """First matching entry mentioning a requested bit decides everything."""
    for entry in s.ACLS[path]:
        if not s.entry_applies(entry, user, path):
            continue
        etype, _, _, mask = entry
        if mask & needed:
            return etype == "A"
    return False


def granted_w3(user, path, needed):
    """A single allow entry must carry every requested bit."""
    for entry in s.ACLS[path]:
        if not s.entry_applies(entry, user, path):
            continue
        etype, _, _, mask = entry
        if etype == "D" and (mask & needed):
            return False
    for entry in s.ACLS[path]:
        if not s.entry_applies(entry, user, path):
            continue
        etype, _, _, mask = entry
        if etype == "A" and (needed & ~mask) == 0:
            return True
    return False


def decide_w5(user, path, op):
    """Correct evaluation on the target, but no ancestor traversal check."""
    return "PERMIT" if s.granted(user, path, s.OP_BITS[op]) else "DENY"


if VARIANT == "W1":
    s.granted = granted_w1
elif VARIANT == "W2":
    s.granted = granted_w2
elif VARIANT == "W3":
    s.granted = granted_w3
elif VARIANT == "W5":
    s.decide = decide_w5
else:
    raise SystemExit(f"unknown variant {VARIANT}")

s.main()
