from typing import Union, Iterator


def _find_keys(node: dict, keyword: str) -> Iterator[Union[list, dict]]:
    """
    Recursive function to find a key-pair-value based on a key inside a nested dict/json

    Parameters
    ----------
    node: dict
        Where to perform the search
    keyword: str
        The input key to search

    Returns
    -------
    Iterator[Union[list, dict]]
        Yields the result values of the search
    """
    if isinstance(node, list):
        for i in node:
            for value in _find_keys(i, keyword):
                yield value
    elif isinstance(node, dict):
        if keyword in node:
            yield node[keyword]
        for j in node.values():
            for value in _find_keys(j, keyword):
                yield value


def find_key(node: dict, keyword: str) -> Union[list, dict]:
    """
    Recursive function to find a key-pair-value based on a key inside a nested dict/json

    Parameters
    ----------
    node: dict
        Where to perform the search
    keyword: str
        The input key to search

    Returns
    -------
    Iterator[Union[list, dict]]
        Return only the first occurrence
    """
    result = list(_find_keys(node, keyword))
    if result:
        # Only return the first occurrence.
        # The schema should only contains unique ids
        return result[0]
    return []


def add_value_to_key(node: dict, keyword: str, child_node: Union[list, dict]) -> None:
    """
    Find a key-pair-value based on a key inside a nested dict/json and add the input child node into it.

    Parameters
    ----------
    node: dict
        Where to perform the search
    keyword: str
        The input key to search
    child_node:
        The child node to add
    """
    result = find_key(node, keyword)
    if isinstance(result, dict):
        result.update(child_node)
    elif isinstance(result, list):
        result.clear()
        result.extend(child_node)


def read_tag_list(root, tag):
    ret = []
    for k in root.findall(tag):
        for i in k.iter():
            if i.text is not None:
                ret.append(i.text)
    return ret


def read_text(root, tag):
    text = root.find(tag).text
    if text is None:
        return ''
    else:
        return text


def read_contacts(root):
    contacts = []
    for contact in root.findall("contact"):
        contact_object = {"FirstName": contact.find('firstName').text,
                          "LastName": contact.find('lastName').text,
                          "MidInitials": contact.find('midInitials').text,
                          "Email": contact.find('email').text,
                          "Phone": contact.find('phone').text,
                          "Address": contact.find('address').text,
                          "Affiliation": contact.find('affiliation').text,
                          "Role": contact.find('role').text}
        if not is_invalid_contact(contact_object):
            contacts.append(add_contact_value(contact))

    return contacts


def read_tag(root, tag):
    if root.find(tag).text is not None:
        # Check if the xml tag exist and if it contains an ontology class
        if root.find(tag).get("id") is not None and ":http:" in root.find(tag).get("id"):
            return {"id": root.find(tag).get("id"), "label": root.find(tag).text}
        else:
            return {"id": "", "label": root.find(tag).text}
    else:
        return {"id": "", "label": ""}


def read_tag_node(root, tag):
    node_list = []
    for i in root.iterfind(tag):
        for k in i:
            if k.text is not None:
                node_list.append(k.text)
    return node_list


def is_invalid_contact(contact):
    return contact["LastName"] is None and contact["FirstName"] is None and contact["MidInitials"] is None and contact[
        "Email"] is None and contact["Phone"] is None and contact["Address"] is None and contact[
               "Affiliation"] is None and contact["Role"] is None


def add_contact_value(contact):
    return {
        "@context": {
            "FirstName": "https://schema.metadatacenter.org/properties/89b82b7c-457b-4d85-a452-25f4aef66ead",
            "LastName": "https://schema.metadatacenter.org/properties/54ef56e8-3371-4f89-840c-74b35236b002",
            "MidInitials": "https://schema.metadatacenter.org/properties/7984939f-a9a5-4328-830a-0d389718c835",
            "Email": "https://schema.metadatacenter.org/properties/75f7c277-5071-4926-bb0a-512b9e560026",
            "Phone": "https://schema.metadatacenter.org/properties/07d636a9-4b7b-4e72-b35d-d35acf99c73c",
            "Address": "https://schema.metadatacenter.org/properties/a57912c3-6a65-46fd-86d0-b98c23046f93",
            "Affiliation": "https://schema.metadatacenter.org/properties/33626622-b8f5-44ee-8088-076d24a32088",
            "Role": "https://schema.metadatacenter.org/properties/5591dcbc-89ac-4e63-adbe-b5aa2f06ec11"
        },
        "FirstName": {
            "@value": contact.find('firstName').text
        },
        "LastName": {
            "@value": contact.find('lastName').text
        },
        "MidInitials": {
            "@value": contact.find('midInitials').text
        },
        "Email": {
            "@value": contact.find('email').text
        },
        "Phone": {
            "@value": contact.find('phone').text,
            "@type": "xsd:decimal"
        },
        "Address": {
            "@value": contact.find('address').text
        },
        "Affiliation": {
            "@value": contact.find('affiliation').text
        },
        "Role": {
            "@value": contact.find('role').text
        },
        "@id": "https://repo.metadatacenter.org/template-element-instances/a4ac16dc-2534-4f4f-b777-24d938403a63"
    }
