#!/usr/bin/env bash
path="/nlmumc/projects/$1"

size=$(irule "calcCollectionSize('$path', 'B', 'none', *result); writeLine('stdout', *result);" null ruleExecOut)

echo "Setting dcat:byteSize to $size"

if [[ $2 == "--commit" ]]; then
    imeta set -C $path 'dcat:byteSize' $size
fi