# irodsRemoveAvuFromProjects

* **Name:** irodsRemoveAvuFromProjects
* **Description**: Removes a specified AVU from all iRODS projects in DataHub
* **Developer:** Maarten Coonen, DataHub Maastricht University
* **License:** ?
* **Depends on:** iRODS icommands

# Usage
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.
1. Edit the _irodsRemoveAvuFromProjects.sh_ script and indicate the proper values for the old and new resource. Examples are: 
    ```
    AvuName='NCIT:C88193'
    projectsRoot='/nlmumc/projects/'
    ```
1. **[DRY-RUN]** Test the script and review the output with
    `./irodsRemoveAvuFromProjects.sh`
1. **[COMMIT]** Execute the changes with
    `./irodsRemoveAvuFromProjects.sh --commit`

