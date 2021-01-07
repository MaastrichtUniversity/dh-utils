# irodsMigrateUserRole

* **Name:** irodsMigrateUserRole
* **Description**: Based on a mapping file, this script applies the same role (PI, Data steward )
    as the old user had.
* **Developer:** Jonathan Mélius, based on irodsMigratePermissions
* **License:** Apache
* **Depends on:** iRODS icommands

# Usage
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.

2. Create a mapping file _mapping.txt_, containing a mapping of `current username` to `new user name` (space separated). 
   ```
   j.thiede1 jthiede
   p.vanschayck2 pvanschayc
   ```

3. Call the script with the following parameters:
   ```
    ./irodsMigrateUserRole.sh
    
    -m 
    Choose the mode in which the scipt works 
    file for file mode. Use input file for mapping
    user for single user mode. Use single user as input for mapping
    
    -f 
    Choose the mapping file. To use with the file mode
    defaults to mapping.txt
    
    -d 
    Choose to use dry-run or not. Options are true or false
    defaults to true
    
    -u 
    Choose the input username that will be duplicated. To use with the user mode
    
    -n 
    Choose the new username. To use with the user mode

   ```
   
   Examples
   ```
    ./irodsMigrateUserRole.sh -m "file" 
    ./irodsMigrateUserRole.sh -m "file" -f "mapping.txt" 
    ./irodsMigrateUserRole.sh -m "file" -f "mapping.txt" -d "false"
    
    ./irodsMigrateUserRole.sh -m "user" -u "m.coonen@maastrichtuniversity.nl" -n "mcoonen"
    ./irodsMigrateUserRole.sh -m "user" -u "m.coonen@maastrichtuniversity.nl" -n "mcoonen" -d "false" 
   ```
5. For each old username, look if it matches as a PI or a data steward project AVU and replace it with the new username.


