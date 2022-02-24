from enum import Enum
from typing import Tuple, Optional


class CedarSchemaName(Enum):
    TEXTFIELD = 1
    TEMPORAL = 2
    EMAIL = 3
    NUMERIC = 4
    LINK = 5
    TEXTAREA = 6
    RADIO = 7
    CHECKBOX = 8
    PAGE_BREAK = 9
    SECTION_BREAK = 10
    # Not supported (yet)
    LIST = 11
    PHONE_NUMBER = 12
    ATTRIBUTE_VALUE = 13


class Severities(Enum):
    WARNING = "WARNING"
    ERROR = "ERROR"


class CedarUtils:
    ERROR_COUNT = 0
    WARNING_COUNT = 0

    def parse_schema_name(self, element_schema_name: str, node_id: str) -> CedarSchemaName:
        """
        Parses a string schema name into a CedarSchemaName enum

        Parameters
        ----------
        element_schema_name: str
            The schema name in a string variant
        node_id: str
            The id of the node

        Returns
        -------
        The schema name as CedarSchemaName

        """
        schema_name = None

        if element_schema_name == "textfield":
            schema_name = CedarSchemaName.TEXTFIELD
        elif element_schema_name == "temporal":
            schema_name = CedarSchemaName.TEMPORAL
        elif element_schema_name == "email":
            schema_name = CedarSchemaName.EMAIL
        elif element_schema_name == "numeric":
            schema_name = CedarSchemaName.NUMERIC
        elif element_schema_name == "link":
            schema_name = CedarSchemaName.LINK
        elif element_schema_name == "textarea":
            schema_name = CedarSchemaName.TEXTAREA
        elif element_schema_name == "radio":
            schema_name = CedarSchemaName.RADIO
        elif element_schema_name == "checkbox":
            schema_name = CedarSchemaName.CHECKBOX
        elif element_schema_name == "page-break":
            schema_name = CedarSchemaName.PAGE_BREAK
        elif element_schema_name == "section-break":
            schema_name = CedarSchemaName.SECTION_BREAK
        else:
            self.log_message(Severities.ERROR, node_id, f"schema_name '{element_schema_name}' is not allowed for node")
        return schema_name

    def log_message(self, severity: Severities, node_id: str, message: str):
        """
        Log a message to the console

        Parameters
        ----------
        severity: Severities
            The severity of the message, e.g. "ERROR", "WARNING", "INFO" etc.
        node_id: str
            The ID of the concerning node
        message: str
            The message to post to the console
        """
        print(f"\t {severity.value} (id: '{node_id}'): {message}")
        if severity == Severities.ERROR:
            self.ERROR_COUNT += 1
        elif severity == Severities.WARNING:
            self.WARNING_COUNT += 1


GENERAL_SCHEMA_FIELDS_TO_CHECK = {
    "1_Identifier": {
        "type": "object",
        "fields": {
            "datasetIdentifier": {"type": "object", "_ui": {"inputType": "textfield", "hidden": True}},
            "datasetIdentifierType": {"type": "object", "_ui": {"inputType": "textfield", "hidden": True}},
        },
    },
    "2_Creator": {
        "type": "object",
        "fields": {
            "creatorIdentifier": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
                "_valueConstraints": {"defaultValue": "0000-0000-0000-0000"},
            },
            "creatorIdentifierScheme": {
                "type": "object",
                "_ui": {"inputType": "textfield", "hidden": True},
                "_valueConstraints": {
                    "branches": [
                        {
                            "source": "Ontology for Generic Dataset Metadata Template (FDC-GDMT)",
                            "acronym": "FDC-GDMT",
                            "uri": "http://vocab.fairdatacollective.org/gdmt/IdentifierScheme",
                            "name": "Identifier Scheme",
                            "maxDepth": 0,
                        }
                    ],
                    "defaultValue": {"termUri": "https://orcid.org/", "rdfs:label": "ORCiD"},
                },
            },
            "creatorIdentifierSchemeIRI": {
                "type": "object",
                "_ui": {"inputType": "textfield", "hidden": True},
                "_valueConstraints": {
                    "branches": [
                        {
                            "source": "Ontology for Generic Dataset Metadata Template (FDC-GDMT)",
                            "acronym": "FDC-GDMT",
                            "uri": "http://vocab.fairdatacollective.org/gdmt/IdentifierScheme",
                            "name": "Identifier Scheme",
                            "maxDepth": 0,
                        }
                    ],
                    "defaultValue": {"termUri": "https://orcid.org/", "rdfs:label": "ORCiD"},
                },
            },
            "creatorAffiliation": {
                "type": "object",
                "_ui": {"inputType": "textfield", "hidden": True},
                "_valueConstraints": {"requiredValue": False},
            },
            "creatorGivenName": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
                "_valueConstraints": {"requiredValue": True},
            },
            "creatorFamilyName": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
                "_valueConstraints": {"requiredValue": True},
            },
            "creatorFullName": {
                "type": "object",
                "_ui": {"inputType": "textfield", "hidden": True},
                "_valueConstraints": {"requiredValue": True},
            },
        },
    },
    "3_Title": {
        "type": "object",
        "fields": {
            "title": {"type": "object", "_ui": {"inputType": "textfield"}, "_valueConstraints": {"requiredValue": True}}
        },
    },
    "4_Publisher": {
        "type": "object",
        "fields": {
            "Publisher": {
                "type": "object",
                "_ui": {"inputType": "textfield", "hidden": True},
                "_valueConstraints": {"requiredValue": True, "defaultValue": "DataHub"},
            },
        },
    },
    "6_Subject": {
        "type": "array",
        "fields": {
            "Subject": {
                "type": "object",
                "_ui": {
                    "inputType": "textfield",
                },
            },
            "subjectSchemeIRI": {
                "type": "object",
                "_ui": {"inputType": "textfield", "hidden": True},
            },
            "valueURI": {
                "type": "object",
                "_ui": {"inputType": "textfield", "hidden": True},
                "_valueConstraints": {
                    "ontologies": [
                        {
                            "numTerms": 28815,
                            "acronym": "EFO",
                            "name": "Experimental Factor Ontology",
                            "uri": "https://data.bioontology.org/ontologies/EFO",
                        }
                    ],
                },
            },
        },
    },
    "7_ContactPerson": {
        "type": "array",
        "fields": {
            "contactType": {
                "type": "object",
                "_ui": {"inputType": "textfield", "hidden": True},
                "_valueConstraints": {
                    "branches": [
                        {
                            "source": "undefined (ZONMW-GENERIC)",
                            "acronym": "ZONMW-GENERIC",
                            "uri": "http://purl.org/zonmw/generic/10075",
                            "name": "contributor type",
                            "maxDepth": 0,
                        }
                    ],
                    "defaultValue": {"termUri": "http://purl.org/zonmw/generic/10089", "rdfs:label": "contact person"},
                },
            },
            "contactFullName": {
                "type": "object",
                "_ui": {"inputType": "textfield", "hidden": True},
                "_valueConstraints": {"requiredValue": True},
            },
            "contactGivenName": {
                "type": "object",
                "_ui": {
                    "inputType": "textfield",
                },
                "_valueConstraints": {"requiredValue": True},
            },
            "contactFamilyName": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
                "_valueConstraints": {"requiredValue": True},
            },
            "contactEmail": {
                "type": "object",
                "_ui": {"inputType": "email"},
                "_valueConstraints": {"requiredValue": True},
            },
            "contactNameIdentifier": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
            },
            "contactNameIdentifierScheme": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
                "_valueConstraints": {
                    "branches": [
                        {
                            "source": "Ontology for Generic Dataset Metadata Template (FDC-GDMT)",
                            "acronym": "FDC-GDMT",
                            "uri": "http://vocab.fairdatacollective.org/gdmt/IdentifierScheme",
                            "name": "Identifier Scheme",
                            "maxDepth": 0,
                        }
                    ],
                },
            },
            "contactAffiliation": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
                "_valueConstraints": {
                    "branches": [
                        {
                            "source": "ZonMw Generic Terms (ZONMW-GENERIC)",
                            "acronym": "ZONMW-GENERIC",
                            "uri": "http://purl.org/zonmw/generic/10027",
                            "name": "institution",
                            "maxDepth": 0,
                        }
                    ],
                },
            },
        },
    },
    "7_Contributor": {
        "type": "array",
        "fields": {
            "contributorType": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
                "_valueConstraints": {
                    "branches": [
                        {
                            "source": "undefined (ZONMW-GENERIC)",
                            "acronym": "ZONMW-GENERIC",
                            "uri": "http://purl.org/zonmw/generic/10075",
                            "name": "contributor type",
                            "maxDepth": 0,
                        }
                    ],
                },
            },
            "contributorFullName": {
                "type": "object",
                "_ui": {"inputType": "textfield", "hidden": True},
                "_valueConstraints": {"requiredValue": True},
            },
            "contributorGivenName": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
                "_valueConstraints": {"requiredValue": True},
            },
            "contributorFamilyName": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
                "_valueConstraints": {"requiredValue": True},
            },
            "contributorEmail": {
                "type": "object",
                "_ui": {"inputType": "email"},
            },
            "contributorIdentifier": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
            },
            "contributorIdentifierScheme": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
                "_valueConstraints": {
                    "branches": [
                        {
                            "source": "Ontology for Generic Dataset Metadata Template (FDC-GDMT)",
                            "acronym": "FDC-GDMT",
                            "uri": "http://vocab.fairdatacollective.org/gdmt/IdentifierScheme",
                            "name": "Identifier Scheme",
                            "maxDepth": 0,
                        }
                    ],
                    "defaultValue": {"termUri": "https://orcid.org/", "rdfs:label": "ORCiD"},
                },
            },
            "contributorAffiliation": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
                "_valueConstraints": {
                    "branches": [
                        {
                            "source": "ZonMw Generic Terms (ZONMW-GENERIC)",
                            "acronym": "ZONMW-GENERIC",
                            "uri": "http://purl.org/zonmw/generic/10027",
                            "name": "institution",
                            "maxDepth": 0,
                        }
                    ],
                },
            },
        },
    },
    "8_Date": {
        "type": "object",
        "fields": {
            "datasetDate": {
                "type": "object",
                "_ui": {"inputType": "temporal"},
                "_valueConstraints": {
                    "requiredValue": True,
                },
            },
            "datasetDateType": {
                "type": "object",
                "_ui": {"inputType": "textfield", "hidden": True},
                "_valueConstraints": {
                    "requiredValue": True,
                    "defaultValue": {
                        "termUri": "http://vocab.fairdatacollective.org/gdmt/Submitted",
                        "rdfs:label": "Submitted",
                    },
                    "branches": [
                        {
                            "source": "Ontology for Generic Dataset Metadata Template (FDC-GDMT)",
                            "acronym": "FDC-GDMT",
                            "uri": "http://vocab.fairdatacollective.org/gdmt/DateType",
                            "name": "Date Type",
                            "maxDepth": 0,
                        }
                    ],
                },
            },
        },
    },
    "10_ResourceType": {
        "type": "object",
        "fields": {
            "resourceTypeDetail": {
                "type": "object",
                "_ui": {"inputType": "textfield", "hidden": True},
            },
            "resourceTypeGeneral": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
                "_valueConstraints": {
                    "branches": [
                        {
                            "source": "undefined (FDC-GDMT)",
                            "acronym": "FDC-GDMT",
                            "uri": "http://vocab.fairdatacollective.org/gdmt/ResourceTypeCategory",
                            "name": "Resource Type Category",
                            "maxDepth": 0,
                        }
                    ],
                    "defaultValue": {
                        "termUri": "http://vocab.fairdatacollective.org/gdmt/Collection",
                        "rdfs:label": "Collection",
                    },
                },
            },
        },
    },
    "12_RelatedIdentifier": {
        "type": "array",
        "fields": {
            "relatedResourceIdentifier": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
            },
            "relatedResourceIdentifierType": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
                "_valueConstraints": {
                    "branches": [
                        {
                            "source": "Ontology for Generic Dataset Metadata Template (FDC-GDMT)",
                            "acronym": "FDC-GDMT",
                            "uri": "http://vocab.fairdatacollective.org/gdmt/IdentifierType",
                            "name": "Identifier Type",
                            "maxDepth": 0,
                        }
                    ],
                },
            },
            "relationType": {
                "type": "object",
                "_ui": {"inputType": "textfield"},
                "_valueConstraints": {
                    "branches": [
                        {
                            "source": "Ontology for Generic Dataset Metadata Template (FDC-GDMT)",
                            "acronym": "FDC-GDMT",
                            "uri": "http://vocab.fairdatacollective.org/gdmt/RelationType",
                            "name": "Relation Type",
                            "maxDepth": 0,
                        }
                    ],
                },
            },
        },
    },
    "17_Description": {
        "type": "object",
        "fields": {
            "Description": {
                "type": "object",
                "_ui": {"inputType": "textarea"},
                "_valueConstraints": {"requiredValue": True},
            },
            "descriptionType": {
                "type": "object",
                "_ui": {"inputType": "textfield", "hidden": True},
                "_valueConstraints": {
                    "defaultValue": "Abstract",
                },
            },
        },
    },
}
