# Access recertification AR-2025-Q2 — filer `tank01` — audit specification

## 1. Scope and authority

This review recertifies user access on the corporate file service `tank01`,
a ZFS-backed filer exporting `/export` over NFSv4. The filer enforces
NFSv4 access control lists (RFC 8881) natively on every object.

Each review row asks: for this user, this path, and this operation, does
the filer grant the access? The recorded decision states **enforcement as
the filer applies it** — what an actual request by that user would get —
not the access that administrators may have intended to configure.

## 2. Capture bundle

All inputs were captured together on 2025-06-30 from the audit host, a
Linux client with the export mounted:

- `acl_dump.txt` — every object's ACL, captured with `nfs4_getfacl` walking
  the tree; below each `# file: <path>` line, the object's entries appear
  exactly as the filer returned them.
- `object_manifest.csv` — `path,type,owner,group` for every object
  (`type` is `d` directory or `f` regular file).
- `passwd.snapshot`, `group.snapshot` — the identity source of record,
  copied from the central directory in standard `passwd(5)` / `group(5)`
  format.
- `access_review_partial.csv` — the review worksheet. The quarterly audit
  tool stopped mid-run during the 2025-06-30 storage incident; rows it had
  already completed carry a decision, the remaining rows carry an empty
  decision field.

## 3. Identity resolution

- A user's groups are: the primary group named by their `passwd` entry,
  plus every group whose member list in `group.snapshot` contains their
  login.
- ACL principals are qualified with `@corp.example.com`. A principal with
  the `g` flag names a group; without it, a user. Match principals by name
  against the snapshot files.
- `OWNER@` applies to the user who owns the object (see the manifest).
- `GROUP@` applies to any user whose groups include the object's group.
- `EVERYONE@` applies to every user — including the object's owner and
  the object's group members.
- Review requests are evaluated for the named user alone; no request in
  this review is made by `root` or carries elevated privilege.

## 4. ACL entries

Entries follow the `nfs4_acl(5)` client notation `type:flags:principal:permissions`.

- `type` — `A` grants the listed permission bits; `D` denies them.
- `flags` — `g`: principal is a group; `f`/`d`: the entry propagates to
  newly created files/subdirectories; `i`: inherit-only — the entry takes
  part only in that propagation and is **not** part of the object's own
  access control.
- `permissions` — permission bits, drawn from:

| bit | on a file | on a directory |
|-----|-----------|----------------|
| `r` | read data | list entries |
| `w` | write data | add a file |
| `a` | extend data | add a subdirectory |
| `x` | execute | traverse (lookup) |
| `d` | delete self | delete self |
| `D` | — | delete a child |
| `t` / `T` | read / write attributes | read / write attributes |
| `n` / `N` | read / write named attributes | read / write named attributes |
| `c` / `C` | read / write the ACL | read / write the ACL |
| `o` | change owner | change owner |
| `y` | synchronize | synchronize |

## 5. Operations under review

| operation | target | filer must grant on the target |
|-----------|--------|-------------------------------|
| `read` | file | `r` |
| `modify` | file | `w` |
| `readwrite` | file | `r` and `w` |
| `list` | directory | `r` |
| `create` | directory | `w` |

Reaching the target also requires traverse access: the filer must grant
the user `x` on **every ancestor directory** of the target path (each
directory strictly above the target, from `/export` down to the target's
parent).

## 6. Decision rule

A row's decision is `PERMIT` when the filer, enforcing the captured ACLs
under NFSv4 semantics (RFC 8881), would grant the user every permission
bit the operation requires on the target object, and would grant `x` on
every ancestor directory of the target. Otherwise the decision is `DENY`.

## 7. Report format

The finished report is a CSV with the exact header
`row_id,user,path,operation,decision` and one line per request, rows
`R0001` through `R0240` in ascending `row_id`, LF line endings, no
quoting. Every decision is `PERMIT` or `DENY`. Rows that already carry a
decision in `access_review_partial.csv` were completed and issued when
the tool stopped; the finished report reproduces those lines unchanged,
byte for byte. Rows with an empty decision are completed per §6.
