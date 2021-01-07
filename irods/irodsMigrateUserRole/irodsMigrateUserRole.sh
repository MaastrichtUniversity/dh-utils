#!/usr/bin/env bash

DRY_RUN=true
MAPPING_FILE='mapping.txt'

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
   echo "Migrating all users found in $MAPPING_FILE, dry-run=$DRY_RUN"
   echo ""
   echo "reading in mapping-file..."
   while read current_name new_name; do
     USER_NAME_MAP["$current_name"]="$new_name"
   done < <(grep -v "^;" $MAPPING_FILE)
elif [ $MODE == "user" ] ; then
   echo "applying single user $USERNAME to $NEW_USER , dry-run=$DRY_RUN"
   USER_NAME_MAP["$USERNAME"]="$NEW_USER"
else
   echo "no valid option provided for mode. exiting..."
   exit 1
fi

# debug line: shows content of the associative array USER_NAME_MAP
#for x in "${!USER_NAME_MAP[@]}"; do printf "[%q]=%q\n" "$x" "${USER_NAME_MAP[$x]}" ; done


for old_name in "${!USER_NAME_MAP[@]}";
do
   if [ ${USER_NAME_MAP["$old_name"]+_} ]; then
      # Create the new users, and add it to the same groups
      new_name=${USER_NAME_MAP["$old_name"]}
      
      echo "Check new user"
			check=$(imeta ls -u $new_name)

			if echo "$check" | grep -q "does not exist"; then
					echo " * User $new_name not found"
					echo " * Exit"
					exit
			else
					echo " * User $new_name exists"
			fi


			echo "Check data steward role"
			attribute=dataSteward
			ds=$(imeta ls -u $old_name specialty)

			if echo "$ds" | grep -q "data-steward"; then
					echo " * $old_name is a data steward"
					echo " * Give data steward role to $new_name"
					[[ $DRY_RUN == "false" ]] && imeta set -u $new_name specialty data-steward
					
					echo "Change data steward from $old_name to $new_name for the project(s):"
					for project in  $(iquest "select COLL_NAME where META_COLL_ATTR_NAME = '$attribute' AND  META_COLL_ATTR_VALUE = '$old_name'" | grep "COLL_NAME" | cut -d" " -f 3)
						do
							 echo " * $project"
						   [[ $DRY_RUN == "false" ]] && imeta set -C $project $attribute $new_name
						done
			else
					echo " * No data steward role found"
			fi


			echo "Check PI role"
			attribute="OBI:0000103"

			PI=$(iquest "select COLL_NAME where META_COLL_ATTR_NAME = '$attribute' AND  META_COLL_ATTR_VALUE = '$old_name'")

			if echo $PI | grep -q "Nothing was found matching your query"; then
					echo " * No PI role found"
			else
					echo " * $old_name is a PI"
					echo "Change PI from $old_name to $new_name for the project(s):"
					for project in  $(iquest "select COLL_NAME where META_COLL_ATTR_NAME = '$attribute' AND  META_COLL_ATTR_VALUE = '$old_name'" | grep "COLL_NAME" | cut -d" " -f 3)
					do
							 echo " * $project"
						   [[ $DRY_RUN == "false" ]] && imeta set -C $project $attribute $new_name
					done
			fi
   fi
done


