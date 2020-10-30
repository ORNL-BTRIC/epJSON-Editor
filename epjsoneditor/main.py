import json
from epjsoneditor.schemainputobject import SchemaInputObject

data_dictionary = {}
with open("c:\EnergyPlusV9-4-0\Energy+.schema.epJSON") as schema_file:
    epschema = json.load(schema_file)
    for object_name, json_properties in epschema["properties"].items():
        data_dictionary[object_name] = SchemaInputObject(object_name, json_properties)
    print('x')
