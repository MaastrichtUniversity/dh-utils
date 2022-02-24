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


def parse_schema_name(element_schema_name: str, node_id: str) -> Tuple[Optional[CedarSchemaName], int]:
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
    The amount of errors that occurred in the execution of this method

    """
    schema_name = None
    errors = 0

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
        log_message("ERROR", node_id, f"schema_name '{element_schema_name}' is not allowed for node")
        errors += 1
    return schema_name, errors


def log_message(severity: str, node_id: str, message: str):
    """
    Log a message to the console

    Parameters
    ----------
    severity: str
        The severity of the message, e.g. "ERROR", "WARNING", "INFO" etc.
    node_id: str
        The ID of the concerning node
    message: str
        The message to post to the console
    """
    print(f"\t {severity} (id: '{node_id}'): {message}")
