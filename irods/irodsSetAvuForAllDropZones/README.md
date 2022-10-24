# irodsSetAvuForAllDropZones

* **Name:** irodsSetAvuForAllDropZones
* **Description**: Sets a specified AVU for ~~all~~ mounted iRODS dropzone in DataHub
* **Developer:** Jonathan Mélius, DataHub Maastricht University
* **License:** ?
* **Depends on:** Python 2.7 or 3 & iRODS icommands

# Usage of mounted drop-zones only
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.
2. **[DRY-RUN]** Test the script and review the output with (it only performs an `ils` to check the arguments):

    `python irodsSetAvuForAllDropZones.py --mounted --attribute legacy --value false`
3. **[COMMIT]** Execute the changes with:

    `python irodsSetAvuForAllDropZones.py --commit --mounted --attribute legacy --value false`

