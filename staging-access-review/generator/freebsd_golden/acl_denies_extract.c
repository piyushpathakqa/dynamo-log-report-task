/*
 * Return 0, iff access is allowed, 1 otherwise.
 */
static int
_acl_denies(const struct acl *aclp, int access_mask, struct ucred *cred,
    int file_uid, int file_gid, int *denied_explicitly)
{
	int i;
	const struct acl_entry *entry;

	if (denied_explicitly != NULL)
		*denied_explicitly = 0;

	KASSERT(aclp->acl_cnt <= ACL_MAX_ENTRIES,
	    ("aclp->acl_cnt <= ACL_MAX_ENTRIES"));

	for (i = 0; i < aclp->acl_cnt; i++) {
		entry = &(aclp->acl_entry[i]);

		if (entry->ae_entry_type != ACL_ENTRY_TYPE_ALLOW &&
		    entry->ae_entry_type != ACL_ENTRY_TYPE_DENY)
			continue;
		if (entry->ae_flags & ACL_ENTRY_INHERIT_ONLY)
			continue;
		switch (entry->ae_tag) {
		case ACL_USER_OBJ:
			if (file_uid != cred->cr_uid)
				continue;
			break;
		case ACL_USER:
			if (entry->ae_id != cred->cr_uid)
				continue;
			break;
		case ACL_GROUP_OBJ:
			if (!groupmember(file_gid, cred))
				continue;
			break;
		case ACL_GROUP:
			if (!groupmember(entry->ae_id, cred))
				continue;
			break;
		default:
			KASSERT(entry->ae_tag == ACL_EVERYONE,
			    ("entry->ae_tag == ACL_EVERYONE"));
		}

		if (entry->ae_entry_type == ACL_ENTRY_TYPE_DENY) {
			if (entry->ae_perm & access_mask) {
				if (denied_explicitly != NULL)
					*denied_explicitly = 1;
				return (1);
			}
		}

		access_mask &= ~(entry->ae_perm);
		if (access_mask == 0)
			return (0);
	}

	if (access_mask == 0)
		return (0);

	return (1);
}
