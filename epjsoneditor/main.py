import json
from epjsoneditor.schemainputobject import SchemaInputObject

data_dictionary = {}


def create_data_dictionary():
    """
     Create the simplified version of the Energy+.schema.epJSON that
     is closer to what is needed for displaying the grid elements
    """
    with open("c:/EnergyPlusV9-4-0/Energy+.schema.epJSON") as schema_file:
        epschema = json.load(schema_file)
        for object_name, json_properties in epschema["properties"].items():
            data_dictionary[object_name] = SchemaInputObject(json_properties)


create_data_dictionary()
print()
