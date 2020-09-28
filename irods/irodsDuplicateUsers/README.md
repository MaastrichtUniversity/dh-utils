# irodsDuplicateUsers

* **Name:** irodsDuplicateUsers
* **Description**: Based on a mapping file, this script creates new users and applies the same project permissions (ACLs) as the old user had.
* **Developer:** Jan-Erek Thiede, DataHub Maastricht University
* **License:** ?
* **Depends on:** iRODS icommands

# Usage
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.

2. Create a mapping file _users.txt_, containing a mapping of `current username` to `new user name` (space separated). Be aware 
   that the current username has to be in the format `user#zone`. Please find an example file below:
   ```
   j.thiede@maastrichtuniversity.nl#nlmumc	j.thiede@maastrichtuniversity.datahub.sram.surf.nl
   p.vanschayck@maastrichtuniversity#nlmumc p.vanschayck@maastrichtuniversity.datahub.sram.surf.nl
   ```

   You can create this file by using this two commands and then modify _users.txt_ as wished:
   ```
   iadmin lu | grep -v "@" | sort | sed -r 's/(\S+)/\1\t\1/g' > users.txt
   iadmin lu | grep "@" | sort | sed -r 's/(\S+)/\1\t\1/g' >> users.txt
   # The first command will show special users, those should probably be removed from the file!)
   ```

3. Call the script with the following parameters:
   ```
    ./irodsDuplicateUsers.sh
    
    -m 
    Choose the mode in which the scipt works 
    file for file mode. Use input file for mapping
    user for single user mode. Use single user as input for mapping
    
    -f 
    Choose the mapping file. To use with the file mode
    defaults to users.txt
    
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
    ./irodsDuplicateUsers.sh -m "file" 
    ./irodsDuplicateUsers.sh -m "file" -f "users.txt" 
    ./irodsDuplicateUsers.sh -m "file" -f "users.txt" -d "false"
    
    ./irodsDuplicateUsers.sh -m "user" -u "m.coonen@maastrichtuniversity.nl#nlmumc" -n "m.coonen@maastrichtuniversity.datahub.sram.surf.nl"
    ./irodsDuplicateUsers.sh -m "user" -u "m.coonen@maastrichtuniversity.nl#nlmumc" -n "m.coonen@maastrichtuniversity.datahub.sram.surf.nl" -d "false" 
   ```
4. The new users will be created, having the same group memberships as the old users.

5. All project collections will be traversed, for each collection changeProjectPermissions.r is called,
   with the new usernames and the corresponding access rights of the old users.


