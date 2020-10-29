

class SchemaInputFieldDict:

    def __init__(self, field, json_properties, counter):
        pattern_properties = json_properties["patternProperties"]

        if field == "name" and "name" in json_properties:
            self.dict = json_properties["name"]
        elif ".*" in pattern_properties:
            self.dict = self.get_from_under_pattern_properties(pattern_properties[".*"], field)
        elif "^.*\\S.*$" in pattern_properties:
            self.dict = self.get_from_under_pattern_properties(pattern_properties["^.*\\S.*$"], field)
        self.add_field_name_with_spaces(json_properties, field)


    def get_from_under_pattern_properties(self, subkey, field):
        return_dict = {}
        if "properties" in subkey:
            if field in subkey["properties"]:
                 return_dict = subkey["properties"][field]
        return return_dict

    def add_field_name_with_spaces(self, subkey, field):
        if "legacy_idd" in subkey:
            if "field_info" in subkey["legacy_idd"]:
                field_info = subkey["legacy_idd"]["field_info"]
                if field in field_info:
                    if "field_name" in field_info[field]:
                        self.dict["field_name_with_spaces"] = field_info[field]["field_name"]

