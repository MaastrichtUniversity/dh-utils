#!/usr/bin/env bash

attribute=$2
value=$3

if [[ $1 != "--commit" ]]; then
    echo "---- RUNNING SCRIPT IN DRY RUN ----"
fi;

ils /nlmumc/projects | while read -r prefix project ; 
do
	if [[ $project =~ ^\/nlmumc\/projects\/P[0-9]{9}$ ]] ;	then
		if [[ $1 == "--dry-run" ]]; then
			imeta ls -C $project $attribute
		fi;	
		if [[ $1 == "--commit" ]]; then	
    	echo "Set AVU ${attribute} to $value for project $project"
			imeta set -C $project $attribute $value	
		fi;
		
	fi;
done
