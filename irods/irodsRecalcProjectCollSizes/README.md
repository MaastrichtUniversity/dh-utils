# irodsRecalcProjectCollSizes

* **Name:** irodsRecalcProjectCollSizes
* **Description**: Recalculate the byteSizes and numFiles for all iRODS project collections in DataHub
* **Developer:** Maarten Coonen, DataHub Maastricht University
* **License:** ?
* **Depends on:** 
    * iRODS icommands
    * [irods-ruleset](https://github.com/MaastrichtUniversity/irods-ruleset), v3.2.0 or higher
 

# Usage
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.
1. Edit the _irodsRecalcProjectCollSizes.sh_ script and indicate the proper values for the old and new resource. Examples are: 
    ```
    projectsRoot='/nlmumc/projects/'
    ```
1. **[DRY-RUN]** There is no actual dry-run. Command below will just print instructions.
    `./irodsRecalcProjectCollSizes.sh`

1. **[COMMIT]** Execute the changes with
    `./irodsRecalcProjectCollSizes.sh --commit`

1. **Progress and outcome** Progress can be monitored in stdout. Details in rodsLog. Look for these entries:
    ```
    Aug  2 15:04:24 pid:3234 NOTICE: msiWriteRodsLog message: setCollectionSize: Starting for /nlmumc/projects/P000000010/C000000001
    Aug  2 15:04:24 pid:3234 NOTICE: msiWriteRodsLog message: setCollectionSize: Removing pre-existing AVU dcat:byteSize_resc_10002
    Aug  2 15:04:24 pid:3234 NOTICE: msiWriteRodsLog message: setCollectionSize: Removing pre-existing AVU dcat:byteSize_resc_10963
    Aug  2 15:04:24 pid:3234 NOTICE: msiWriteRodsLog message: setCollectionSize: Removing pre-existing AVU numFiles_resc_10002
    Aug  2 15:04:24 pid:3234 NOTICE: msiWriteRodsLog message: setCollectionSize: Removing pre-existing AVU numFiles_resc_10963
    Aug  2 15:04:24 pid:3234 NOTICE: chlSetAVUMetadata found metaId 63117
    Aug  2 15:04:24 pid:3234 NOTICE: chlSetAVUMetadata found metaId 84560
    Aug  2 15:04:24 pid:3234 NOTICE: msiWriteRodsLog message: setCollectionSize: Finished for /nlmumc/projects/P000000010/C000000001
    ```

