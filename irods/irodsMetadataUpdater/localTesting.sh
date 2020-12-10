#!/usr/bin/env bash

set -e

# This specifies the version of the migrate script to be executed
version=2.0.0

# remove and (re)create output directory
if [ -x testing/$version/output ]; then
    rm -r testing/$version/output
fi
mkdir testing/$version/output

files=( $(ls testing/$version/*.xml))
for i in "${files[@]}"
do
    file=$(basename "$i")
    python migrations/$version/metadata_xml_migrate.py testing/$version/$file testing/$version/output/$file
done
