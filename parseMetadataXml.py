import xml.etree.ElementTree as ET
import sys
import os

##This script changes the node tag of specified node(s) from inputfile and creates a backup of the original file
#Commandline arguments
# inputfilename (This also becomes the filename for the changed file)
# backupfilename (Copy of the original file)
# original node tag
# new node tag
### example: parseMetadataXml.py metadata_full.xml metadata_full_bu.xml organ tissue

## Read filename from command line
inputFilename = sys.argv[1]
backupFilename = sys.argv[2]

## Read orginal node name from command line
originalNodeName = sys.argv[3]

## Read new node name from command line
newNodeName = sys.argv[4]

#parse XML using ElementTree
tree = ET.parse(inputFilename)
root = tree.getroot()

#search for original node name and replace tag with newnodename
for element in root.iter(originalNodeName):
    element.tag = newNodeName

#create backup of original file
os.rename(inputFilename,backupFilename)

#Write output
tree.write(inputFilename)