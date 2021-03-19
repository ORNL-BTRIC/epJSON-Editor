import time
import jsonschema


class ValidateEpJson:
    def __init__(self, schema_to_compile):
        self.validator = jsonschema.Draft4Validator(schema_to_compile)
        self.named_schema = schema_to_compile

    def check_if_valid(self, json_instance):
        start = time.time()
        errors = sorted(self.validator.iter_errors(json_instance), key=lambda e: e.path)
        messages = []
        for error in errors:
            # print(f"{error.message} in path {error.path}")
            messages.append((error.message,error.path))
        end = time.time()
        print(f"time for check_if_valid is {end - start}")
        return messages