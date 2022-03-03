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
        self.check_duplicate_node_id(node_id)
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
            schema_value_constraints = node["_valueConstraints"]
            unsupported_value_constraints = [
                "numberType",
                "minValue",
                "maxValue",
                "decimalPlace",
                "unitOfMeasure",
                "minLength",
                "maxLength",
                "temporalType",
            ]
            for unsupported_value_constraint in unsupported_value_constraints:
                if unsupported_value_constraint in schema_value_constraints:
                    self.utils.log_message(
                        Severities.WARNING,
                        node_id,
                        f"The valueConstraint {unsupported_value_constraint} is not supported or rendered in MDR",
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

    def validate_textarea(self, node: dict, node_id: str):
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

    def check_duplicate_node_id(self, node_id: str):
        if node_id in self.NODE_IDS:
            self.utils.log_message(Severities.ERROR, node_id, "Duplicate node ID")
        self.NODE_IDS.append(node_id)

    # endregion
    # region Formset validators

    def check_nested_formset(self, node: dict, node_id: str):
        """
        Check if the formset passed is nested, because that is not allowed

        Parameters
        ----------
        is_array: bool
            If the caller is coming from an array node
        node: dict
            The node to validate
        node_id: str
            The ID of the node for reference
        """
        if "items" in node:
            if "order" in node["items"]["_ui"]:
                self.utils.log_message(Severities.ERROR, node_id, "Nested formsets are not allowed")
        else:
            if "order" in node["_ui"]:
                self.utils.log_message(
                    Severities.WARNING, node_id, "A formset within a nested object will not be rendered properly in MDR"
                )

    # endregion
    # region General schema validation

    def validate_general_fields(self, schema: dict):
        for node_id, general_node in GENERAL_SCHEMA_FIELDS_TO_CHECK.items():
            if node_id in schema["properties"]:
                current_node = schema["properties"][node_id]
                try:
                    self.check_node_is_valid(node_id, current_node, general_node)
                except KeyError as e:
                    self.utils.log_message(
                        Severities.ERROR, node_id, f"Required element from DataHub General not identical {e}"
                    )
            else:
                self.utils.log_message(Severities.ERROR, node_id, "Required element from DataHub General not found")

    def check_node_is_valid(self, node_id: str, current_node: dict, general_node: dict):
        self.check_node_type_valid(node_id, current_node, general_node)
        for field, value in general_node["fields"].items():
            element_to_check = (
                current_node["items"]["properties"][field]
                if current_node["type"] == "array"
                else current_node["properties"][field]
            )
            self.check_field_type_valid(field, element_to_check, value)
            self.check_field_input_type_valid(field, element_to_check, value)
            self.check_field_hidden_valid(field, element_to_check, value)
            self.check_field_required_valid(field, element_to_check, value)
            self.check_field_default_value_valid(field, element_to_check, value)
            self.check_field_ontology_valid(field, element_to_check, value, "branches")
            self.check_field_ontology_valid(field, element_to_check, value, "ontologies")
            self.check_field_ontology_valid(field, element_to_check, value, "classes")

    def check_node_type_valid(self, node_id: str, current_node: dict, general_node: dict):
        if current_node["type"] != general_node["type"]:
            self.utils.log_message(
                Severities.ERROR,
                node_id,
                f"Required element from DataHub General not the same type: Current: {current_node['type']} != General: {general_node['type']}",
            )

    def check_field_type_valid(self, field_id: str, current_field: dict, general: dict):
        if current_field["type"] != general["type"]:
            self.utils.log_message(
                Severities.ERROR,
                field_id,
                f"Field type not the same as general field type: '{current_field['type']}' != '{general['type']}'",
            )

    def check_field_input_type_valid(self, field_id: str, current_field: dict, general: dict):
        valid = True
        if "_ui" in general and "inputType" in general["_ui"]:
            valid = current_field["_ui"]["inputType"] == general["_ui"]["inputType"]
        if not valid:
            self.utils.log_message(
                Severities.ERROR,
                field_id,
                f"Field input type not the same as general field type: {current_field['_ui']['inputType']} != {general['_ui']['inputType']}",
            )

    def check_field_hidden_valid(self, field_id: str, current_field: dict, general: dict):
        general_hidden = "_ui" in general and "hidden" in general["_ui"] and general["_ui"]["hidden"]
        current_hidden = "_ui" in current_field and "hidden" in current_field["_ui"] and current_field["_ui"]["hidden"]
        valid = current_hidden == general_hidden
        if not valid:
            self.utils.log_message(
                Severities.ERROR,
                field_id,
                f"Field 'hidden' not the same. Current: '{current_hidden}' != General: '{general_hidden}'",
            )

    def check_field_required_valid(self, field_id: str, current_field: dict, general: dict):
        general_required = (
            "_valueConstraints" in general
            and "requiredValue" in general["_valueConstraints"]
            and general["_valueConstraints"]["requiredValue"]
        )
        current_required = (
            "_valueConstraints" in current_field
            and "requiredValue" in current_field["_valueConstraints"]
            and current_field["_valueConstraints"]["requiredValue"]
        )
        valid = current_required == general_required
        if not valid:
            self.utils.log_message(
                Severities.ERROR,
                field_id,
                f"Field 'required' not the same as general: Current: '{current_required}' != General: '{general_required}'",
            )

    def check_field_default_value_valid(self, field_id: str, current_field: dict, general: dict):
        valid = True
        if "_valueConstraints" in general and "defaultValue" in general["_valueConstraints"]:
            valid = current_field["_valueConstraints"]["defaultValue"] == general["_valueConstraints"]["defaultValue"]
        if not valid:
            self.utils.log_message(
                Severities.ERROR,
                field_id,
                f"Field 'default value' not the same as general: {current_field['_valueConstraints']['defaultValue']} != {general['_valueConstraints']['defaultValue']}",
            )

    def check_field_ontology_valid(self, field_id: str, current_field: dict, general: dict, key: str):
        valid = True
        if "_valueConstraints" in general and key in general["_valueConstraints"]:
            valid = current_field["_valueConstraints"][key] == general["_valueConstraints"][key]
        if not valid:
            if current_field["_valueConstraints"][key][0]["uri"] == general["_valueConstraints"][key][0]["uri"]:
                self.utils.log_message(
                    Severities.WARNING,
                    field_id,
                    f"Field ontology '{key}' not exactly the same as general, but URI does match",
                )
            else:
                self.utils.log_message(
                    Severities.ERROR,
                    field_id,
                    f"Field ontology '{key}' not the same as general: {current_field['_valueConstraints'][key]} != {general['_valueConstraints'][key]}",
                )

    # endregion
