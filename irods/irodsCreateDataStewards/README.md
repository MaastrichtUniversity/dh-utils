# irodsCreateDataStewards

* **Name:** irodsRemoveAvuFromProjects
* **Description**: Retrospectively set the data steward AVU to all projects, add data steward(s) with OWN permission to all his/her projects. Also set data-steward AVU to data stewards iRODS users.
* **Developer:** Jonathan Mélius, DataHub Maastricht University
* **License:** ?
* **Depends on:** iRODS icommands

# Usage
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.
1. The script take as input a DataStewards.csv file. The csv file must contain 3 columns comma separated:
		- the project full path
		- the principal investigator user name
		- the data steward user name 
    Lines examples: 
    ```
    /nlmumc/projects/P000000010,x.y@maastrichtuniversity.nl,y.z@maastrichtuniversity.nl 
    /nlmumc/projects/P000000011,a.b@maastrichtuniversity.nl,c.d@maastrichtuniversity.nl
    ```
1. **[DRY-RUN]** Test the script and review the output with
    `./irodsCreateDataStewards.sh --dry-run DataStewards.csv`
1. **[COMMIT]** Execute the changes with
    `./irodsCreateDataStewards.sh --commit DataStewards.csv`

