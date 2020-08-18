#!/usr/bin/env bash

### Comments after review of DHS-620 ###
# These open issues should be looked into when leveraging this script to production in a subsequent story
# TODO: Check if the script accepts a tab- (instead of space-)separated users.txt file as input. I assume that in production, we will create this input file using a spreadsheet application and save it as tab delimited.
# TODO: Call 'changeProjectPermissions' from the rulebase instead of the file in /rules/... This makes development easier as you are able to run it outside of the irods container. Otherwise, mention this dependency (/rules folder) in this script's README.
# TODO: Test scalability and performance of this script on a production database. See if iRODS can cope with a large amount of 'changeProjectPermissions' rules in the delay queue.

MAPPING_FILE='users.txt'
DRY_RUN=true

[[ "$#" -ge 1 ]] && MAPPING_FILE=$1
[[ "$#" -ge 2 ]] && DRY_RUN=$2

echo "duplicating all users found in $MAPPING_FILE, dry-run=$DRY_RUN"
echo ""
echo "reading in mapping-file..."
#assoziativ array of user ids to old and new name, could be loaded from file
declare -A USER_NAME_MAP
#USER_NAME_MAP=( ['g.tria@maastrichtuniversity.nl#nlmumc']="g.tria@DUPLICATE.sram" ['jonathan.melius@maastrichtuniversity.nl#nlmumc']="jonathan.melius@DUPLICATE.sram" )
while read current_name new_name; do
  #echo "  - $current_name $new_name"
  USER_NAME_MAP["$current_name"]="$new_name"
done < <(grep -v "^;" $MAPPING_FILE)

##debug line: shows content of the assoziative array
##for x in "${!USER_NAME_MAP[@]}"; do printf "[%q]=%q\n" "$x" "${USER_NAME_MAP[$x]}" ; done

#second assoziative array, needed because iquest on collections won't give us the user name for an ACL...
declare -A USER_ID_MAP
echo "-----------------"


echo "Create new users with same group memberships..."

# Looping over all existing users: check if the user should be duplicated
for user in $(iadmin lu)
do
   userId=$(iadmin lu $user | grep "user_id" | cut -d " " -f 2)
#   echo "   existing user: $user  -> $userId"
   if [ ${USER_NAME_MAP["$user"]+_} ]; then
      # Create the new users, and add it to the same groups
      newUserName=${USER_NAME_MAP["$user"]}
      USER_ID_MAP[$userId]="$user"
      #check if user already exists!
      #the output "No rows found" is expected and shows the new user can be safely created!
      if iadmin lu $newUserName | grep 'No rows found'; then
         echo " * iadmin mkuser $newUserName rodsuser"
         #could still fail, if there is still a home collection for the user!
         [[ !DRY_RUN ]] iadmin mkuser $newUserName rodsuser
         iuserinfo $user | grep "member of group" | cut -d " " -f 4 | while read -r group ; do
           # Skip adding the new user to the groups 'public' and his homegroup, as that is done automatically upon user creation.
           #For the conditional below, we need to append the zone to the group, because the username of 'iadmin lu' contains the zone as well.
           if [[ "$group#nlmumc" != "$user" && "$group" != "public" ]]; then
             [[ !DRY_RUN ]] && iadmin atg "$group" "$newUserName"
             echo " ** iadmin atg $group $newUserName"
           fi
         done
      fi
   fi
done

#echo ""
#echo "mapping of old userIds to userNames (for duplicated users):"
#for x in "${!USER_ID_MAP[@]}"; do printf "[%q]=%q\n" "$x" "${USER_ID_MAP[$x]}" ; done
echo "-----------------"



# Looping over all projects: run the changePermissions rule for the new users
echo "Granting user permissions for new users on all projects..."
for project in  $(iquest "select COLL_NAME where COLL_PARENT_NAME = '/nlmumc/projects'" | grep "COLL_NAME" | cut -d" " -f 3)
do 
   projectName=${project##*/}
   echo " * Project: $project   $projectName"
   permissionsString=""
   #{ iquest "select COLL_NAME, COLL_ACCESS_USER_ID, COLL_ACCESS_NAME where COLL_NAME = '$project'"  | while mapfile -t -n 4 blocks && ((${#blocks[@]}));} do
   while  mapfile -t -n 4 blocks && ((${#blocks[@]})); 
   do
      collection=${blocks[0]##* = }
      userId=${blocks[1]##* = }
      accessName=${blocks[2]##* = }
      [[ "$accessName" == "modify object" ]] && accessName="write" 
      [[ "$accessName" == "read object" ]] && accessName="read"

      if [ ${USER_ID_MAP[$userId]+_} ]; then
         oldUserName=${USER_ID_MAP[$userId]}
         newUserName=${USER_NAME_MAP[$oldUserName]}
#        ichmod -M "${accessName}" "$newUserName" "$collection"
         echo " ** $newUserName $accessName"
         permissionsString+="$newUserName:$accessName "
      else
         :
      fi
   done< <(iquest "select COLL_NAME, COLL_ACCESS_USER_ID, COLL_ACCESS_NAME where COLL_NAME = '$project'" )
   [[ !DRY_RUN ]] && irule -s -F /rules/projects/changeProjectPermissions.r *project="$projectName" *users="$permissionsString"
   echo "  irule -s -F /rules/projects/changeProjectPermissions.r *project=\"$projectName\" *users=\"$permissionsString\""
done 


