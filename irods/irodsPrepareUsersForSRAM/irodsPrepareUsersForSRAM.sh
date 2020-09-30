#!/usr/bin/env bash

if [[ $1 != "--commit" ]]; then
    echo "---- RUNNING SCRIPT IN DRY RUN ----"
fi;

# Retrieve list rodsusers
users=( $(iquest --no-page "select USER_NAME where USER_TYPE = 'rodsuser'" | grep USER | awk '{print $3}'))

# Loop over users to add the correct AVU
for i in "${users[@]}"
do
    if [[ $i == service-* ]] ; then
        echo "Adding AVU ldapSync false to service user $i"
        if [[ $1 == "--commit" ]]; then
           imeta set -u "${i}" "ldapSync" "false"
        fi;
    else
	echo "Adding AVU pendingSramInvite user $i"
        if [[ $1 == "--commit" ]]; then
           imeta set -u "${i}" "pendingSramInvite" "true"
        fi;
    fi;
done
