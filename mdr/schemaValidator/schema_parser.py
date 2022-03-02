from cedar_parser import CedarParser, CedarSchemaName
from schema_validator import SchemaValidator
from utils import CedarUtils, Severities


class SchemaParser(CedarParser):
    def __init__(self, args):
        self.file = args.file
        self.utils = CedarUtils()
        self.cedar_validator = SchemaValidator(self.utils)

    def validate(self):
        """
        Validate the schema
        """
        schema = None
        try:
            schema = self.open_and_load(self.file.read())
        except ValueError as e:
            self.utils.log_message(Severities.ERROR, "", f"encountered while parsing the schema as JSON: '{e}'")
        if schema:
            print(f"Starting basic validation of '{self.file.name}'")
            self.parse_root_node(schema)
            print("-" * 65)
            print(f"Starting general schema validation of '{self.file.name}'")
            self.cedar_validator.validate_general_fields(schema)

    def parse_unknown_schema_name(self, node_schema_name=None, node_id=None):
        self.utils.log_message(Severities.ERROR, node_id, f"schema_name '{node_schema_name}' is not allowed for node")

    def parse_child_node(self, node, node_id, parent=None) -> CedarSchemaName:
        self.cedar_validator.check_duplicate_node_id(node_id)

        schema_name = super().parse_child_node(node, node_id, parent)

        self.cedar_validator.handle_field_specific_validation(schema_name, node, node_id)
        return schema_name

    def parse_single_object_field(self, node, node_id=None, parent=None) -> CedarSchemaName:
        """
        Validates a single field (singular --> object)

        Parameters
        ----------
        node: dict
            The node to validate
        node_id: str
            The ID of the node for reference
        parent: str
            The parent's id of the current node

        Returns
        -------
        schema_name: CedarSchemaName
            The schema name enum
        """
        schema_name = self.parse_schema_name(node["_ui"]["inputType"], node_id)
        return schema_name

    def parse_nested_object_field(self, node, node_id=None, parent=None):
        """
        This means we are dealing with a singular formset, which means we need to recurse back
        for every element in the formset to get the schema_name of the fields

        Parameters
        ----------
        node: dict
            The node to validate
        node_id: str
            The ID of the node for reference
        parent: str
            The parent's id of the current node
        """
        for field_id in node["_ui"]["order"]:
            current_field = node["properties"][field_id]
            self.cedar_validator.check_nested_formset(current_field, field_id)
            self.parse_child_node(current_field, field_id)

    def parse_single_array_field(self, node, node_id=None, parent=None) -> CedarSchemaName:
        """
        Validates a single field (multiple --> array)

        Parameters
        ----------
        node: dict
            The node to validate
        node_id: str
            The ID of the node for reference
        parent: str
            The parent's id of the current node

        Returns
        -------
        schema_name: CedarSchemaName
            The schema name enum
        """
        schema_name = self.parse_schema_name(node["items"]["_ui"]["inputType"], node_id)
        return schema_name

    def parse_nested_array_field(self, node, node_id=None, parent=None):
        """
        This means we are dealing with a formset with 'multiple', which means we need to recurse back
        for every element in the formset to get the schema_name of the fields

        Parameters
        ----------
        node: dict
            The node to validate
        node_id: str
            The ID of the node for reference
        parent: str
            The parent's id of the current node
        """
        for field_id in node["items"]["_ui"]["order"]:
            current_field = node["items"]["properties"][field_id]
            self.cedar_validator.check_nested_formset(current_field, field_id)
            self.parse_child_node(current_field, field_id)
