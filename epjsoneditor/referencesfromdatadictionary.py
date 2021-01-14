class ReferencesFromDataDictionary:
    def __init__(self, data_dictionary):
        self.reference_fields = {}
        self.gather_references_from_schema(data_dictionary)

    def gather_references_from_schema(self, data_dictionary):
        for class_name, schema_object in data_dictionary.items():
            for field_name, field_details in schema_object.input_fields.items():
                if 'reference' in field_details:
                    for current_named_reference in field_details['reference']:
                        if current_named_reference in self.reference_fields:
                            self.reference_fields[current_named_reference].append((class_name, field_name))
                        else:
                            self.reference_fields[current_named_reference] = [(class_name, field_name)]
