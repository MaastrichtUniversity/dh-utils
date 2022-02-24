import argparse
import json

from utils import parse_schema_name, CedarSchemaName, log_message


class SchemaValidator:
    ERROR_COUNT = 0
    WARNING_COUNT = 0
    PAGE_BREAK = False

    def __init__(self, args):
        self.file = args.file

    def validate(self):
        """
        Validate the schema
        """
        schema = self.open_and_parse()
        if schema:
            nodes = schema["_ui"]["order"]
            for node_id in nodes:
                node = schema["properties"][node_id]
                self.validate_node(node, node_id)

    def open_and_parse(self) -> dict:
        """
        Open the file provided by the user and parse the JSON out of it

        Returns
        -------
        schema: dict
            The parsed JSON
        """
        schema = None
        try:
            schema = json.loads(self.file.read())
        except ValueError as e:
            self.ERROR_COUNT += 1
            log_message("ERROR", "", f"encountered while parsing the schema as JSON: '{e}'")
        return schema

    # region Node validation
    def validate_node(self, node: dict, node_id: str):
        """
        Validate the node. Is a recursive operation.

        Parameters
        ----------
        node: dict
            The node to validate
        node_id: str
            The ID of the node for reference
        """
        schema_name = None
        if node["type"] == "object" and "inputType" in node["_ui"]:
            schema_name = self.validate_single_field(node, node_id)
        elif node["type"] == "object" and "order" in node["_ui"]:
            self.validate_nested_field(node)
        elif node["type"] == "array" and "inputType" in node["items"]["_ui"]:
            schema_name = self.validate_single_block_field(node, node_id)
        elif node["type"] == "array" and "order" in node["items"]["_ui"]:
            self.validate_nested_block_field(node)

        self.handle_field_specific_validation(schema_name, node, node_id)

    def validate_single_field(self, node: dict, node_id: str) -> CedarSchemaName:
        """
        Validates a single field (singular --> object)

        Parameters
        ----------
        node: dict
            The node to validate
        node_id: str
            The ID of the node for reference

        Returns
        -------
        schema_name: CedarSchemaName
            The schema name enum
        """
        schema_name, errors = parse_schema_name(node["_ui"]["inputType"], node_id)
        self.ERROR_COUNT += errors
        return schema_name

    def validate_nested_field(self, node: dict):
        """
        This means we are dealing with a singular formset, which means we need to recurse back
        for every element in the formset to get the schema_name of the fields

        Parameters
        ----------
        node: dict
            The node to validate
        """
        for field_id in node["_ui"]["order"]:
            current_field = node["properties"][field_id]
            self.check_nested_formset(current_field, field_id)
            self.validate_node(current_field, field_id)

    def validate_single_block_field(self, node: dict, node_id: str) -> CedarSchemaName:
        """
        Validates a single field (multiple --> array)

        Parameters
        ----------
        node: dict
            The node to validate
        node_id: str
            The ID of the node for reference

        Returns
        -------
        schema_name: CedarSchemaName
            The schema name enum
        """
        schema_name, errors = parse_schema_name(node["items"]["_ui"]["inputType"], node_id)
        self.ERROR_COUNT += errors
        return schema_name

    def validate_nested_block_field(self, node: dict):
        """
        This means we are dealing with a formset with 'multiple', which means we need to recurse back
        for every element in the formset to get the schema_name of the fields

        Parameters
        ----------
        node: dict
            The node to validate
        """
        for field_id in node["items"]["_ui"]["order"]:
            current_field = node["items"]["properties"][field_id]
            self.check_nested_formset(current_field, field_id)
            self.validate_node(current_field, field_id)

    # endregion
    # region Field specific validators

    def handle_field_specific_validation(self, schema_name: CedarSchemaName, node: dict, node_id: str):
        """
        This method checks the DH-specific rules for the schema

        Parameters
        ----------
        schema_name: CedarSchemaName
            The schema_name of the field to check
        node: dict
            The node to validate
        node_id: str
            The ID of the node for reference

        """
        if schema_name == CedarSchemaName.PAGE_BREAK:
            self.validate_page_break(node_id)
        elif schema_name == CedarSchemaName.TEXTAREA:
            self.validate_textarea(node, node_id)

    def validate_page_break(self, node_id: str):
        """
        Validates if there is only (a maximum of) ONE page-break

        Parameters
        ----------
        node_id: str
            The ID of the node for reference

        """
        if self.PAGE_BREAK:
            self.WARNING_COUNT += 1
            log_message("WARNING", node_id, "Only 1 page break is rendered in MDR")
        self.PAGE_BREAK = True

    def validate_textarea(self, node, node_id):
        """
        Validates if the textarea is not 'multiple' because that is not allowed

        Parameters
        ----------
        node: dict
            The node to validate
        node_id: str
            The ID of the node for reference

        """
        if node["type"] == "array":
            self.ERROR_COUNT += 1
            log_message("ERROR", node_id, "Textarea can not be multiple")

    # endregion
    # region Formset validators

    def check_nested_formset(self, node, node_id):
        """
        Check if the formset passed is nested, because that is not allowed

        Parameters
        ----------
        node: dict
            The node to validate
        node_id: str
            The ID of the node for reference
        """
        if "items" in node:
            field_ui = node["items"]["_ui"]
        else:
            field_ui = node["_ui"]
        if "order" in field_ui:
            self.ERROR_COUNT += 1
            log_message("ERROR", node_id, "nested formset for field_id")

    # endregion


def main():
    parser = argparse.ArgumentParser(description="validate schema description")
    parser.add_argument("file", type=argparse.FileType("r"), help="Path to the schema to validate")
    args = parser.parse_args()

    if not args.file.name.endswith(".json"):
        exit(f"Invalid file path provided. Should be a '.json' file")

    print(f"Starting validation of {args.file.name}")
    validator = SchemaValidator(args)
    validator.validate()
    if not validator.ERROR_COUNT:
        print("Validation result: OK. No errors found.")
        print(f"\t {validator.WARNING_COUNT} warning(s) encountered")
    else:
        print("Validation result: NOT OK - errors found")
        print(f"\t {validator.ERROR_COUNT} error(s) encountered")
        print(f"\t {validator.WARNING_COUNT} warning(s) encountered")


if __name__ == "__main__":
    main()
