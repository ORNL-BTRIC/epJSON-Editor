
class SchemaInputObject:
    def __init__(self, object_name, json_properties):
        # self.json_properties = json_properties # for debugging only

        if "memo" in json_properties:
            self.memo = json_properties["memo"]

        self.is_required = False
        if "minProperties" in json_properties:
            if json_properties["minProperties"] == 1:
                self.is_required = True

        self.is_unique = False
        if "maxProperties" in json_properties:
            if json_properties["maxProperties"] == 1:
                self.is_unique = True

        self.min_fields = 0
        if "min_fields" in json_properties:
            self.min_fields = json_properties["min_fields"]

        self.extensible_size = 0
        if "extensible_size" in json_properties:
            self.min_fields = json_properties["extensible_size"]

        fields_in_order = []
        extensible_fields = []
        if "legacy_idd" in json_properties:
            if "fields" in json_properties["legacy_idd"]:
                fields_in_order = json_properties["legacy_idd"]["fields"]
            if "extension" in json_properties["legacy_idd"]:
                extensible_fields.append(json_properties["legacy_idd"]["extension"])
        self.input_fields = {}  # note Python 3.7 and later preserve insertion order for dictionaries.
        for field in fields_in_order:
            self.input_fields[field] = self.get_input_field(field, json_properties, False)
        for field in extensible_fields:
            self.input_fields[field] = self.get_input_field(field, json_properties, True)

    def get_input_field(self, field, json_properties, is_extension):
        pattern_properties = json_properties["patternProperties"]
        return_dict = {}
        if field == "name" and "name" in json_properties:
            return_dict = json_properties["name"]
        elif ".*" in pattern_properties:
            return_dict = self.get_from_under_pattern_properties(pattern_properties[".*"], field)
            return_dict["is_required"] = self.is_field_required(pattern_properties[".*"], field)
        elif "^.*\\S.*$" in pattern_properties:
            return_dict = self.get_from_under_pattern_properties(pattern_properties["^.*\\S.*$"], field)
            return_dict["is_required"] = self.is_field_required(pattern_properties["^.*\\S.*$"], field)
        if is_extension:
            extension_dict = self.trim_extension_field_hierarchy(return_dict)
            for extensible_field in extension_dict.keys():
                extension_dict[extensible_field]["field_name_with_spaces"] = self.add_field_name_with_spaces(return_dict, json_properties, extensible_field)
                extension_dict[extensible_field]["is_required"] = self.is_field_required(return_dict, extensible_field)
            return extension_dict
        return_dict["field_name_with_spaces"] = self.add_field_name_with_spaces(return_dict, json_properties, field)
        return return_dict

    def get_from_under_pattern_properties(self, sub_key, field):
        return_dict = {}
        if "properties" in sub_key:
            if field in sub_key["properties"]:
                 return_dict = sub_key["properties"][field]
        return return_dict

    def add_field_name_with_spaces(self, cur_dictionary, sub_key, field):
        if "legacy_idd" in sub_key:
            if "field_info" in sub_key["legacy_idd"]:
                field_info = sub_key["legacy_idd"]["field_info"]
                if field in field_info:
                    if "field_name" in field_info[field]:
                        return field_info[field]["field_name"]
        return ""

    def trim_extension_field_hierarchy(self,working_dictionary):
        if "items" in working_dictionary:
            if "properties" in working_dictionary["items"]:
                return working_dictionary["items"]["properties"]
        return working_dictionary

    def is_field_required(self, working_dictionary, field):
        if "required" in working_dictionary:
            is_required = field in working_dictionary["required"]
        else:
            is_required = False
        return is_required


