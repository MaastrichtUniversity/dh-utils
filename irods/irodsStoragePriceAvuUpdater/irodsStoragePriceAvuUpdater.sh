#!/usr/bin/env bash

# BEFORE YOU BEGIN: Set the correct values for these variables
resourceName='replRescUM01'
AvuName='NCIT:C88193'
AvuOldValue='0.32'
AvuNewValue='0.189'


if [[ $1 != "--commit" ]]; then
    echo "---- RUNNING SCRIPT IN DRY RUN ----"
fi;

echo "-- Run configuration --"
echo "resourceName: $resourceName"
echo "AVU to update: $AvuName"
echo "Old Value: $AvuOldValue"
echo "New Value: $AvuNewValue"
echo "-----------------------"

# Retrieve all projects matching the resource indicated in 'resourceName' and storage price equal to 'AvuOldValue' (grep omits the separating lines containing '----' )
projects=( $(imeta qu -C resource = $resourceName and $AvuName = $AvuOldValue | awk '{print $2}' | grep /nlmumc))

# Loop over projects to update the AVU
for j in "${projects[@]}"
do
    # Set AVU
    echo "Setting $AvuName for project $j to $AvuNewValue"
    if [[ $1 == "--commit" ]]; then
        imeta set -C $j $AvuName $AvuNewValue
    fi;
done
