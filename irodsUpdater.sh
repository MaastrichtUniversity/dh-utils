#!/bin/bash

# This specifies the version of the migrate script to be executed
version=2.0.0

# Base path in iRODS
base=/nlmumc/projects

# Listing for projects
projects=( $(ils $base | awk '{print $2}'))
for i in "${projects[@]}"
do
    # store  project in variable
    project=$(basename "$i")
    # listing for collections in projects
    collections=( $(ils $i | awk '{print $2}'))

    for j in "${collections[@]}"
    do
        # store  collection name in variable
        collection=$(basename "$j")

        p=$project/$collection

        # create backup path on local disk
        mkdir -p processing/$p

        # TODO: We should place metadata.xml version information somewhere, as iRODS metadata or in the XML itself

        # download metadata.xml from irods
        iget -f $base/$p/metadata.xml processing/$p/metadata.xml > /dev/null 2>&1

        rc=$?
        if [[ $rc != 0 ]]; then
            echo "Warning, could not retrieve $p/metadata.xml"
            continue
        fi

        echo "Updating $p/metadata.xml"

        # Break on any error from here on
        set -e

        # parse xml in python and change xml tag
        python migrations/$version/migrate.py processing/$p/metadata.xml processing/$p/metadata.new.xml

        # Open project collection for writing
        irule "openProjectCollection('$project', '$collection')" null null

        # Update file in irods
        iput -f processing/$p/metadata.new.xml $base/$p/metadata.xml

        # Close project collection for writing
        irule "closeProjectCollection('$project', '$collection')" null null

        # Stop breaking on any error from here on
        set +e
    done
done

