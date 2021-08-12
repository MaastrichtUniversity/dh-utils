#!/usr/bin/env bash

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