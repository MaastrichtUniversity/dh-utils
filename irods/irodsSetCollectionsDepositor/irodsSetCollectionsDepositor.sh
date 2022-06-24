#!/usr/bin/env bash

Red='\033[0;31m'    # Red
Green='\033[0;32m'  # Green
#Yellow='\033[0;33m' # Yellow
NC='\033[0m'        # No Color


if [[ $1 != "--commit" ]]; then
    echo "---- RUNNING SCRIPT IN DRY RUN ----"
fi

projectsRoot='/nlmumc/projects/'
errorCount=0

# Retrieve list of all projects
projects=($(ils ${projectsRoot} | awk '{print $2}'))

# Loop over projects
for i in "${projects[@]}"
do
    proj=$(basename "$i")

    projectCollections=($(ils "${i}" | awk '{print $2}'))

    # Loop over the collections
    for projectCollection in "${projectCollections[@]}"
    do
        coll=$(basename "$projectCollection")
        echo "* $projectCollection"

        # Get collection creator AVU
        creator=($(imeta ls -C "$projectCollection" creator | grep value | awk '{print $2}'))
        if [[ $creator == "" ]]; then
          echo -e "${Red} - No creator AVU found. Skip $projectCollection${NC}"
          echo "-------------"
          errorCount=$((errorCount + 1))
          continue
        else
          echo " - AVU creator: " $creator
        fi
        # Lowercase the creator AVU value for the following query
        creator="${creator,,}"
        # Query username by the email AVU value
        creator_username=$(iquest "SELECT USER_NAME  WHERE META_USER_ATTR_VALUE = '$creator'" | grep USER_NAME | awk '{print $3}')
        if [[ $creator_username == "" ]]; then
          echo -e "${Red} - No active user found for $creator. Skip $projectCollection${NC}"
          errorCount=$((errorCount + 1))
        else
          echo " - AVU creator username: "$creator_username
		      if [[ $1 == "--commit" ]]; then
            echo " - Setting AVU depositor ($creator_username) for $projectCollection"
            irule -F /rules/projectCollection/openProjectCollection.r "*project='$proj'" "*projectCollection='$coll'" "*user='rods'" "*rights='own'"
            imeta set -C $projectCollection depositor $creator_username
            irule -F /rules/projectCollection/closeProjectCollection.r "*project='$proj'" "*projectCollection='$coll'"
            echo -e "${Green} - AVU updated${NC}"
          fi
        fi
        echo "-------------"
    done
done

echo "Summary:"
if [[ $errorCount == 0 ]]; then
  echo -e "${Green} - No error found${NC}"
else
  echo -e "${Red} - Error found:  $errorCount${NC}"
fi