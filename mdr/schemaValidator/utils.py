from enum import Enum


class Severities(Enum):
    WARNING = "WARNING"
    ERROR = "ERROR"


class CedarUtils:
    ERROR_COUNT = 0
    WARNING_COUNT = 0

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
            "datasetIdentifier": {
                "type": "object",
                "_ui": {"inputType": "textfield", "hidden": True},
                "_valueConstraints": {"requiredValue": False, "defaultValue": ""},
            },
            "datasetIdentifierType": {
                "type": "object",
                "_ui": {"inputType": "textfield", "hidden": True},
                "_valueConstraints": {
                    "requiredValue": True,
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
