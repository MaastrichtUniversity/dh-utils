# irodsCustomPermissionUpdater

* **Name:** irodsCustomPermissionUpdater
* **Description**: Updates permissions in bulk for certain files in an iRODS collection
* **Developer:** Maarten Coonen, DataHub Maastricht University
* **License:** ?
* **Depends on:** iRODS icommands

# Usage
**Note** _In the current state, the script is quite hardcoded. For heavier usage, it should receive some refactoring._
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.
1. Edit the line that starts with `files=` to indicate which iRODS collection to scan and which files to select (i.e. `grep`)
1. Edit line 12 to indicate the permission level (read,write,own,null) and user or group to apply to. 
1. **[DRY-RUN]** Test the script and review the output with
    `./irodsCustomPermissionUpdater.sh`
1. **[COMMIT]** Execute the changes with
    `./irodsCustomPermissionUpdater.sh --commit`

