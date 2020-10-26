import json
from epjsoneditor.schemainputobject import SchemaInputObject

data_dictionary = {}
with open("c:\EnergyPlusV9-4-0\Energy+.schema.epJSON") as schema_file:
    epschema = json.load(schema_file)
    for object_name, json_properties in epschema["properties"].items():
        print(object_name)
        data_dictionary[object_name] = SchemaInputObject(object_name, json_properties)
    print('x')




    #version_obj = epschema["properties"]["Version"]
    # print(json.dumps(value, indent=2))
    #    if key == "SimulationControl":
    #        # print(json.dumps(value, indent=2))
    #        legacy_portion = value["legacy_idd"]
    #        # print(json.dumps(legacy_portion, indent=2))
    #        fields_in_order = legacy_portion["fields"]
    #        print(fields_in_order)
    #        properties = value["patternProperties"][".*"]["properties"]
    #        # print(json.dumps(properties, indent=2))
    #        for field in fields_in_order:
    #            print(f"---- {field} -----------")
    #            print(json.dumps(properties[field], indent=2))
