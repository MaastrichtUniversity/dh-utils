#!/usr/bin/env bash

# BEFORE YOU BEGIN: Set the correct resource values
projectsRoot='/nlmumc/projects/'


if [[ $1 != "--commit" ]]; then
    echo "WARNING: This script does not have a dry-run. Test it thorougly on a non-production environment and think twice before you use the --commit flag"
    echo "Now exiting without making any changes"
    exit 0
fi;

# Retrieve list of all projects
projects=( $(ils ${projectsRoot} | awk '{print $2}'))

# Loop over projects
for i in "${projects[@]}"
do
    proj=$(basename "$i")

    projectCollections=( $(ils ${i} | awk '{print $2}'))

    for j in "${projectCollections[@]}"
    do
        coll=$(basename "$j")
        echo $proj $coll
        if [[ ${proj} == "P000000010" ]]; then
            echo "Leave permissions as is for ${proj}/${coll}"
            irule "setCollectionSize( '${proj}', '${coll}', 'false', 'false' )" null null
        else
            irule "setCollectionSize( '${proj}', '${coll}', 'true', 'true' )" null null
        fi
    done
done
