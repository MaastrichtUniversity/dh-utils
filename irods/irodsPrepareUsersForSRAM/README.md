# irodsPrepareUsersForSRAM

* **Name:** irodsPrepareUsersForSRAM
* **Description**: Prepare existing iRODS users for the use of SRAM. Add the  not-sync AVU to existing service accounts and existing user accounts 
* **Developer:** Daniel Theunissen, DataHub Maastricht University
* **License:** ?
* **Depends on:** iRODS icommands

# Usage
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.
1. **[DRY-RUN]** Test the script and review the output with
    `./irodsPrepareUsersForSRAM.sh`
1. **[COMMIT]** Execute the changes with
    `./irodsPrepareUsersForSRAM.sh --commit`
