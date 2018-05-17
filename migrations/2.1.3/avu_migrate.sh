#!/usr/bin/env bash
# Fail on errors
set -e

project="$1"
collection="$2"
projectcollection="$1$2"
baseURL="http://pacman.dev2.rit.unimaas.nl/hdl/"
mirthURL="http://mirthconnect.dev2.rit.unimaas.nl:6681"
URL="$baseURL$1/$2"
path="/nlmumc/projects/$project/$collection"

PID=$(curl -d '{"ID":"'$projectcollection'", "URL":"'$URL'"}' -H "Content-Type: application/json" -X POST $mirthURL)

echo "Setting PID to $PID with URL as $URL for $path"


if [[ $3 == "--commit" ]]; then
    imeta set -C $path 'PID' $PID
fi
