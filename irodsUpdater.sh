#!/bin/bash

#Enter the xml tag that needs to be updated
inputXMLTag="organ"
#Enter the xml tag that the output should contain
outputXMLTag="tissue"


##Initial listing for projects
array=( $(ils /nlmumc/projects | awk '{print $2}'))
#parse projects
for i in "${array[@]}"
do
        echo $i
        #store  projectName in variable
        project=$(basename "$i")
        #listing for collections in projects
        array2=( $(ils $i | awk '{print $2}'))
        for j in "${array2[@]}"
        do
                echo $j
                #store  collection name in variable
                collection=$(basename "$j")
                #listing for files in collections
                array3=( $(ils $j | awk '{print $1}'))
                for k in "${array3[@]}"
                do
                        #If file is metadata .xml  download,parse and update
                        if [[ $k == *"metadata"* ]]; then
                                echo  $j/$k
                                path=$j
                                backup=${path/\//}

                                #create path on local disk
                                mkdir -p $backup
                                #download metadata.xml from irods
                                iget $path/$k $backup/$k
                                echo "parsing $backup/$k"
                                #parse  xml in python and change xml tag
                                python parseMetadataXml.py $backup/$k $backup/$k\_orig "$inputXMLTag" "$outputXMLTag"
                                echo "updating irods"
                                #open irods collection for writing
                                echo "irule -F $rulespath/projects/openProjectCollection.r\" \"*project='$project'\" \"*projectCollection='$collection'\""
                                irule -F /rules/projects/openProjectCollection.r "*project='$project'" "*projectCollection='$collection'"
                                #Update file in irods
                                iput -f $backup/$k $path/$k
                                #close collection for writing in irods
                                irule -F /rules/projects/closeProjectCollection.r "*project='$project'" "*projectCollection='$collection'"
                        fi
                done
        done
done

