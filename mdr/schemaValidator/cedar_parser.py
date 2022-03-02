from abc import abstractmethod
import json

from cedar_utils import CedarSchemaName


class CedarParser:
    @staticmethod
    def open_and_load(schema_file) -> dict:
        """
        Open the file provided by the user and parse the JSON out of it

        Returns
        -------
        schema: dict
            The parsed JSON
        """
        schema = json.loads(schema_file)
        return schema

    def parse_root_node(self, schema: dict) -> None:
        nodes = schema["_ui"]["order"]
        for node_id in nodes:
            node = schema["properties"][node_id]
            self.parse_child_node(node, node_id, "root")

    def parse_child_node(self, node, node_id, parent=None) -> CedarSchemaName:
        schema_name = None
        if node["type"] == "object" and "inputType" in node["_ui"]:
            schema_name = self.parse_single_object_field(node, node_id, parent)
        elif node["type"] == "object" and "order" in node["_ui"]:
            self.parse_nested_object_field(node, node_id, parent)
        elif node["type"] == "array" and "inputType" in node["items"]["_ui"]:
            schema_name = self.parse_single_array_field(node, node_id, parent)
        elif node["type"] == "array" and "order" in node["items"]["_ui"]:
            self.parse_nested_array_field(node, node_id, parent)

        return schema_name

    def parse_schema_name(self, node_schema_name: str, node_id: str) -> CedarSchemaName:
        """
        Parses a string schema name into a CedarSchemaName enum

        Parameters
        ----------
        node_schema_name: str
            The schema name in a string variant
        node_id: str
            The id of the node

        Returns
        -------
        The schema name as CedarSchemaName

        """
        schema_name = None

        if node_schema_name == "textfield":
            schema_name = CedarSchemaName.TEXTFIELD
        elif node_schema_name == "temporal":
            schema_name = CedarSchemaName.TEMPORAL
        elif node_schema_name == "email":
            schema_name = CedarSchemaName.EMAIL
        elif node_schema_name == "numeric":
            schema_name = CedarSchemaName.NUMERIC
        elif node_schema_name == "link":
            schema_name = CedarSchemaName.LINK
        elif node_schema_name == "textarea":
            schema_name = CedarSchemaName.TEXTAREA
        elif node_schema_name == "radio":
            schema_name = CedarSchemaName.RADIO
        elif node_schema_name == "checkbox":
            schema_name = CedarSchemaName.CHECKBOX
        elif node_schema_name == "page-break":
            schema_name = CedarSchemaName.PAGE_BREAK
        elif node_schema_name == "section-break":
            schema_name = CedarSchemaName.SECTION_BREAK
        else:
            self.parse_unknown_schema_name(node_schema_name, node_id)
        return schema_name

    @abstractmethod
    def parse_unknown_schema_name(self, node_schema_name=None, node_id=None):
        pass

    @abstractmethod
    def parse_single_object_field(self, node, node_id=None, parent=None):
        pass

    @abstractmethod
    def parse_nested_object_field(self, node, node_id=None, parent=None):
        pass

    @abstractmethod
    def parse_single_array_field(self, node, node_id=None, parent=None):
        pass

    @abstractmethod
    def parse_nested_array_field(self, node, node_id=None, parent=None):
        pass
