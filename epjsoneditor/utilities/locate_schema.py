import os
import string
import glob

from epjsoneditor.utilities.crossplatform import Platform


class LocateSchema:

    def __init__(self):
        self.schema_path = None

    def get_schema_path(self):
        file_sought = 'Energy+.schema.epJSON'
        found_path = self.search_up_tree(file_sought)
        if found_path:
            self.schema_path = found_path
            return found_path
        found_path = self.search_common_places(file_sought)
        if found_path:
            self.schema_path = found_path
            return found_path
        # nothing found
        self.schema_path = ""
        return ""

    def search_up_tree(self,file_sought):
        # first search from the current working directory and up directory tree
        possible_dir = os.getcwd()
        possible_path = os.path.join(possible_dir, file_sought)
        while not os.path.exists(possible_path):
            previous_dir = possible_dir
            # print(f"possible path : {possible_path}")
            possible_dir, _ = os.path.split(possible_dir)
            possible_path = os.path.join(possible_dir, file_sought)
            if possible_dir == previous_dir:
                possible_dir = ''
                break
        if possible_dir:
            self.schema_path = possible_path
            return possible_path

    def search_common_places(self, file_sought):
        # that did not work so look for latest version
        search_roots = {
            Platform.WINDOWS: ["%s:\\" % c for c in string.ascii_uppercase],
            Platform.LINUX: ['/usr/local/bin/', '/tmp/'],
            Platform.MAC: ['/Applications/', '/tmp/'],
            Platform.UNKNOWN: [],
        }
        current_search_roots = search_roots[Platform.get_current_platform()]
        search_names = ["EnergyPlus*", "energyplus*", "EP*", "ep*", "E+*", "e+*"]
        for search_root in current_search_roots:
            for search_name in search_names:
                full_search_path = os.path.join(search_root, search_name)
                full_search_path_with_schema = os.path.join(full_search_path, file_sought)
                possible_directories = glob.glob(full_search_path_with_schema)
                possible_directories.sort(reverse=True)
                # print(f"possible_directories : {possible_directories}")
                if possible_directories:
                    if possible_directories[0]:
                        self.schema_path = possible_directories[0]
                        return possible_directories[0]

# OLD CODE WITH HARD PATHS
#        current_platform = Platform.get_current_platform()
#        if current_platform == Platform.WINDOWS:
#            path_to_schema = "C:/Users/jglaz/Documents/projects/epJSON Editor/schema/2021-02-10 schema/Energy+.schema.epJSON"
#        elif current_platform == Platform.LINUX:
#            path_to_schema = "/eplus/repos/1eplus/builds/r/Products/Energy+.schema.epJSON"
#        elif current_platform == Platform.MAC:
#            path_to_schema = "/eplus/repos/1eplus/builds/r/Products/Energy+.schema.epJSON"
#        else:
#            path_to_schema = "/eplus/repos/1eplus/builds/r/Products/Energy+.schema.epJSON"
