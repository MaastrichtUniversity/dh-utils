# irodsStoragePriceAvuUpdater

* **Name:** irodsStoragePriceAvuUpdater
* **Description**: Updates value for Storage Price (quotation) AVU on iRODS projects in DataHub
* **Developer:** Maarten Coonen, DataHub Maastricht University
* **License:** ?
* **Depends on:** iRODS icommands

# What this script does
1. Select all projects in iRODS that are stored on the specified **resourceName** AND have a storage price equal to **AvuOldValue**
2. Update the storage price AVU for these projects to the value of **AvuNewValue** 

# Usage
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.
1. Edit the _irodsStoragePriceAvuUpdater.sh_ script and indicate the proper values for the variables (with examples) below: 
    ```
    resourceName='replRescUM01'
    AvuName='NCIT:C88193'
    AvuOldValue='0.32'
    AvuNewValue='0.189'
    ```
1. **[DRY-RUN]** Test the script and review the output with
    `./irodsStoragePriceAvuUpdater.sh`
1. **[COMMIT]** Execute the changes with
    `./irodsStoragePriceAvuUpdater.sh --commit`

