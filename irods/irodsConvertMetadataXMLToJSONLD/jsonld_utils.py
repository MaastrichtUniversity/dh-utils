import json


def add_date_value(value):
    return {"@value": value, "@type": "xsd:date"}


def add_publications_values(articles):
    ret = []
    for article in articles:
        ret.append(
            {
                "relationType": {
                    "rdfs:label": "Is Documented By",
                    "@id": "http://vocab.fairdatacollective.org/gdmt/IsDocumentedBy",
                },
                "relatedResourceIdentifierType": {
                    "rdfs:label": "DOI",
                    "@id": "http://vocab.fairdatacollective.org/gdmt/DOI",
                },
                "@id": "https://repo.metadatacenter.org/template-elements/c13bdf4e-46a5-4364-925a-c33d33c13256",
                "relatedResourceIdentifier": {"@value": article},
                "@context": {
                    "relationType": "http://rs.tdwg.org/dwc/terms/relationshipOfResource",
                    "relatedResourceIdentifierType": "http://schema.org/propertyID",
                    "relatedResourceIdentifier": "http://purl.org/dc/terms/identifier",
                },
            }
        )
    return ret


def add_array_ontology_value(value):
    ret = {}
    if value["id"] != "" and "http" in value["id"]:
        ontology_id = "http" + value["id"].split("http")[1]
        ret = {"@id": ontology_id, "rdfs:label": value["label"]}
    return [ret]


def format_common_value(value: str) -> dict:
    """
    Format the given value to match the common json-ld standard.

    Parameters
    ----------
    value: str
        The user input value to format

    Returns
    -------
    dict
        The json-ld formatted value
    """
    return {"@value": value}


def add_creator(avu_metadata):
    full_name = f"{avu_metadata['creatorGivenName']} {avu_metadata['creatorFamilyName']}"
    ret = {
        "creatorGivenName": format_common_value(avu_metadata["creatorGivenName"]),
        "creatorFamilyName": format_common_value(avu_metadata["creatorFamilyName"]),
        "creatorFullName": format_common_value(full_name),
        "creatorIdentifier": format_common_value("0000-0000-0000-0000"),
        "creatorAffiliation": {},
        "creatorIdentifierScheme": {"@id": "https://orcid.org/", "rdfs:label": "ORCiD"},
        "creatorIdentifierSchemeIRI": {"@id": "https://orcid.org/", "rdfs:label": "ORCiD"},
    }
    return ret


def add_keywords(keywords):
    ret = []
    for keyword in keywords:
        ret.append(
            {
                "@context": {
                    "subjectSchemeIRI": "http://vocab.fairdatacollective.org/gdmt/hasSubjectSchemeIRI",
                    "valueURI": "https://schema.metadatacenter.org/properties/af9c45ec-d971-4056-a6c2-5ce930b9b181",
                    "Subject": "https://schema.metadatacenter.org/properties/71f1a80c-d59e-4d92-a084-4f22f219cb6e",
                },
                "subjectSchemeIRI": {"@value": None},
                "valueURI": {},
                "@id": "https://repo.metadatacenter.org/template-elements/fc4e957d-637c-4a00-b371-d9e981ce3af4",
                "Subject": {"@value": keyword},
            }
        )

    return ret


def add_contact_affiliation(affiliation, affiliation_mapping):
    ret = {}
    if affiliation in affiliation_mapping:
        ret = affiliation_mapping[affiliation]
    return ret


def add_contact_full_name(contact):
    if contact["FirstName"] is None:
        raise Exception("FirstName is null")
    if contact["LastName"] is None:
        raise Exception("LastName is null")
    ret = f"{contact['FirstName']} {contact['LastName']}"
    if contact["MidInitials"]:
        ret = f"{contact['FirstName']} {contact['MidInitials']} {contact['LastName']}"
    return ret


def add_contact_person(contacts, affiliation_mapping_path):
    with open(affiliation_mapping_path, encoding="utf-8") as mapping_file:
        affiliation_mapping = json.load(mapping_file)
    ret = []
    for contact in contacts:
        ret.append(
            {
                "contactNameIdentifierScheme": {},
                "contactNameIdentifier": {"@value": None},
                "contactFullName": {"@value": add_contact_full_name(contact)},
                "contactAffiliation": add_contact_affiliation(contact["Affiliation"], affiliation_mapping),
                "contactPersonRole": {"@value": contact["Role"]},
                "contactEmail": {"@value": contact["Email"]},
                "contactPersonPhone": {"@value": contact["Phone"]},
                "contactFamilyName": {"@value": contact["LastName"]},
                "contactGivenName": {"@value": contact["FirstName"]},
                "contactType": {"rdfs:label": "contact person", "@id": "http://purl.org/zonmw/generic/10089"},
                "@context": {
                    "contactNameIdentifierScheme": "https://schema.metadatacenter.org/properties/98a4370e-4712-482e-9ba8-95eb508250d4",
                    "contactFullName": "https://schema.metadatacenter.org/properties/9cc96e17-345e-43c1-955d-9777ef8136aa",
                    "contactNameIdentifier": "https://schema.metadatacenter.org/properties/2d775625-b775-47c9-86a9-25b6ec514a94",
                    "contactAffiliation": "https://schema.metadatacenter.org/properties/488e6114-b24f-4bf6-83b0-45a33abdabf6",
                    "contactPersonRole": "https://schema.metadatacenter.org/properties/2db8b77d-450f-4435-a5ff-cd8f849d6725",
                    "contactEmail": "https://schema.metadatacenter.org/properties/72eb0553-76b7-4ef2-898f-694aa015cdd4",
                    "contactPersonPhone": "https://schema.metadatacenter.org/properties/d99194e1-183f-4dc8-9af9-3efbd81b9dac",
                    "contactFamilyName": "https://schema.metadatacenter.org/properties/510d9317-3658-429b-b773-8f9c0d288668",
                    "contactGivenName": "https://schema.metadatacenter.org/properties/1b2e719d-c7cc-4db0-b6f8-22ccdf43a387",
                    "contactType": "https://schema.metadatacenter.org/properties/4d0bd488-6d4a-4388-bfa9-3cbb1d941afb",
                },
                "@id": "https://repo.metadatacenter.org/template-elements/00011dcd-573f-40dc-8453-b1e4a238a481",
            }
        )

    return ret


def add_pi_contact(pi):
    return [
        {
            "contactType": {"@id": "http://purl.org/zonmw/generic/10089", "rdfs:label": "contact person"},
            "contactFullName": {"@value": pi["contributorFullName"]},
            "contactGivenName": {"@value": pi["contributorGivenName"]},
            "contactFamilyName": {"@value": pi["contributorFamilyName"]},
            "contactEmail": {"@value": pi["contributorEmail"]},
            "contactNameIdentifier": {"@value": None},
            "contactNameIdentifierScheme": {},
            "contactAffiliation": {},
            "contactPersonPhone": {"@value": None},
            "contactPersonRole": {"@value": None},
            "@id": "https://repo.metadatacenter.org/template-elements/00011dcd-573f-40dc-8453-b1e4a238a481",
            "@context": {
                "contactType": "https://schema.metadatacenter.org/properties/4d0bd488-6d4a-4388-bfa9-3cbb1d941afb",
                "contactFullName": "https://schema.metadatacenter.org/properties/9cc96e17-345e-43c1-955d-9777ef8136aa",
                "contactGivenName": "https://schema.metadatacenter.org/properties/1b2e719d-c7cc-4db0-b6f8-22ccdf43a387",
                "contactFamilyName": "https://schema.metadatacenter.org/properties/510d9317-3658-429b-b773-8f9c0d288668",
                "contactEmail": "https://schema.metadatacenter.org/properties/72eb0553-76b7-4ef2-898f-694aa015cdd4",
                "contactNameIdentifier": "https://schema.metadatacenter.org/properties/2d775625-b775-47c9-86a9-25b6ec514a94",
                "contactNameIdentifierScheme": "https://schema.metadatacenter.org/properties/98a4370e-4712-482e-9ba8-95eb508250d4",
                "contactAffiliation": "https://schema.metadatacenter.org/properties/488e6114-b24f-4bf6-83b0-45a33abdabf6",
                "contactPersonPhone": "https://schema.metadatacenter.org/properties/d99194e1-183f-4dc8-9af9-3efbd81b9dac",
                "contactPersonRole": "https://schema.metadatacenter.org/properties/2db8b77d-450f-4435-a5ff-cd8f849d6725",
            },
        }
    ]


def add_contributors(contributors):
    ret = []
    for contributor in contributors.values():
        ret.append(
            {
                "contributorIdentifierScheme": {"@id": "https://orcid.org/", "rdfs:label": "ORCiD"},
                "contributorIdentifier": {"@value": None},
                "contributorAffiliation": {},
                "contributorFullName": {"@value": contributor["contributorFullName"]},
                "contributorGivenName": {"@value": contributor["contributorGivenName"]},
                "contributorFamilyName": {"@value": contributor["contributorFamilyName"]},
                "contributorEmail": {"@value": contributor["contributorEmail"]},
                "contributorType": contributor["contributorType"],
                "@id": "https://repo.metadatacenter.org/template-elements/1d979a88-1028-421d-a124-11b5011f278a",
                "@context": {
                    "contributorIdentifierScheme": "https://schema.metadatacenter.org/properties/264bff35-9c7e-4a84-a722-712217dfa232",
                    "contributorAffiliation": "https://schema.metadatacenter.org/properties/73214405-3002-4fde-8f6c-b012faf907ec",
                    "contributorFullName": "https://schema.metadatacenter.org/properties/272d6c5e-467c-4c01-a513-23b8df92585d",
                    "contributorIdentifier": "https://schema.metadatacenter.org/properties/4636604a-6a42-4257-8a34-b8c68627cf32",
                    "contributorFamilyName": "https://schema.metadatacenter.org/properties/510d9317-3658-429b-b773-8f9c0d288668",
                    "contributorType": "https://schema.metadatacenter.org/properties/4d0bd488-6d4a-4388-bfa9-3cbb1d941afb",
                    "contributorGivenName": "https://schema.metadatacenter.org/properties/1b2e719d-c7cc-4db0-b6f8-22ccdf43a387",
                    "contributorEmail": "https://schema.metadatacenter.org/properties/72eb0553-76b7-4ef2-898f-694aa015cdd4",
                },
            }
        )

    return ret
