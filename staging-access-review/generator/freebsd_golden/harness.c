/*
 * Author-side external-golden harness (never shipped in the task image).
 *
 * Wraps FreeBSD's _acl_denies() — the kernel's NFSv4 ACL access-check
 * evaluator from sys/kern/subr_acl_nfs4.c, extracted VERBATIM into
 * acl_denies_extract.c — with just enough userland shims to compile.
 * The generator feeds every elementary access check through this binary
 * and asserts bit-for-bit agreement with the Python golden.
 *
 * Input (stdin), one check per line, all fields decimal:
 *   file_uid file_gid access_mask ngroups g1..gN nace \
 *     tag,id,perm,type,flags ... (nace times)
 * Output: one line per check: "0" (allowed) or "1" (denied).
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>

/* --- constants from FreeBSD sys/sys/acl.h (values copied exactly) --- */
#define ACL_MAX_ENTRIES            254

#define ACL_USER_OBJ               0x00000001
#define ACL_USER                   0x00000002
#define ACL_GROUP_OBJ              0x00000004
#define ACL_GROUP                  0x00000008
#define ACL_EVERYONE               0x00000040

#define ACL_ENTRY_TYPE_ALLOW       0x0100
#define ACL_ENTRY_TYPE_DENY        0x0200

#define ACL_ENTRY_INHERIT_ONLY     0x0008

/* --- minimal struct shims (field names match the kernel usage) --- */
struct acl_entry {
	int  ae_tag;
	int  ae_id;
	int  ae_perm;
	int  ae_entry_type;
	int  ae_flags;
};

struct acl {
	int acl_cnt;
	struct acl_entry acl_entry[ACL_MAX_ENTRIES];
};

#define MAX_GROUPS 64
struct ucred {
	uid_t cr_uid;
	int   cr_ngroups;
	gid_t cr_groups[MAX_GROUPS];
};

/* FreeBSD's groupmember(): is gid among the cred's groups (incl. egid)? */
static int
groupmember(gid_t gid, struct ucred *cred)
{
	int i;

	for (i = 0; i < cred->cr_ngroups; i++) {
		if (cred->cr_groups[i] == gid)
			return (1);
	}
	return (0);
}

#define KASSERT(exp, msg) \
	do { if (!(exp)) { fprintf(stderr, "KASSERT failed\n"); exit(2); } } while (0)

/* The kernel evaluator, verbatim. */
#include "acl_denies_extract.c"

int
main(void)
{
	char line[65536];

	while (fgets(line, sizeof(line), stdin) != NULL) {
		char *p = line;
		char *tok;
		struct ucred cred;
		struct acl acl;
		int file_uid, file_gid, access_mask, nace, i;

		memset(&cred, 0, sizeof(cred));
		memset(&acl, 0, sizeof(acl));

		tok = strtok(p, " \t\n"); if (tok == NULL) continue;
		file_uid = atoi(tok);
		tok = strtok(NULL, " \t\n"); file_gid = atoi(tok);
		tok = strtok(NULL, " \t\n"); access_mask = atoi(tok);
		tok = strtok(NULL, " \t\n"); cred.cr_ngroups = atoi(tok);
		if (cred.cr_ngroups > MAX_GROUPS) { fprintf(stderr, "too many groups\n"); exit(2); }
		for (i = 0; i < cred.cr_ngroups; i++) {
			tok = strtok(NULL, " \t\n");
			cred.cr_groups[i] = (gid_t)atoi(tok);
		}
		/* cr_uid comes after groups on the line for parsing simplicity */
		tok = strtok(NULL, " \t\n"); cred.cr_uid = (uid_t)atoi(tok);
		tok = strtok(NULL, " \t\n"); nace = atoi(tok);
		if (nace > ACL_MAX_ENTRIES) { fprintf(stderr, "too many aces\n"); exit(2); }
		acl.acl_cnt = nace;
		for (i = 0; i < nace; i++) {
			tok = strtok(NULL, " \t\n");
			if (sscanf(tok, "%d,%d,%d,%d,%d",
			    &acl.acl_entry[i].ae_tag, &acl.acl_entry[i].ae_id,
			    &acl.acl_entry[i].ae_perm, &acl.acl_entry[i].ae_entry_type,
			    &acl.acl_entry[i].ae_flags) != 5) {
				fprintf(stderr, "bad ace token\n"); exit(2);
			}
		}
		printf("%d\n", _acl_denies(&acl, access_mask, &cred,
		    file_uid, file_gid, NULL));
	}
	return (0);
}
