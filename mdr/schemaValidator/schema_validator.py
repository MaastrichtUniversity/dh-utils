from cedarparsingutils.utils import CedarSchemaName
from utils import Severities, GENERAL_SCHEMA_FIELDS_TO_CHECK


class SchemaValidator:
    NODE_IDS = []
    PAGE_BREAK = False

    def __init__(self, cedar_utils):
        self.utils = cedar_utils

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
            if not valid:
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
                    "Field ontology branches not exactly the same as general, but URI does match",
                )
            else:
                self.utils.log_message(
                    Severities.ERROR,
                    field_id,
                    f"Field ontology branches not the same as general: {current_field['_valueConstraints']['branches']} != {general['_valueConstraints']['branches']}",
                )
        return valid

    def check_duplicate_node_id(self, node_id):
        if node_id in self.NODE_IDS:
            self.utils.log_message(Severities.ERROR, node_id, "Duplicate node ID")
        self.NODE_IDS.append(node_id)

    # endregion
