# dynamo/access-review-backfill

Complete an interrupted quarterly access recertification for a ZFS-backed
NFSv4 filer. The agent receives the filer capture (per-object ACLs in
`nfs4_getfacl` notation, an object manifest, and a passwd/group identity
snapshot) plus the audit tool's partially completed worksheet, and must
fill in the 150 missing PERMIT/DENY decisions exactly as the filer would
enforce them, preserving the 90 issued rows verbatim. Graded byte-exactly
against the enforced outcome.
