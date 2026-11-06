# irodsDeletePendingUsers

Delete iRODS users pending deletion in one batch, saving each user's current project
permissions before attempting deletion. This standalone utility uses an existing
iCommands connection; it does not require MDR, the rule wrapper, or a Python iRODS client.

## Requirements

- Python 3.8 or later; no additional Python packages.
- iRODS iCommands, with `irule` available on `PATH`.
- A working iCommands login to the intended iRODS environment. Live deletion
  requires the client username **`rods`**, as enforced by `delete_user`.
- The DataHub rules `get_all_users_pending_deletion`,
  `get_users_active_permissions`, and `delete_user` installed on the server,
  including the dependencies of `delete_user` (such as `check_user_is_deletable`)
  and the `test_rule_output` dispatcher used by `/rules/tests/run_test.sh`.
  The script uses `irods_rule_engine_plugin-irods_rule_language-instance`.

## Quick start

Initialize your iCommands connection if necessary, then check the active environment:

```bash
iinit
ienv
ils
```

Confirm that `ienv` shows the intended server, zone, and username `rods`.
From this utility's directory, preview the batch:

```bash
python3 delete_pending_users.py --dry-run --output-dir ./deletion-preview
```

Review the console output, log, and saved permissions. To run the deletion batch:

```bash
python3 delete_pending_users.py --output-dir ./deletion-report
```

**Omitting `--dry-run` attempts actual deletions without an additional prompt.**
Each invocation fetches the current pending-user list; a live run does not reuse
the list from an earlier preview.

## Options

| Option | Behavior |
| --- | --- |
| `--dry-run` | Save permissions and report “would attempt deletion”; never call `delete_user`. |
| `--output-dir PATH` | Store JSON files and the log here; create the directory if needed. Default: current directory. |
| `-h`, `--help` | Show command help and exit. |

Dry-run still contacts iRODS and writes local reports. It does **not** call deletion
eligibility checks and does not establish whether a live deletion will succeed.

## Processing and reports

Rules are invoked through `test_rule_output`, matching the examples at the top
of the Python rules and the commands issued by `/rules/tests/run_test.sh`:

```bash
irule -r irods_rule_engine_plugin-irods_rule_language-instance \
  'test_rule_output("get_all_users_pending_deletion", "")' null ruleExecOut
irule -r irods_rule_engine_plugin-irods_rule_language-instance \
  'test_rule_output("get_users_active_permissions", "alice")' null ruleExecOut
```

The dispatcher calls the Python rules and writes their JSON output. The utility
does not require the `run_test.sh` file locally. Because the dispatcher splits
arguments on commas, usernames containing commas are reported as failures and
skipped without attempting deletion.

The script calls `get_all_users_pending_deletion`, removes duplicate usernames,
and processes users sequentially. For each user it:

1. Calls `get_users_active_permissions`.
2. Saves the returned JSON permissions list and closes the file.
3. Calls `delete_user`, or reports the intended attempt in dry-run mode.

Nonempty permissions do not independently block a deletion attempt. The existing
server-side checks decide whether deletion is allowed, including the pending-deletion
flag, project responsibilities, remaining managers, and open dropzones.

Reports use one UTC timestamp per invocation, formatted as `YYYYMMDDTHHMMSSffffffZ`:

```text
deletion-report/
├── delete_pending_users_20261106T143012123456Z.log
├── user_permissions_alice_20261106T143012123456Z.json
└── user_permissions_bob_20261106T143012123456Z.json
```

Permissions files contain the rule's JSON list, for example:

```json
[
  {
    "project": "/nlmumc/projects/P000000001",
    "username": "alice",
    "user_id": "10001",
    "access": "read"
  }
]
```

Users without project permissions get an empty list (`[]`). Unusual username
characters are percent-encoded in filenames so they cannot introduce paths.
Existing report files are never overwritten.

The console and log include progress, individual failures, and final counts:

```text
Summary: pending=3, deleted=2, would_attempt=0, failures=1
Complete failure list:
user='alice', stage=delete_user: delete_user exited with status 4: ...
```

If fetching or parsing the pending-user list fails, no users are processed.
If reading or saving one user's permissions fails, that user's deletion is skipped.
If deletion fails, the saved permissions remain available. Per-user failures do not
stop other users from being processed. Failed deletion calls are not automatically
retried; a connection failure or invalid response can leave the outcome uncertain,
so check iRODS before manually retrying that user.

## Exit codes and troubleshooting

| Exit code | Meaning |
| --- | --- |
| `0` | All operations succeeded, including an empty pending list or a successful dry-run. |
| `1` | A connection, rule, response, or report-writing operation failed; review the console and log. |
| `2` | Invalid command-line arguments. |

- **`irule` not found:** install iCommands or add its executable directory to `PATH`.
- **Connection/authentication error:** inspect `ienv`, refresh credentials with `iinit`,
  and verify access with `ils`.
- **Rule not found:** verify the DataHub rules, `test_rule_output` dispatcher, and the named
  rule-engine instance are installed. Compare with `/rules/tests/run_test.sh -r get_all_users_pending_deletion -j`.
- **Only callable by RODS:** initialize a connection with client username `rods`.
- **User not valid for deletion:** review the server's eligibility checks; the script does not bypass them.
- **Invalid JSON:** inspect the logged response and verify the installed rule's output.
- **Cannot save permissions or initialize reports:** check the output directory's permissions and free space.
  A user is never deleted after a failed permissions save.

## Offline tests

From this directory:

```bash
python3 -m unittest -v test_delete_pending_users
```

All `irule` invocations are mocked. Tests do not require a server or credentials
and perform no live deletions.
