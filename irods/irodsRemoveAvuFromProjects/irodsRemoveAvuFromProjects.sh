#!/usr/bin/env bash

# BEFORE YOU BEGIN: Set the correct resource values
AvuName='NCIT:C88193'
projectsRoot='/nlmumc/projects'


if [[ $1 != "--commit" ]]; then
    echo "---- RUNNING SCRIPT IN DRY RUN ----"
fi;

# Retrieve list of all projects with AvuName present
projects=( $(iquest "select COLL_NAME where COLL_PARENT_NAME like '${projectsRoot}' and META_COLL_ATTR_NAME like '${AvuName}'" | awk '{print $3}' | grep /nlmumc ))

# Loop over projects to remove the AVU
for i in "${projects[@]}"
do
    echo "Removing AVU ${AvuName} from project $i"
    if [[ $1 == "--commit" ]]; then
        # imeta rmw -C Name AttName AttValue
        # using % wildcard as AttValue
        imeta rmw -C "${i}" "${AvuName}" "%"
    fi;
done
