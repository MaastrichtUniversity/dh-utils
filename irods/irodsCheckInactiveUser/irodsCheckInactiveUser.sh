#!/usr/bin/env bash

Red='\033[0;31m'    # Red
Green='\033[0;32m'  # Green
Yellow='\033[0;33m' # Yellow
NC='\033[0m'        # No Color

DRY_RUN=true

while getopts ":d:u:" opt; do
  case $opt in
  d)
    echo "-d was triggered with $OPTARG" >&2
    DRY_RUN=${OPTARG}
    echo "DRY_RUN is $DRY_RUN" >&2
    ;;
  u)
    echo "-u was triggered with $OPTARG" >&2
    USERNAME=${OPTARG}
    echo "USERNAME is $USERNAME" >&2
    ;;
  \?)
    echo "Invalid option: -$OPTARG" >&2
    exit 1
    ;;
  :)
    echo "Option -$OPTARG requires an argument." >&2
    exit 1
    ;;
  *)
    echo "No arguments given exiting" >&2
    exit 1
    ;;
  esac
done

if [ $OPTIND -eq 1 ]; then
  echo "No options were passed"
  exit 1
fi

SAFE_DELETION=true

echo "Check data steward role"
attribute=dataSteward
ds=$(imeta ls -u "$USERNAME" specialty)

if echo "$ds" | grep -q "data-steward"; then
  echo -e "${NC}* $USERNAME is a data steward for the project(s):"
  for project in $(iquest "select COLL_NAME where META_COLL_ATTR_NAME = '$attribute' AND  META_COLL_ATTR_VALUE = '$USERNAME'" | grep "COLL_NAME" | cut -d" " -f 3); do
    echo -e "${Red} * $project${NC}"
    SAFE_DELETION=false
  done
else
  echo " * No data steward role found"
fi

echo "Check PI role"
attribute="OBI:0000103"

PI=$(iquest "select COLL_NAME where META_COLL_ATTR_NAME = '$attribute' AND  META_COLL_ATTR_VALUE = '$USERNAME'")

if echo "$PI" | grep -q "Nothing was found matching your query"; then
  echo " * No PI role found"
else
  echo -e "${Red}* $USERNAME is a PI for the project(s):${NC}"
  for project in $(iquest "select COLL_NAME where META_COLL_ATTR_NAME = '$attribute' AND  META_COLL_ATTR_VALUE = '$USERNAME'" | grep "COLL_NAME" | cut -d" " -f 3); do
    echo -e "${Red} * $project${NC}"
    SAFE_DELETION=false
  done
fi

echo "Summary:"
if $SAFE_DELETION; then
  echo -e "${Green} The user is safe for deletion${NC}"
else
  echo -e "${Red} The user is not safe for deletion.${NC}"
  echo -e "${NC} Please resolve the pending issue (in red in the log above)"
fi
