#!/usr/bin/env bash

if [[ $1 != "--commit" ]]; then
    echo "---- RUNNING SCRIPT IN DRY RUN ----"
fi;

# Retrieve list rodsusers
# Yes was added because iquests pauses output when there are too many
# One person gets replaced by an equal sign. That user was manually updated to have the pendingSramInvite AVU
users=( $(yes | iquest "select USER_NAME where USER_TYPE = 'rodsuser'" | grep USER | awk '{print $3}'))

# Loop over users to add the correct AVU
for i in "${users[@]}"
do
    if [[ $i == service-* ]] ; then
        echo "Adding AVU ldapSync false to service user $i"
        if [[ $1 == "--commit" ]]; then
           imeta set -u "${i}" "ldapSync" "false"
        fi;
    else
       # The equal sign gets added in the output because of the 'yes' 
        if [[ $i != "=" ]]; then
	    echo "Adding AVU pendingSramInvite user $i"
            if [[ $1 == "--commit" ]]; then
               imeta set -u "${i}" "pendingSramInvite" "true"
            fi;
	fi;
    fi;
done
