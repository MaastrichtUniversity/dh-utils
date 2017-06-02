from xml.etree import ElementTree as ET
import sys

# Commandline arguments
# input filename
# output filename
# example: migrate.py metadata.xml metadata.new.xml

# Read filename from command line
inputFilename = sys.argv[1]
outputFilename = sys.argv[2]

originalNodeName = "organ"
newNodeName = "tissue"

# parse XML using ElementTree
tree = ET.parse(inputFilename)
root = tree.getroot()

# search for original node name and replace tag with newNodeName
for element in root.iter(originalNodeName):
    element.tag = newNodeName

# Remove all articles
for element in root.iter("article"):
    root.remove(element)

# Append dummy article with reference
ref = ET.Element("article")
ref.text = "http://dx.doi.org/10.1353/lib.0.0036"
root.append( ref )

# Write output
tree.write(outputFilename, encoding='utf-8', xml_declaration=True)

