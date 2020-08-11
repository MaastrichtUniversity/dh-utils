# irodsDuplicateUsers

* **Name:** irodsDuplicateUsers
* **Description**: duplicates all Users with a different name and the same ACLs
* **Developer:** Jan-Erek Thiede, DataHub Maastricht University
* **License:** ?
* **Depends on:** iRODS icommands

# Usage
1. Get a working _rodsadmin_ connection through `iinit` to iRODS server of choice.

2. create a mapping file users.json, containing a mapping of current-username to new user-name, be aware, the current username
   has to be in the formar user#zone:

   j.thiede@maastrichtuniversity.nl#nlmumc	j.thiede@maastrichtuniversity.datahub.sram.surf.nl
   p.vanschayck@maastrichtuniversity#nlmumc	p.vanschayck@maastrichtuniversity.datahub.sram.surf.nl

   You can create this file by using this two commands, and then modify users.txt as wished:

   iadmin lu | grep -v "@" | sort | sed -r 's/(\S+)/\1\t\1/g' > users.csv
   iadmin lu | grep "@" | sort | sed -r 's/(\S+)/\1\t\1/g' >> users.csv

   (The first command will show special users, those should probably be removed from the file!)

3. Call the skript with the optional parameters:

   . irodsDuplicateUsers.sh [file] [dryrun] 
  
   file is the generated csv-file (defaults to users.csv)
   dryrun is a boolean (defaults to true)

   e.g.: 
     irodsDuplicateUsers.sh
     irodsDuplicateUsers.sh users.csv true   

3. The new users will be created, having the same group memberships as the old users.

4. All project collection will be traversed, for each collection changeProjectPermissions.r is called,
   with the new usernames and the corresponding access rights of the old users


