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

3. Call the script with the optional parameters:
   ```
   ./irodsDuplicateUsers.sh [file] [dryrun] 
   ```
   
   * file is the generated txt-file (defaults to users.txt)
   * dryrun is a boolean (defaults to true)
   
   ```
   e.g.: 
     ./irodsDuplicateUsers.sh
     ./irodsDuplicateUsers.sh users.txt true   
   ```
3. The new users will be created, having the same group memberships as the old users.

4. All project collections will be traversed, for each collection changeProjectPermissions.r is called,
   with the new usernames and the corresponding access rights of the old users.


