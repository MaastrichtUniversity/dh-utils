def add_date_value(value):
    return {
        "@value": value,
        "@type": "xsd:date"
    }


def add_publications_values(articles):
    ret = []
    for article in articles:
        ret.append({
            "relationType": {
                "rdfs:label": "Is Documented By",
                "@id": "http://vocab.fairdatacollective.org/gdmt/IsDocumentedBy"
            },
            "relatedResourceIdentifierType": {
                "rdfs:label": "DOI",
                "@id": "http://vocab.fairdatacollective.org/gdmt/DOI"
            },
            "@id": "https://repo.metadatacenter.org/template-elements/c13bdf4e-46a5-4364-925a-c33d33c13256",
            "relatedResourceIdentifier": {
                "@value": article
            },
            "@context": {
                "relationType": "http://rs.tdwg.org/dwc/terms/relationshipOfResource",
                "relatedResourceIdentifierType": "http://schema.org/propertyID",
                "relatedResourceIdentifier": "http://purl.org/dc/terms/identifier"
            }
        })
    return ret


def add_factors_values(factors):
    ret = []
    for factor in factors:
        ret.append({
            "@value": factor
        })
    return ret


def add_ontology_value(value):
    return {
        "@id": value.split("::")[0],
        "rdfs:label": value.split("::")[1]
    }
