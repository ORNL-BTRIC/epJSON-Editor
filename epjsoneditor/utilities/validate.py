import time
import jsonschema

# import sys
# import json
# import fastjsonschema


class ValidateEpJson:
    def __init__(self, schema_to_compile):
        #  self.validator = self.open_and_compile_validator(path_to_schema)
        #  self.validator = self.compile_validator(schema_to_compile)
        self.validator = jsonschema.Draft4Validator(schema_to_compile)
        self.named_schema = schema_to_compile

    # def open_and_compile_validator(self, path_to_schema):
    #     with open(path_to_schema) as schema_file:
    #         json_schema = json.load(schema_file)
    #     schema_validator = fastjsonschema.compile(json_schema)
    #     return schema_validator
    #
    # def compile_validator(self, schema_to_compile):
    #     try:
    #         schema_validator = fastjsonschema.compile(schema_to_compile)
    #     except fastjsonschema.JsonSchemaDefinitionException as e:
    #         print(e.message)
    #     return schema_validator
    #
    # def check_json_against_schema(self, json_dict):
    #     try:
    #         self.validator(json_dict)
    #     except fastjsonschema.JsonSchemaException as e:
    #         print(e.message)
    #         print(f"invalid value {e.value}")
    #         print(f"rule is broken {e.rule} and definition is {e.rule_definition}")
    #         print()

    def check_if_valid(self, json_instance):
        # try:
        #     jsonschema.validate(json_instance, self.named_schema)
        # except jsonschema.SchemaError as e:
        #     print(f"Schema error {e}")
        # except jsonschema.ValidationError as e:
        #     print("validation error")
        #     print(e.message)
        #     print(e.path)
        # except AttributeError as e:
        #     print(f"Attribute error {e.message}")
        # except:
        #     print("none of the above")
        #     e = sys.exc_info()[0]
        #     print(f"Error: {e}")
        start = time.time()
        # v = jsonschema.Draft4Validator(self.named_schema)
        # errors = sorted(v.iter_errors(json_instance), key=lambda e: e.path)
        errors = sorted(self.validator.iter_errors(json_instance), key=lambda e: e.path)
        messages = []
        for error in errors:
            print(f"{error.message} in path {error.path}")
            messages.append((error.message,error.path))
        end = time.time()
        print(f"time for check_if_valid is {end - start}")
        return messages