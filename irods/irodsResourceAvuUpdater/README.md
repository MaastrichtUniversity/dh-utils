# irodsResourceAvuUpdater

* **Name:** irodsResourceAvuUpdater
* **Description**: Updates AVUs for `ingestResource` and `resource` on iRODS projects in DataHub
* **Developer:** Maarten Coonen, DataHub Maastricht University
* **License:** ?
* **Depends on:** iRODS icommands

# Usage
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.
1. Edit the _irodsResourceAvuUpdater.sh_ script and indicate the proper values for the old and new resource. Examples are: 
    ```
    oldIngestResource='iresResource'
    newIngestResource='ires-centosResource'
    oldResource='replRescUM01'
    newResource='replRescAZM01'
    ```
1. **[DRY-RUN]** Test the script and review the output with
    `./irodsResourceAvuUpdater.sh`
1. **[COMMIT]** Execute the changes with
    `./irodsResourceAvuUpdater.sh --commit`

