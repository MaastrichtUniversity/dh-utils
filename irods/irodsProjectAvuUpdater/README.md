# irodsProjectAvuUpdater

* **Name:** irodsProjectAvuUpdater
* **Description**: Loops over iRODS projects and updates AVU of choice from old to new value
* **Developer:** Maarten Coonen, DataHub Maastricht University
* **License:** ?
* **Depends on:** iRODS icommands

# Usage
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.
1. Edit the `CONFIGURATION` section of _irodsProjectAvuUpdater.sh_ script to your liking. Examples: 
    ```
    # CONFIGURATION
    avuName='responsibleCostCenter'
    oldValue='UM-30001234X'
    newValue='UM-30005678X'
    ```
1. **[DRY-RUN]** Test the script and review the output with
    `./irodsProjectAvuUpdater.sh`
1. **[COMMIT]** Execute the changes with
    `./irodsProjectAvuUpdater.sh --commit`

