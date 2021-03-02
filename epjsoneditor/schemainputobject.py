
class SchemaInputObject:
    def __init__(self, json_properties):
        # self.json_properties = json_properties # for debugging only

        if "memo" in json_properties:
            self.memo = json_properties["memo"]

        if "group" in json_properties:
            self.group = json_properties["group"]

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
            self.extensible_size = json_properties["extensible_size"]

        fields_in_order = []
        extensible_fields = []
        if "legacy_idd" in json_properties:
            if "fields" in json_properties["legacy_idd"]:
                fields_in_order = json_properties["legacy_idd"]["fields"]
            if "extension" in json_properties["legacy_idd"]:
                extensible_fields.append(json_properties["legacy_idd"]["extension"])
                self.extension = json_properties["legacy_idd"]["extension"]
        self.input_fields = {}  # note Python 3.7 and later preserve insertion order for dictionaries.
        for field in fields_in_order:
            self.input_fields[field] = self.get_input_field(field, json_properties, False)
        for field in extensible_fields:
            self.input_fields[field] = self.get_input_field(field, json_properties, True)

    def get_input_field(self, field, json_properties, is_extension):
        """
        Based on the the field and the portion of the Energy+.schema.epJSON file
        returns the details for that field.
        """
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
                extension_dict[extensible_field]["field_name_with_spaces"] = \
                    self.add_field_name_with_spaces(json_properties, extensible_field)
                extension_dict[extensible_field]["is_required"] = \
                    self.is_field_required(return_dict["items"], extensible_field)
                self.fix_any_of(extension_dict[extensible_field])
            return extension_dict
        return_dict["field_name_with_spaces"] = self.add_field_name_with_spaces(json_properties, field)
        self.fix_any_of(return_dict)
        return return_dict

    @staticmethod
    def fix_any_of(dictionary):
        if 'field' in dictionary:
            print(f'field found in dictionary: {dictionary}')
        if 'anyOf' in dictionary:
            # print(f'anyOf found in: {field} of class {return_dict["field_name_with_spaces"]}
            # in the form {return_dict["anyOf"]}')
            if len(dictionary['anyOf']) == 2:
                first_dict, second_dict = dictionary['anyOf']
                combined_enum = []
                if 'enum' in first_dict:
                    combined_enum = first_dict['enum']
                if 'enum' in second_dict:
                    combined_enum.extend(second_dict['enum'])
                dictionary.update(first_dict)
                dictionary.update(second_dict)
                if combined_enum:
                    dictionary['enum'] = combined_enum
                dictionary['type'] = 'number_or_string'
                del dictionary['anyOf']
            else:
                print(f'while parsing schema an anyOf not of length 2 was found {dictionary["field_name_with_spaces"]}')

    @staticmethod
    def get_from_under_pattern_properties(sub_key, field):
        """
        Returns a portion of the json-schema in the Energy+.schema.epJSON that corresponds to just the current field.
        """
        return_dict = {}
        if "properties" in sub_key:
            if field in sub_key["properties"]:
                return_dict = sub_key["properties"][field]
        return return_dict

    @staticmethod
    def add_field_name_with_spaces(sub_key, field):
        """
        Returns the full field name with capital letters and spaces from the JSON schema
        """
        if "legacy_idd" in sub_key:
            if "field_info" in sub_key["legacy_idd"]:
                field_info = sub_key["legacy_idd"]["field_info"]
                if field in field_info:
                    if "field_name" in field_info[field]:
                        return field_info[field]["field_name"]
        return ""

    @staticmethod
    def trim_extension_field_hierarchy(working_dictionary):
        """
        Returns a subset of the Energy+.schema.epJSON schema file that is under /items/properties
        """
        if "items" in working_dictionary:
            if "properties" in working_dictionary["items"]:
                return working_dictionary["items"]["properties"]
        return working_dictionary

    @staticmethod
    def is_field_required(working_dictionary, field):
        """
        Determines if a field is required or not.
        """
        if "required" in working_dictionary:
            is_required = field in working_dictionary["required"]
        else:
            is_required = False
        return is_required
