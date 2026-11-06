# irodsRestoreDeletedUserPermissions

Restore project ACLs from a deleted user's JSON permissions backup to an existing
iRODS username. Uses Python 3.8+ and iCommands; no additional Python packages.

Initialize iCommands with `iinit` using a **rodsadmin** account and check the
intended environment with `ienv`. The target user must already exist. All changes
use `ichmod -M` (admin mode).

From this directory, preview the supplied backup:

```bash
python3 restore_deleted_user_permissions.py user_permissions_syang2_20261106.json NEW_USERNAME --dry-run
```

Apply the permissions by omitting `--dry-run`:

```bash
python3 restore_deleted_user_permissions.py user_permissions_syang2_20261106.json NEW_USERNAME
```

The backup must be a JSON list, for example:

```json
[
  {
    "project": "/nlmumc/projects/P000000473",
    "username": "syang2",
    "user_id": "47346486",
    "access": "modify_object"
  }
]
```

The supplied target username is used for every entry; the backup's `username` and
`user_id` are ignored. A zone-qualified target such as `alice#nlmumc` is accepted.

| Saved access | Commands for each project |
| --- | --- |
| `read`, `read_object`, `read object` | `ichmod -M -r read USER PROJECT` |
| `modify`, `modify_object`, `modify object`, `write` | `ichmod -M -r read USER PROJECT`, then `ichmod -M write USER PROJECT` |
| `own` | `ichmod -M -r read USER PROJECT`, then `ichmod -M own USER PROJECT` |

Recursive read applies to the project, all subcollections, and all data objects.
Write or own is then applied only to the project root. These commands set the
target user's explicit ACLs, replacing any existing ACL for that user on those
paths, including higher access on descendants. Effective access through group
membership may still be higher. Collection inheritance settings are unchanged.
See the [official ichmod source and command help](https://github.com/irods/irods_client_icommands/blob/main/src/ichmod.cpp)
for the recursive flag, admin mode, and read/write aliases.

The complete input is validated before any commands run. Project paths must have
the form `/<zone>/projects/<project>`. Unsupported access levels and conflicting
entries for the same project are rejected; identical entries are applied once.
An empty list succeeds without invoking iCommands. Dry-run only reads the local
JSON and prints commands; it does not verify server connectivity or user existence.

Execution stops on the first failed command and exits with status `1`. Earlier
changes, including partial recursive changes, are not rolled back. Successful
runs exit `0`; invalid command-line arguments exit `2`.

Run the offline tests:

```bash
python3 -m unittest -v test_restore_deleted_user_permissions
```

Tests mock all iCommands calls and do not change live permissions.
