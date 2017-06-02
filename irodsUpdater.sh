#!/bin/bash

# Enter the xml tag that needs to be updated
inputXMLTag="organ"
# Enter the xml tag that the output should contain
outputXMLTag="tissue"

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
        mkdir -p $p

        # TODO: We should place metadata.xml version information somewhere, as iRODS metadata or in the XML itself

        # download metadata.xml from irods
        iget -f $base/$p/metadata.xml $p/metadata.xml > /dev/null 2>&1

        rc=$?
        if [[ $rc != 0 ]]; then
            echo "Warning, could not retrieve $p/metadata.xml"
            continue
        fi

        echo "Updating $p/metadata.xml"

        # Break on any error from here on
        set -e

        # parse xml in python and change xml tag
        python parseMetadataXml.py $p/metadata.xml $p/metadata.orig.xml "$inputXMLTag" "$outputXMLTag"

        # Open project collection for writing
        irule "openProjectCollection('$project', '$collection')" null null

        # Update file in irods
        iput -f $p/metadata.xml $base/$p/metadata.xml

        # Close project collection for writing
        irule "closeProjectCollection('$project', '$collection')" null null

        # Stop breaking on any error from here on
        set +e
    done
done

