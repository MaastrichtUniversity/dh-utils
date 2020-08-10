#!/usr/bin/env bash

#echo "iterate through ALL Collections"
#ils -r / | grep "C-"  | cut -d " " -f 4 | while read -r collection_path ; do
#   echo "Collection: $collection_path"
#   ils -A "$collection_path" | grep "ACL" 
#done

#assoziativ array of user ids to old and new name, could be loaded from json file
declare -A USER_NAME_MAP
USER_NAME_MAP=( ['g.tria@maastrichtuniversity.nl#nlmumc']="g.tria@DUPLICATE.sram" ['jonathan.melius@maastrichtuniversity.nl#nlmumc']="jonathan.melius@DUPLICATE.sram" ["o.palmen@maastrichtuniversity.nl#nlmumc"]="o.palmen@DUPLICATE.sram" ["p.vanschayck@maastrichtuniversity.nl#nlmumc"]="p.vanschayck@DUPLICATE.sram" ["rbg.ravelli@maastrichtuniversity.nl#nlmumc"]="rgb.ravelli@DUPLICATE.sram")

declare -A USER_ID_MAP


#for all existing users, check if the user should be duplicated,
#reate the new users, and add it to the same groups
echo "create new users with same group memberships..."
for user in $(iadmin lu)
do
   userId=$(iadmin lu $user | grep "user_id" | cut -d " " -f 2)
#   echo "   existing user: $user  -> $userId"
   if [ ${USER_NAME_MAP["$user"]+_} ]; then
      newUserName=${USER_NAME_MAP["$user"]}
      USER_ID_MAP[$userId]="$user"
      #check if user already exists!
      if iadmin lu $newUserName | grep 'No rows found'; then
         echo " * NEW USER $newUserName"
         #could still fail, if there is still a home collection for the user!
         iadmin mkuser $newUserName rodsuser
         iuserinfo $user | grep "member of group" | cut -d " " -f 4 | while read -r group ; do
           #we need to add the zone to the group, because the username of 'iadmin lu' contains the zone as well.
           if [[ "$group#nlmumc" != "$user" && "$group" != "public" ]]; then
             iadmin atg "$group" "$newUserName"
              echo " ** ATG $newUserName --> $group"
           fi
         done
      fi
   fi
done

echo ""
echo "mapping of old userIds to userNames (for duplicated users):"
for x in "${!USER_ID_MAP[@]}"; do printf "[%q]=%q\n" "$x" "${USER_ID_MAP[$x]}" ; done
echo "-----------------"


#this will go through all collections
echo "going through all collections, granting user rights for duplicated users..."
iquest "select COLL_NAME, COLL_ACCESS_USER_ID, COLL_ACCESS_TYPE, COLL_ACCESS_NAME"  | while  mapfile -t -n 5 blocks && ((${#blocks[@]})); do
   collection=${blocks[0]##* = }
   userId=${blocks[1]##* = }
   accessName=${blocks[3]##* = }

   #echo "collection: $collection"
   #iquest "select USER_NAME where USER_ID = '$userId'"
   if [ ${USER_ID_MAP[$userId]+_} ]; then
     oldUserName=${USER_ID_MAP[$userId]}
     newUserName=${USER_NAME_MAP[$oldUserName]}
     echo "  - $collection ($oldUserName/$userId) granting: $newUserName ${accessName}"
     ichmod -M "${accessName}" "$newUserName" "$collection"
   else
     #echo "  - ignoring $collection (userId: $userId)"
     :
   fi
done 


