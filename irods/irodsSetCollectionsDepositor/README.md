# irodsSetCollectionsDepositor

* **Name:** irodsSetCollectionsDepositor
* **Description**: Loop over all existing project collections and set the depositor as the creator username
* **Developer:** Jonathan Mélius, DataHub Maastricht University
* **License:** ?
* **Depends on:** iRODS icommands


# Usage
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.
2. **[DRY-RUN]** Test the script and review the output with
    `./irodsSetCollectionsDepositor.sh`
3. **[COMMIT]** Execute the changes with
    `./irodsSetCollectionsDepositor.sh --commit`
