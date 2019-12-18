#!/bin/bash

# Fail on error
set -e

files=( $(ils /nlmumc/projects/P000000010/C000000001 | grep -v nlmumc | grep -v safe))

for i in "${files[@]}"
do
  echo Processing /nlmumc/projects/P000000010/C000000001/$i
  if [[ $1 == "--commit" ]]; then
    ichmod read DH-IBD /nlmumc/projects/P000000010/C000000001/$i
  fi
done
