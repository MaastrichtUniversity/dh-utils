# irodsSetAvuForAllProjects

* **Name:** irodsSetAvuForAllDropZones
* **Description**: Sets a specified AVU for all iRODS dropzone in DataHub
* **Developer:** Jonathan Mélius, DataHub Maastricht University
* **License:** ?
* **Depends on:** Python 2.7 or 3 & iRODS icommands

# Usage
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.
2. **[DRY-RUN]** Test the script and review the output with
    `python irodsSetAvuForAllDropZones.py -a legacy -v false`
3. **[COMMIT]** Execute the changes with
    `python irodsSetAvuForAllDropZones.py -c -a legacy -v false`

