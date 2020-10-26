from epjsoneditor.schemainputfield import SchemaInputField


class SchemaInputObject:
    def __init__(self, object_name, json_properties):
        self.json_properties = json_properties

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

        fields_in_order = json_properties["legacy_idd"]["fields"]
        self.input_fields = {}  # note Python 3.7 and later preserve insertion order for dictionaries.
        for field in fields_in_order:
            self.input_fields[field] = SchemaInputField(field, json_properties)
