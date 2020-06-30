#!/usr/bin/env bash

mode=$1
input=$2
while IFS=, read -r project pi datasteward
do
		if [[ $project =~ ^\/nlmumc\/projects\/P[0-9]{9}$ ]] ;	then
			projectID="$(cut -d'/' -f4 <<<"$project")"
			echo "$projectID"			
			
			if [[ $1 == "--dry-run" ]]; then
				echo "- List data steward AVU on $projectID"
				imeta ls -C $project datasteward
				
				echo "- List data steward AVU on $datasteward"
				imeta ls -u $datasteward specialty
				
				echo "- List ACL on $projectID"
				ils -A $project
			fi;
    
			if [[ $1 == "--commit" ]]; then
				echo "- Add data steward AVU on $projectID"
				imeta set -C $project datasteward $datasteward
				
				echo "- Add data steward AVU on $datasteward"
				imeta set -u $datasteward specialty data-steward
				
				echo "- Give manager permission to $datasteward recursively on $projectID and its collections"
				irule -s -F /rules/projects/changeProjectPermissions.r *project="$projectID" *users="$datasteward:own"		
			fi;
				
		fi
done < "$input"

