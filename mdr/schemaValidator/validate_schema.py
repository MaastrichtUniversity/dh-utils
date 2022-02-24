import argparse
import json

from utils import (
    CedarUtils,
    CedarSchemaName,
    GENERAL_SCHEMA_FIELDS_TO_CHECK,
    Severities,
)


class SchemaValidator:
    PAGE_BREAK = False

    def __init__(self, args):
        self.file = args.file
        self.utils = CedarUtils()

    def validate(self):
        """
        Validate the schema
        """
        schema = self.open_and_parse()
        if schema:
            nodes = schema["_ui"]["order"]
            print(f"Starting basic validation of '{self.file.name}'")
            for node_id in nodes:
                node = schema["properties"][node_id]
                self.validate_node(node, node_id)
            print(f"Starting general schema validation of '{self.file.name}'")
            self.validate_general_fields(schema)

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
            self.utils.log_message(Severities.ERROR, "", f"encountered while parsing the schema as JSON: '{e}'")
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
        schema_name = self.utils.parse_schema_name(node["_ui"]["inputType"], node_id)
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
        schema_name = self.utils.parse_schema_name(node["items"]["_ui"]["inputType"], node_id)
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
        self.validate_field_properties(node, node_id)
        if schema_name == CedarSchemaName.PAGE_BREAK:
            self.validate_page_break(node_id)
        elif schema_name == CedarSchemaName.TEXTAREA:
            self.validate_textarea(node, node_id)

    def validate_field_properties(self, node: dict, node_id: str):
        """
        Validate the properties of a single field

        Parameters
        ----------
        node: dict
            The node to validate
        node_id: str
            The ID of the node for reference


        """
        if "skos:altLabel" in node and node["skos:altLabel"]:
            self.utils.log_message(
                Severities.WARNING, node_id, "Alternative labels are not supported or rendered in MDR"
            )
        if "_valueConstraints" in node:
            value_constraints = node["_valueConstraints"]
            if "numberType" in value_constraints:
                self.utils.log_message(
                    Severities.WARNING, node_id, "The valueConstraint 'numberType' is not supported or rendered in MDR"
                )
            if "minValue" in value_constraints:
                self.utils.log_message(
                    Severities.WARNING, node_id, "The valueConstraint 'minValue' is not supported or rendered in MDR"
                )
            if "maxValue" in value_constraints:
                self.utils.log_message(
                    Severities.WARNING, node_id, "The valueConstraint 'maxValue' is not supported or rendered in MDR"
                )
            if "decimalPlace" in value_constraints:
                self.utils.log_message(
                    Severities.WARNING,
                    node_id,
                    "The valueConstraint 'decimalPlace' is not supported or rendered in MDR",
                )
            if "unitOfMeasure" in value_constraints:
                self.utils.log_message(
                    Severities.WARNING,
                    node_id,
                    "The valueConstraint 'unitOfMeasure' is not supported or rendered in MDR",
                )
            if "maxLength" in value_constraints:
                self.utils.log_message(
                    Severities.WARNING, node_id, "The valueConstraint 'maxLength' is not supported or rendered in MDR"
                )
            if "minLength" in value_constraints:
                self.utils.log_message(
                    Severities.WARNING, node_id, "The valueConstraint 'minLength' is not supported or rendered in MDR"
                )
            if "temporalType" in value_constraints:
                self.utils.log_message(
                    Severities.WARNING,
                    node_id,
                    "The valueConstraint 'temporalType' is not supported or rendered in MDR",
                )

    def validate_page_break(self, node_id: str):
        """
        Validates if there is only (a maximum of) ONE page-break

        Parameters
        ----------
        node_id: str
            The ID of the node for reference

        """
        if self.PAGE_BREAK:
            self.utils.log_message(Severities.WARNING, node_id, "Only 1 page break is rendered in MDR")
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
            self.utils.log_message(Severities.ERROR, node_id, "Textarea can not be multiple")

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
            self.utils.log_message(Severities.ERROR, node_id, "nested formset for field_id")

    # endregion
    # region General schema validation

    def validate_general_fields(self, schema):
        for key, value in GENERAL_SCHEMA_FIELDS_TO_CHECK.items():
            if key in schema["properties"]:
                element = schema["properties"][key]
                try:
                    self.check_element_is_valid(element, value)
                except KeyError as e:
                    self.utils.log_message(
                        Severities.ERROR, key, f"Required element from DataHub General not identical {e}"
                    )
            else:
                self.utils.log_message(Severities.ERROR, key, "Required element from DataHub General not found")

    def check_element_is_valid(self, element, json_to_check):
        valid = True
        if element["type"] != json_to_check["type"]:
            return False
        for field, value in json_to_check["fields"].items():
            element_to_check = (
                element["items"]["properties"][field] if element["type"] == "array" else element["properties"][field]
            )
            valid = (
                self.check_field_type_valid(field, element_to_check, value)
                and self.check_field_input_type_valid(field, element_to_check, value)
                and self.check_field_hidden_valid(field, element_to_check, value)
                and self.check_field_default_value_valid(field, element_to_check, value)
                and self.check_field_branches_valid(field, element_to_check, value)
            )
            if valid is False:
                break

        return valid

    def check_field_type_valid(self, field_id, current_field, general):
        valid = current_field["type"] == general["type"]
        if not valid:
            self.utils.log_message(
                Severities.ERROR,
                field_id,
                f"Field type not the same as general field type: '{current_field['type']}' != '{general['type']}'",
            )
        return valid

    def check_field_input_type_valid(self, field_id, current_field, general):
        valid = True
        if "_ui" in general and "inputType" in general["_ui"]:
            valid = current_field["_ui"]["inputType"] == general["_ui"]["inputType"]
        if not valid:
            self.utils.log_message(
                Severities.ERROR,
                field_id,
                f"Field input type not the same as general field type: {current_field['_ui']['inputType']} != {general['_ui']['inputType']}",
            )

        return valid

    def check_field_hidden_valid(self, field_id, current_field, general):
        valid = True
        if "_ui" in general and "hidden" in general["_ui"]:
            valid = current_field["_ui"]["hidden"] == general["_ui"]["hidden"]
        if not valid:
            self.utils.log_message(
                Severities.ERROR,
                field_id,
                f"Field 'hidden' not the same as general: {current_field['_ui']['hidden']} != {general['_ui']['hidden']}",
            )

        return valid

    def check_field_default_value_valid(self, field_id, current_field, general):
        valid = True
        if "_valueConstraints" in general and "defaultValue" in general["_valueConstraints"]:
            valid = current_field["_valueConstraints"]["defaultValue"] == general["_valueConstraints"]["defaultValue"]
        if not valid:
            self.utils.log_message(
                Severities.ERROR,
                field_id,
                f"Field 'default value' not the same as general: {current_field['_valueConstraints']['defaultValue']} != {general['_valueConstraints']['defaultValue']}",
            )

        return valid

    def check_field_branches_valid(self, field_id, current_field, general):
        valid = True
        if "_valueConstraints" in general and "branches" in general["_valueConstraints"]:
            valid = current_field["_valueConstraints"]["branches"] == general["_valueConstraints"]["branches"]
        if not valid:
            if (
                current_field["_valueConstraints"]["branches"][0]["uri"]
                == general["_valueConstraints"]["branches"][0]["uri"]
            ):
                valid = True
                self.utils.log_message(
                    Severities.WARNING,
                    field_id,
                    f"Field ontology branches not exactly the same as general, but URI does match: {current_field['_valueConstraints']['branches']} != {general['_valueConstraints']['branches']}",
                )
            else:
                self.utils.log_message(
                    Severities.ERROR,
                    field_id,
                    f"Field ontology branches not the same as general: {current_field['_valueConstraints']['branches']} != {general['_valueConstraints']['branches']}",
                )
        return valid

    # endregion


def main():
    parser = argparse.ArgumentParser(description="validate schema description")
    parser.add_argument("file", type=argparse.FileType("r"), help="Path to the schema to validate")
    args = parser.parse_args()

    if not args.file.name.endswith(".json"):
        exit(f"Invalid file path provided. Should be a '.json' file")

    validator = SchemaValidator(args)
    validator.validate()
    if not validator.utils.ERROR_COUNT:
        if validator.utils.WARNING_COUNT:
            print("Validation result: OK with warnings. No errors found.")
            print(f"\t {validator.utils.WARNING_COUNT} warning(s) encountered")
        else:
            print("Validation result: OK. No errors found.")
            print(f"\t {validator.utils.WARNING_COUNT} warning(s) encountered")
    else:
        print("Validation result: NOT OK - errors found")
        print(f"\t {validator.utils.ERROR_COUNT} error(s) encountered")
        print(f"\t {validator.utils.WARNING_COUNT} warning(s) encountered")


if __name__ == "__main__":
    main()
