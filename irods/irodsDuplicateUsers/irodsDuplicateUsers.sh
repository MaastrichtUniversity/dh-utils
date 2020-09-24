#!/usr/bin/env bash

### Comments after review of DHS-620 ###
# These open issues should be looked into when leveraging this script to production in a subsequent story
# TODO: Test scalability and performance of this script on a production database. See if iRODS can cope with a large amount of 'changeProjectPermissions' rules in the delay queue.


DRY_RUN=true
MAPPING_FILE='users.txt'

while getopts ":m:f:d:u:n:" opt; do
  case $opt in
    m)
      echo "-m was triggered with $OPTARG" >&2
      MODE=${OPTARG}
      echo "MODE is $MODE" >&2
      ;;
    f)
      echo "-f was triggered with $OPTARG" >&2
      MAPPING_FILE=${OPTARG}
      echo "MAPPING_FILE is $MAPPING_FILE" >&2
      ;;
    d)
      echo "-d was triggered with $OPTARG" >&2
      DRY_RUN=${OPTARG}
      echo "DRY_RUN is $DRY_RUN" >&2
      ;;
    u)
      echo "-u was triggered with $OPTARG" >&2
      USERNAME=${OPTARG}
      echo "USERNAME is $USERNAME" >&2
      ;;
    n)
      echo "-n was triggered with $OPTARG" >&2
      NEW_USER=${OPTARG}
      echo "NEW_USER is $NEW_USER" >&2
      ;;

    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
    *)
      echo "No arguments given exiting" >&2
      exit 1
      ;;
  esac
done

if [ $OPTIND -eq 1 ];
 then
   echo "No options were passed";
   exit 1
fi

declare -A USER_NAME_MAP

if [ $MODE == "file" ]; then
   echo "duplicating all users found in $MAPPING_FILE, dry-run=$DRY_RUN"
   echo ""
   echo "reading in mapping-file..."
   while read current_name new_name; do
     #echo "  - $current_name $new_name"
     USER_NAME_MAP["$current_name"]="$new_name"
   done < <(grep -v "^;" $MAPPING_FILE)
elif [ $MODE == "user" ] ; then
   echo "duplicating single user $USERNAME to $NEW_USER , dry-run=$DRY_RUN"
   USER_NAME_MAP["$USERNAME"]="$NEW_USER"
else
   echo "no valid option provided for mode. exiting..."
   exit 1
fi

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
         [[ $DRY_RUN == "false" ]] && iadmin mkuser $newUserName rodsuser
         iuserinfo $user | grep "member of group" | cut -d " " -f 4 | while read -r group ; do
           # Skip adding the new user to the groups 'public' and his homegroup, as that is done automatically upon user creation.
           #For the conditional below, we need to append the zone to the group, because the username of 'iadmin lu' contains the zone as well.
           if [[ "$group#nlmumc" != "$user" && "$group" != "public" ]]; then
             [[ $DRY_RUN == "false" ]] && iadmin atg "$group" "$newUserName"
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
    [[ $DRY_RUN == "false" ]] && irule "changeProjectPermissions(*project, '$permissionsString')" *project="$projectName" ruleExecOut
    echo "irule \"changeProjectPermissions(*project, '$permissionsString')\" *project=\"$projectName\" ruleExecOut"
done

