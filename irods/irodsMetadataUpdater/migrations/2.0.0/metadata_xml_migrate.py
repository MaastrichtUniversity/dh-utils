from xml.etree import ElementTree as ET
import sys

# Commandline arguments
# input filename
# output filename
# example: metadata_xml_migrate.py metadata.xml metadata.new.xml


# Pretty print function for indentation
def indent(elem, level=0):
    i = "\n" + level * "  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


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
for article in root.findall("article"):
    root.remove(article)

# Append dummy article with reference
ref = ET.Element("article")
ref.text = "http://dx.doi.org/10.1353/lib.0.0036"
root.append(ref)

indent(root)

# Write output
tree.write(outputFilename, encoding="utf-8", xml_declaration=True)
