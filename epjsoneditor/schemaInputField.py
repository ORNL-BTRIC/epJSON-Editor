from enum import Enum


class SchemaInputField:

    def __init__(self, field, json_properties):
        pattern_properties = json_properties["patternProperties"]
        under_pattern = {}
        if ".*" in pattern_properties:
            under_pattern = pattern_properties[".*"]["properties"]
        elif "^.*\\S.*$" in pattern_properties:
            under_pattern = pattern_properties["^.*\\S.*$"]["properties"]

        self.note = ""
        if field in under_pattern:
            cur_field = under_pattern[field]
            if "note" in cur_field:
                self.note = cur_field["note"]
            if "default" in cur_field:
                self.default = cur_field["default"]
                self.default_exists = True
            else:
                self.default_exists = False

            self.field_type = FieldType.UNKNOWN
            if "type" in cur_field:
                if cur_field["type"] == "number":
                    self.field_type = FieldType.NUMBER
                    if "minimum" in cur_field:
                        self.minimum = cur_field["minimum"]
                        self.is_exclusive_minimum = False
                        if "exclusiveMinimum" in cur_field:
                            if cur_field["exclusiveMinimum"] == "true":
                                self.is_exclusive_minimum = True
                    if "maximum" in cur_field:
                        self.maximum = cur_field["maximum"]
                        self.is_exclusive_maximum = False
                        if "exclusiveMaximum" in cur_field:
                            if cur_field["exclusiveMaximum"] == "true":
                                self.is_exclusive_maximum = True
                    if "units" in cur_field:
                        self.si_units = cur_field["units"]
                    if "ip-units" in cur_field:
                        self.ip_units = cur_field["ip-units"]
                    if "unitsBasedOnField" in cur_field:
                        self.units_based_on_field = cur_field["unitsBasedOnField"]
                elif cur_field["type"] == "string":
                    if "enum" in cur_field:
                        self.field_type = FieldType.CHOICE
                        self.choices = cur_field["enum"]
                    elif "data_type" in cur_field:
                        if cur_field["data_type"] == "object_list":
                            if "object_list" in cur_field:
                                self.field_type = FieldType.OBJECT_LIST
                                self.object_list = cur_field["object_list"]
                        elif cur_field["data_type"] == "external_list":
                            if "external_list" in cur_field:
                                self.field_type = FieldType.EXTERNAL_LIST
                                self.external_list = cur_field["external_list"]
                    elif "node_name" in field:  # this is a hack solution since \type node was not supported in the Energy+.schema.epJSON file
                        self.field_type = FieldType.NODE
                    else:
                        self.field_type = FieldType.STRING



class FieldType(Enum):
    NUMBER = 1
    STRING = 2
    CHOICE = 3
    OBJECT_LIST = 4
    EXTERNAL_LIST = 5
    NODE = 6
    UNKNOWN = 7
