#!/usr/bin/env bash

# This specifies the version of the migrate script to be executed
version=2.1.3

# Base path in iRODS
base=/nlmumc/projects

# Fail on error
set -e

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

        echo "Updating $p"

        if [[ $1 == "--commit" ]]; then
            # Open project collection for writing
            irule "openProjectCollection('$project', '$collection')" null null
        fi

        # If required, parse and update metadata_xml
        if [[ -e migrations/$version/metadata_xml_migrate.py ]]; then

            # download metadata.xml from irods
            set +e
            iget -f $base/$p/metadata.xml processing/$p/metadata.xml > /dev/null 2>&1
            rc=$?
            set -e

            if [[ $rc != 0 ]]; then
                echo "Warning, could not retrieve $p/metadata.xml"
            else
                python migrations/$version/metadata_xml_migrate.py processing/$p/metadata.xml processing/$p/metadata.new.xml

                # Only put results back when --commit is the argument
                if [[ $1 == "--commit" ]]; then
                    iput -f processing/$p/metadata.new.xml $base/$p/metadata.xml
                fi
            fi
        fi

        # If required, update AVU's
        if [[ -e migrations/$version/avu_migrate.sh ]]; then
            # Only put results back when --commit is the argument
            if [[ $1 == "--commit" ]]; then
                bash migrations/$version/avu_migrate.sh $p --commit
            else
                bash migrations/$version/avu_migrate.sh $p
            fi
        fi

        # If required, update PID
        if [[ -e migrations/$version/new_pid.sh ]]; then
            # Only put results back when --commit is the argument
            if [[ $1 == "--commit" ]]; then
                bash migrations/$version/new_pid.sh $project $collection --commit
            else
                bash migrations/$version/new_pid.sh $project $collection
            fi
        fi

        if [[ $1 == "--commit" ]]; then
            # Close project collection for writing
            irule "closeProjectCollection('$project', '$collection')" null null
        fi;
    done
done

