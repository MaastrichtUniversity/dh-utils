#!/usr/bin/env bash

Red='\033[0;31m'    # Red
Green='\033[0;32m'  # Green
Yellow='\033[0;33m' # Yellow
NC='\033[0m'        # No Color

DRY_RUN=true
WARNING_MODE=true
SAFE_DELETION=true
REVOKE_MODE=false

while getopts ":d:r:u:w:" opt; do
  case $opt in
  d)
    echo "-d was triggered with $OPTARG" >&2
    DRY_RUN=${OPTARG}
    echo "DRY_RUN is $DRY_RUN" >&2
    ;;
  r)
    echo "-r was triggered with $OPTARG" >&2
    REVOKE_MODE=${OPTARG}
    echo "REVOKE_MODE is $DRY_RUN" >&2
    ;;
  u)
    echo "-u was triggered with $OPTARG" >&2
    USERNAME=${OPTARG}
    echo "USERNAME is $USERNAME" >&2
    ;;
  w)
    echo "-w was triggered with $OPTARG" >&2
    WARNING_MODE=${OPTARG}
    echo "WARNING_MODE is $WARNING_MODE" >&2
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

if [ $OPTIND -eq 1 ]; then
  echo "No options were passed"
  echo "Exit"
  exit 1
fi

SAFE_DELETION=true

echo "Check data steward role"
attribute=dataSteward
ds=$(imeta ls -u "$USERNAME" specialty)

occurrences=0
if echo "$ds" | grep -q "data-steward"; then
  for project in $(iquest "select COLL_NAME where META_COLL_ATTR_NAME = '$attribute' AND  META_COLL_ATTR_VALUE = '$USERNAME'" | grep "COLL_NAME" | cut -d" " -f 3); do
    occurrences=$((occurrences+1))
    if [[ "$occurrences" -eq 1 ]]; then
      echo -e "${NC}* $USERNAME is a data steward for the project(s):"
    fi
    echo -e "${Red} * $project${NC}"
    SAFE_DELETION=false
  done
else
  occurrences=-1
  echo " * No data steward role found"
fi
if [[ "$occurrences" -eq 0 ]]; then
  echo " * Data steward role found, but no project assigned"
fi


echo "Check PI role"
attribute="OBI:0000103"

PI=$(iquest "select COLL_NAME where META_COLL_ATTR_NAME = '$attribute' AND  META_COLL_ATTR_VALUE = '$USERNAME'")

if echo "$PI" | grep -q "Nothing was found matching your query"; then
  echo " * No PI role found"
else
  echo -e "${Red}* $USERNAME is a PI for the project(s):${NC}"
  for project in $(iquest "select COLL_NAME where META_COLL_ATTR_NAME = '$attribute' AND  META_COLL_ATTR_VALUE = '$USERNAME'" | grep "COLL_NAME" | cut -d" " -f 3); do
    echo -e "${Red} * $project${NC}"
    SAFE_DELETION=false
  done
fi

userId=$(iadmin lu "$USERNAME" | grep "user_id" | cut -d " " -f 2)

WARNING=0
occurrences=0

echo "Check for last managers"
for project in  $(iquest "select COLL_NAME where COLL_PARENT_NAME = '/nlmumc/projects'" | grep "COLL_NAME" | cut -d" " -f 3)
do
  # Query the numbers of managers for each projects
  for nb_managers in $(iquest "%s"  "select count(COLL_ACCESS_NAME) where COLL_NAME = '$project' AND COLL_ACCESS_NAME = 'own'"); do
    # Check if there are two (rods should always be there) or less managers present
    if [[ "$nb_managers" -le 2 ]]; then
      if $WARNING_MODE; then
        echo -e "${Yellow} * $project has two or less managers${NC}"
        WARNING=$((WARNING+1))
      fi

      # Check if the 2nd manager is the input user
      while mapfile -t -n 4 blocks && ((${#blocks[@]}));
      do
        managerId=${blocks[1]##* = }
        if [ "$userId" == "$managerId" ]; then
          echo -e "${Red} * $USERNAME is the last manager for $project${NC}"
          SAFE_DELETION=false
          occurrences=$((occurrences+1))
        else
           :
        fi
      done< <(iquest "select COLL_NAME, COLL_ACCESS_USER_ID, COLL_ACCESS_NAME where COLL_NAME = '$project' AND COLL_ACCESS_NAME = 'own'" )
    fi
  done
done
if [[ "$occurrences" -eq 0 ]]; then
  echo "* $USERNAME is not the last manager for any project"
fi


echo "Check for active dropzone"
for nb_dropzones in $(iquest "%s" "SELECT count(COLL_ACCESS_USER_ID) WHERE COLL_PARENT_NAME = '/nlmumc/ingest/zones' AND COLL_ACCESS_USER_ID = '$userId'"); do
  if [[ "$nb_dropzones" -gt 0 ]]; then
      echo -e "${Red} * $nb_dropzones active(s) dropzone(s)${NC}"
      SAFE_DELETION=false
      for dropzone in $(iquest "%s" "SELECT COLL_NAME WHERE COLL_PARENT_NAME = '/nlmumc/ingest/zones' AND COLL_ACCESS_USER_ID = '$userId'"); do
        echo -e "${Red} * $dropzone${NC}"
      done
  else
    echo " * No active dropzone"
  fi
done


function write_acl_csv {
  timestamp=$(date +"%Y-%m-%d")
  filename="ACL_$USERNAME-$timestamp.csv"
  touch "$filename"
  echo -e "${Green} # Writing to $filename${NC}"

  # Get individual user permissions
  echo "User individual project ACL:" >> "$filename"
  while mapfile -t -n 4 blocks && ((${#blocks[@]}));
  do
    collection=${blocks[0]##* = }
    accessUserId=${blocks[1]##* = }
    accessName=${blocks[2]##* = }
    [[ "$accessName" == "modify object" ]] && accessName="write"
    [[ "$accessName" == "read object" ]] && accessName="read"

    if [ "$userId" == "$accessUserId" ]; then
      line="$collection,$USERNAME,$accessName"
      echo "$line" >> "$filename"
    fi
  done< <(iquest "SELECT COLL_NAME, COLL_ACCESS_USER_ID, COLL_ACCESS_NAME  WHERE COLL_PARENT_NAME = '/nlmumc/projects'" )

  # Get user group membership
  echo "" >> "$filename"
  echo "User group membership:" >> "$filename"
  for groupName in $(iquest "%s" "SELECT USER_GROUP_NAME WHERE USER_ID = '$userId'"); do
      echo "$groupName" >> "$filename"
  done
}


function revoke_permissions {
  echo -e "${Green} # Revoking permissions${NC}"
  for project in  $(iquest "%s" "select COLL_NAME where COLL_PARENT_NAME = '/nlmumc/projects'")
  do
    ichmod -r null "$USERNAME" "$project"
  done
}


echo "Summary:"
if [ $WARNING -gt 0 ]; then
  echo -e "${Yellow} # $WARNING warning(s) found (yellow in the log above)"
fi

if $SAFE_DELETION; then
  echo -e "${Green} # $USERNAME is safe for deletion${NC}"
  if [[ $DRY_RUN == "false" ]]; then
    echo -e "${Green} # Saving ACL${NC}"
    write_acl_csv
    if $REVOKE_MODE; then
      revoke_permissions
    else
      echo -e " # Skip revoke permissions; REVOKE_MODE is $REVOKE_MODE"
    fi
  fi

else
  echo -e "${Red} # $USERNAME is not safe for deletion.${NC}"
  echo -e "${Red} # Please resolve the pending issue(s) (in red in the log above)${NC}"
fi
