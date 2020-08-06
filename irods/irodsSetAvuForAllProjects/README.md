# irodsSetAvuForAllProjects

* **Name:** irodsSetAvuForAllProjects
* **Description**: Sets a specified AVU for all iRODS projects in DataHub
* **Developer:** Jonathan Mélius, DataHub Maastricht University
* **License:** ?
* **Depends on:** iRODS icommands

# Usage
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.
2. **[DRY-RUN]** Test the script and review the output with
    `../irodsSetAvuForAllProjects.sh --dry-run archiveDestinationResource arcRescSURF01`
3. **[COMMIT]** Execute the changes with
    `../irodsSetAvuForAllProjects.sh --commit archiveDestinationResource arcRescSURF01`

