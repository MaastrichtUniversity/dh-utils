import sys
import urllib.request
import xml.etree.cElementTree as ET

from jsonschema import validate

from jsonld_utils import *
from xml_utils import *


class Conversion:
    def __init__(self, xml_root, json_instance_template, avu_metadata):
        self.xml_root = xml_root
        self.json_instance_template = json_instance_template
        self.avu_metadata = avu_metadata

    def get_instance(self):
        self.add_identifier()
        self.add_creator()
        self.add_title()
        self.add_publisher()
        self.add_subject()
        self.add_contributor()
        self.add_contact()
        self.add_date()
        self.add_resource_type()
        self.add_related_identifier()
        self.add_description()
        self.add_extended_date()
        self.add_extended_experiment()
        self.update_properties()

        return self.json_instance_template

    def update_properties(self):
        creator_uri = f"https://mdr.datahubmaastricht.nl/user/{self.avu_metadata['creator_username']}"
        self.json_instance_template["pav:createdOn"] = self.avu_metadata["ctime"]
        self.json_instance_template["pav:createdBy"] = creator_uri
        self.json_instance_template["pav:lastUpdatedOn"] = self.avu_metadata["ctime"]
        self.json_instance_template["oslc:modifiedBy"] = creator_uri

    def add_identifier(self):
        # "1_Identifier":
        pid = self.avu_metadata["version_PID"]
        add_value_to_key(self.json_instance_template, "datasetIdentifier", {"@value": pid})

    def add_creator(self):
        # "2_Creator":
        add_value_to_key(self.json_instance_template, "2_Creator", add_creator(self.avu_metadata))

    def add_title(self):
        # "3_Title":
        title = read_text(self.xml_root, "title")
        add_value_to_key(self.json_instance_template, "title", {"@value": title})

    def add_publisher(self):
        # "4_Publisher":
        pass

    def add_subject(self):
        # "6_Subject":
        factors = read_tag_node(self.xml_root, "factors")
        if len(factors) != 0:
            add_value_to_key(self.json_instance_template, "6_Subject", add_keywords(factors))

    def add_contributor(self):
        # "7_Contributor":
        add_value_to_key(
            self.json_instance_template, "7_Contributor", add_contributors(self.avu_metadata["contributors"])
        )

    def add_contact(self):
        # "7_ContactPerson":
        contacts = read_contacts(self.xml_root)
        if len(contacts) != 0:
            add_value_to_key(
                self.json_instance_template,
                "7_ContactPerson",
                add_contact_person(contacts, self.avu_metadata["affiliation_mapping_file"]),
            )
        else:
            # If there is no contact in metadata.xml, add the PI by default
            add_value_to_key(
                self.json_instance_template,
                "7_ContactPerson",
                add_pi_contact(self.avu_metadata["contributors"]["project manager"]),
            )

    def add_date(self):
        # "8_Date":
        date = self.avu_metadata["submissionDate"]
        add_value_to_key(self.json_instance_template, "datasetDate", {"@value": date})

    def add_resource_type(self):
        # "10_ResourceType":
        pass

    def add_related_identifier(self):
        # "12_RelatedIdentifier":
        articles = read_tag_list(self.xml_root, "article")
        if len(articles) != 0:
            add_value_to_key(self.json_instance_template, "12_RelatedIdentifier", add_publications_values(articles))

    def add_description(self):
        # "17_Description":
        description = read_text(self.xml_root, "description")
        add_value_to_key(self.json_instance_template, "Description", {"@value": description})

    def add_extended_date(self):
        # "Extended_Date":
        date = read_text(self.xml_root, "date")
        add_value_to_key(self.json_instance_template, "extendedDate", {"@value": date})

    def add_extended_experiment(self):
        # "Extended_Experiment":
        organism = read_tag(self.xml_root, "organism")
        add_value_to_key(self.json_instance_template, "organism", add_ontology_value(organism))

        tissue = read_tag(self.xml_root, "tissue")
        add_value_to_key(self.json_instance_template, "tissue", add_ontology_value(tissue))

        technology = read_tag(self.xml_root, "technology")
        add_value_to_key(self.json_instance_template, "technique", add_ontology_value(technology))


USAGE = f"Usage: python {sys.argv[0]} [configuration file path] [instance.json output file path]"


def main():
    args = sys.argv[1:]
    if not args:
        raise SystemExit(USAGE)

    with open(args[0], encoding="utf-8") as config_file:
        avu_metadata = json.load(config_file)

    output = "instance.json"
    if len(args) > 1:
        output = args[1]

    with open(avu_metadata["instance_file"], encoding="utf-8") as instance_file:
        json_instance_template = json.load(instance_file)

    schema_url = "https://raw.githubusercontent.com/MaastrichtUniversity/dh-mdr/DHS-1825/core/static/assets/schemas/DataHub_extended_schema.json?token=GHSAT0AAAAAABQNGBMEXKMEBOGVUOHPE6E4YP3VB6Q"
    with urllib.request.urlopen(schema_url) as url:
        json_schema = json.loads(url.read().decode())

    with open(avu_metadata["xml_file"], encoding="utf-8") as xml_file:
        xml_root = ET.fromstring(xml_file.read())

    json_instance = Conversion(xml_root, json_instance_template, avu_metadata).get_instance()
    validate(instance=json_instance, schema=json_schema)

    # Write instance.json
    with open(output, "w") as instance_outfile:
        json.dump(json_instance, instance_outfile, ensure_ascii=False, indent=4)

    print(json.dumps(json_instance, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    main()
