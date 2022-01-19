import json
import xml.etree.cElementTree as ET

from jsonld_utils import *
from xml_utils import *


# from jsonschema import validate


class Conversion:
    def __init__(self, xml_root, json_instance_template, avu_metadata):
        self.xml_root = xml_root
        self.json_instance_template = json_instance_template
        self.avu_metadata = avu_metadata

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
        self.add_extended_date()
        self.add_extended_experiment()

    def add_identifier(self):
        # "1_Identifier":
        pid = self.avu_metadata["PID"]
        add_value_to_key(self.json_instance_template, "datasetIdentifier", {"@value": pid})

    def add_creator(self):
        # "2_Creator":
        # creator = self.avu_metadata["PID"]
        add_value_to_key(self.json_instance_template, "2_Creator",
                         {"creatorGivenName": self.avu_metadata["creatorGivenName"]})
        add_value_to_key(self.json_instance_template, "2_Creator",
                         {"creatorFamilyName": self.avu_metadata["creatorFamilyName"]})
        add_value_to_key(self.json_instance_template, "2_Creator",
                         {"creatorAffiliation": self.avu_metadata["creatorAffiliation"]})
        add_value_to_key(self.json_instance_template, "2_Creator",
                         {"creatorIdentifierScheme": self.avu_metadata["creatorIdentifierScheme"]})
        add_value_to_key(self.json_instance_template, "2_Creator",
                         {"creatorIdentifierSchemeIRI": self.avu_metadata["creatorIdentifierSchemeIRI"]})

    def add_title(self):
        # "3_Title":
        title = read_text(self.xml_root, 'title')
        add_value_to_key(self.json_instance_template, "title", {"@value": title})

    def add_publisher(self):
        # "4_Publisher":
        pass

    def add_subject(self):
        # "6_Subject":

        factors = read_tag_node(self.xml_root, "factors")
        add_value_to_key(self.json_instance_template, "Factors", add_factors_values(factors))

    def add_contributor(self):
        # "7_Contributor":
        pass

    def add_contact(self):
        # "7_ContactPerson":
        contacts = read_contacts(self.xml_root)
        add_value_to_key(self.json_instance_template, "ContactsIslandora", contacts)

    def add_date(self):
        # "8_Date":
        date = self.avu_metadata["submissionDate"]
        add_value_to_key(self.json_instance_template, "Date", {"@value": date})

    def add_resource_type(self):
        # "10_ResourceType":
        pass

    def add_related_identifier(self):
        # "12_RelatedIdentifier":
        articles = read_tag_list(self.xml_root, "article")
        add_value_to_key(self.json_instance_template, "12_RelatedIdentifier", add_publications_values(articles))

    def add_description(self):
        # "17_Description":
        description = read_text(self.xml_root, 'description')
        add_value_to_key(self.json_instance_template, "Description", {"@value": description})

    def add_extended_date(self):
        # "Extended_Date":
        date = read_text(self.xml_root, "date")
        add_value_to_key(self.json_instance_template, "datasetDate", {"@value": date})

    def add_extended_experiment(self):
        # "Extended_Experiment":
        organism = read_tag(self.xml_root, "organism")
        result_organism = f"{organism['id']}::{organism['label']}"
        add_value_to_key(self.json_instance_template, "organism", add_ontology_value(result_organism))

        tissue = read_tag(self.xml_root, "tissue")
        result_tissue = f"{tissue['id']}::{tissue['label']}"
        add_value_to_key(self.json_instance_template, "tissue", add_ontology_value(result_tissue))

        technology = read_tag(self.xml_root, "technology")
        result_technology = f"{technology['id']}::{technology['label']}"
        add_value_to_key(self.json_instance_template, "technique", add_ontology_value(result_technology))


def main():
    avu_metadata = {
        "PID": "https://hdl.handle.net/21.T12996/P000000002C000000003",
        "creatorIdentifier": "0000-0000-0000-0000",
        "creatorIdentifierSchemeIRI": {
            "rdfs:label": "ORCiD",
            "@id": "https://orcid.org/"
        },
        "creatorGivenName": {
            "@value": "Maarten"
        },
        "creatorAffiliation": {},
        "creatorIdentifierScheme": {
            "rdfs:label": "ORCiD",
            "@id": "https://orcid.org/"
        },
        "creatorFamilyName": {
            "@value": "Coonen"
        },
        "submissionDate": "2022-01-01"
    }

    with open("instance_template.json", encoding='utf-8') as instance_file:
        json_instance_template = json.load(instance_file)

    with open("DataHub_extended_schema.json", encoding='utf-8') as schema_file:
        template_schema = json.load(schema_file)

    with open("metadata.xml", encoding='utf-8') as xml_file:
        xml_root = ET.fromstring(xml_file.read())

    Conversion(xml_root, json_instance_template, avu_metadata)
    # validate(instance=json_instance_template, schema=template_schema)

    print(json.dumps(json_instance_template, ensure_ascii=False, indent=4))


if __name__ == "__main__":
    main()
