from enum import Enum


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
