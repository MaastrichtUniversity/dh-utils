# irodsCheckInactiveUser

* **Name:** irodsCheckInactiveUser
* **Description**: Based on the given input user, this script checks if the inactive user is safe for deletion:
    * is not a Data Steward for any projects
    * is not a Principal Investigator for any projects
    * is not the last manager of any projects
    * does not have any open dropzone  
    If the inactive user is safe for deletion, generate a backup csv with its permissions.
* **Developer:** Jonathan Mélius, based on irodsMigrateUserRole
* **License:** Apache
* **Depends on:** iRODS icommands

# Usage
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.

2. Call the script with the following parameters:
   ```
    ./irodsCheckInactiveUser.sh
    
    -d 
    Choose to use dry-run or not. Options are true or false
    defaults to true
    
    -u 
    Choose the input username that will be duplicated. To use with the user mode
   ```
   
   Examples
   ```
    ./irodsCheckInactiveUser.sh -u "opalmen"
    ./irodsCheckInactiveUser.sh -u "pvanschay2"  -d "false"
   ```
