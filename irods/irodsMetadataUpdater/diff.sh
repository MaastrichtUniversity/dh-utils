#!/usr/bin/env bash
version=2.0.0

if [[ $1 == "-t" ]]; then
    diff -u -w testing/$version/ testing/$version/output
elif [[ $1 == "-p" ]]; then
    for f in $(find processing -name metadata.xml); do
        pc=$(dirname $f)
        diff -u -w $f $pc/metadata.new.xml
    done
else
    echo "Specify -t for diffing testing, or -p for diffing processing"
fi

