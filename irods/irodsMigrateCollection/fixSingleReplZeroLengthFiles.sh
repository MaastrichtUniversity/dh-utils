#!/usr/bin/env bash

# Execute the following iquest query:
# iquest --no-page "%d %s/%s" "select count(DATA_NAME), COLL_NAME, DATA_NAME WHERE DATA_SIZE = '0' AND COLL_NAME like '/nlmumc/projects/%' " | egrep -v '^2'

# then strip the leading "1 " from each line.

# then execute this script and rerun the query to find potential left-overs


input="./list"
while IFS= read -r dataobj
do
  echo ""
  echo "irepl -M -R rootResc \"${dataobj}\""
  irepl -M -R rootResc "${dataobj}"
  echo "itrim -M -N 1 -S UM-hnas2-4k-repl \"${dataobj}\""
  itrim -M -N 1 -S UM-hnas-4k-repl "${dataobj}"
  echo "irepl -M -R replRescUM01 \"${dataobj}\""
  irepl -M -R replRescUM01 "${dataobj}"
  echo "itrim -M -S demoResc \"${dataobj}\""
  itrim -M -S demoResc "${dataobj}"
done < "$input"

