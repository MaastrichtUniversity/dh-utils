# irodsMigratePermissions

* **Name:** irodsMigratePermissions
* **Description**: Based on a mapping file, this script applies the same project permissions (ACLs) 
    as the old user or group had.
* **Developer:** Jan-Erek Thiede, Paul van Schayck, Daniel Theunissen
* **License:** Apache
* **Depends on:** iRODS icommands

# Usage
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.

2. Create a mapping file _mapping.txt_, containing a mapping of `current username` to `new user name` (space separated). Be aware 
   that the current username has to be in the format `user#zone`. Please find an example file below:
   ```
   j.thiede@maastrichtuniversity.nl#nlmumc	jthiede
   p.vanschayck@maastrichtuniversity#nlmumc pvanschayc
   ```

   You can create this file by using this two commands and then modify _mapping.txt_ as wished:
   ```
   iadmin lu | grep -v "@" | sort | sed -r 's/(\S+)/\1\t\1/g' > mapping.txt
   iadmin lu | grep "@" | sort | sed -r 's/(\S+)/\1\t\1/g' >> mapping.txt
   iadmin lg >> mapping.txt
   # The first command will show special users, those should probably be removed from the file!)
   # The last command will also add all groups
   ```

3. Call the script with the following parameters:
   ```
    ./irodsMigratePermissions.sh
    
    -m 
    Choose the mode in which the scipt works 
    file for file mode. Use input file for mapping
    user for single user mode. Use single user/group as input for mapping
    
    -f 
    Choose the mapping file. To use with the file mode
    defaults to users.txt
    
    -d 
    Choose to use dry-run or not. Options are true or false
    defaults to true
    
    -u 
    Choose the input username/groupname that will be duplicated. To use with the user mode
    
    -n 
    Choose the new username/groupname. To use with the user mode

   ```
   
   Examples
   ```
    ./irodsMigratePermissions.sh -m "file" 
    ./irodsMigratePermissions.sh -m "file" -f "mapping.txt" 
    ./irodsMigratePermissions.sh -m "file" -f "mapping.txt" -d "false"
    
    ./irodsMigratePermissions.sh -m "user" -u "m.coonen@maastrichtuniversity.nl#nlmumc" -n "mcoonen"
    ./irodsMigratePermissions.sh -m "user" -u "m.coonen@maastrichtuniversity.nl#nlmumc" -n "mcoonen" -d "false" 
   ```
5. All project collections will be traversed, for each collection changeProjectPermissions.r is called,
   with the new usernames/groupnames and the corresponding access rights of the old users or groups.


