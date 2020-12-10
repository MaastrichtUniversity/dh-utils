#!/usr/bin/env bash
path="/nlmumc/projects/$1"

size=$(irule "calcCollectionSize('$path', 'B', 'none', *result); writeLine('stdout', *result);" null ruleExecOut)
numFiles=$(irule "calcCollectionFiles('$path', *result); writeLine('stdout', *result);" null ruleExecOut)

echo "Setting dcat:byteSize to $size"
echo "Setting numFiles to $numFiles"

if [[ $2 == "--commit" ]]; then
    imeta set -C $path 'dcat:byteSize' $size
    imeta set -C $path 'numFiles' $numFiles
fi