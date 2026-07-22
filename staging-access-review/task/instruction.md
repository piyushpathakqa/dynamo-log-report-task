Filer `tank01` exports `/export` over NFSv4 with native ACL enforcement.
The quarterly access recertification `AR-2025-Q2` was interrupted: the
audit tool stopped partway through its worksheet during a storage
incident, leaving `/app/data/access_review_partial.csv` with 90 completed
rows and 150 rows whose decision field is empty.

Finish the review:

1. Read the audit specification at `/app/data/audit_spec.md`. It defines
   the capture bundle (`/app/data/acl_dump.txt`,
   `/app/data/object_manifest.csv`, `/app/data/passwd.snapshot`,
   `/app/data/group.snapshot`), identity resolution, the ACL entry
   notation, the operations under review, and the decision rule.
2. For every row whose decision field is empty, determine the decision
   for that user, path, and operation. Each decision must hold what the
   filer would actually enforce for that request under the captured
   ACLs, as `/app/data/audit_spec.md` §6 defines.
3. Rows that carry a decision were completed and issued when the tool
   stopped and are part of the review of record: reproduce those lines
   unchanged, byte for byte.
4. Write the finished report to `/app/access_review.csv`: the exact
   header `row_id,user,path,operation,decision`, then rows `R0001`
   through `R0240` in ascending row_id, LF line endings, every decision
   `PERMIT` or `DENY`.

The capture bundle is the sole source for filer state and identities; the
specification is the sole normative definition of the decision rule.
