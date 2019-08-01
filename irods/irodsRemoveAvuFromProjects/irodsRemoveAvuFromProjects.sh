#!/usr/bin/env bash

# BEFORE YOU BEGIN: Set the correct resource values
AvuName='NCIT:C88193'
projectsRoot='/nlmumc/projects/'


if [[ $1 != "--commit" ]]; then
    echo "---- RUNNING SCRIPT IN DRY RUN ----"
fi;

# Retrieve list of all projects
projects=( $(ils ${projectsRoot} | awk '{print $2}'))

# Loop over projects to remove the AVU
for i in "${projects[@]}"
do
    echo "Removing AVU ${AvuName} from project $i"
    if [[ $1 == "--commit" ]]; then
        imeta rm -C $i ${AvuName}
    fi;
done
