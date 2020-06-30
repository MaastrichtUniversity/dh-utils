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
				
				echo "- Give viewer permission to $datasteward recursively on $projectID and its collections"
				irule -s -F /rules/projects/changeProjectPermissions.r *project="$projectID" *users="$datasteward:read"

				echo "- Change to manager permission for $datasteward on $projectID"
				ichmod own $datasteward /nlmumc/projects/$projectID
			fi;
				
		fi
done < "$input"

