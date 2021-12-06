#!/usr/bin/env bash

# CONFIGURATION
avuName='responsibleCostCenter'
oldValue='UM-30001234X'
newValue='UM-30005678X'


# SCRIPT
if [[ $1 != "--commit" ]]; then
    echo "---- RUNNING SCRIPT IN DRY RUN ----"
fi;

# Retrieve all projects for which 'avuName' equals the value of 'oldValue'
# grep omits the separator lines containing '----'
projects=( $(imeta qu -C $avuName = $oldValue | awk '{print $2}' | grep /nlmumc))

# Loop over projects to set the new value
for i in "${projects[@]}"
do
    # Set new AVU value
    echo "Project $i : Changing attribute '$avuName' from '$oldValue' to '$newValue'"
    if [[ $1 == "--commit" ]]; then
        imeta set -C $i $avuName $newValue
    fi;
done

