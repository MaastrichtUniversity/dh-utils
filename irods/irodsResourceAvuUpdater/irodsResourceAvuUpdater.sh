#!/usr/bin/env bash

# BEFORE YOU BEGIN: Set the correct resource values
oldIngestResource='iresResource'
newIngestResource='ires-centosResource'
oldResource='replRescUM01'
newResource='replRescAZM01'


if [[ $1 != "--commit" ]]; then
    echo "---- RUNNING SCRIPT IN DRY RUN ----"
fi;

# Retrieve all projects with AVU set to the value of 'oldIngestResource' (grep omits the separating lines containing '----' )
projects=( $(imeta qu -C ingestResource = $oldIngestResource | awk '{print $2}' | grep /nlmumc))

# Loop over projects to set the ingestResource
for i in "${projects[@]}"
do
    # Set resource
    echo "Setting ingestResource for project $i to $newIngestResource"
    if [[ $1 == "--commit" ]]; then
        imeta set -C $i 'ingestResource' $newIngestResource
    fi;
done


# Retrieve all projects with AVU set to the value of 'oldResource' (grep omits the separating lines containing '----' )
projects=( $(imeta qu -C resource = $oldResource | awk '{print $2}' | grep /nlmumc))

# Loop over projects to set the resource
for j in "${projects[@]}"
do
    # Set resource
    echo "Setting resource for project $j to $newResource"
    if [[ $1 == "--commit" ]]; then
        imeta set -C $j 'resource' $newResource
    fi;
done
