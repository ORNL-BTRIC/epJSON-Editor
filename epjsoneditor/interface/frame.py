import wx
import wx.grid
import wx.lib.agw.aui as aui
import os
import json
import time
import sys

from epjsoneditor.schemainputobject import SchemaInputObject
from epjsoneditor.referencesfromdatadictionary import ReferencesFromDataDictionary
from epjsoneditor.interface.settings_dialog import SettingsDialog
from epjsoneditor.utilities.locate_schema import LocateSchema
from epjsoneditor.utilities.validate import ValidateEpJson
from epjsoneditor.interface.editor_grid import EditorGrid

if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app
    # path into variable _MEIPASS'.
    application_path = sys._MEIPASS
else:
    application_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class EpJsonEditorFrame(wx.Frame):

    def __init__(self, parent, id=-1, title="epJSON Editor - ", pos=wx.DefaultPosition,
                 size=(1500, 1000), style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        self._mgr = aui.AuiManager()

        self.data_dictionary = {}
        self.cross_references = {}
        self.reference_names = {}
        self.validator = None
        self.create_data_dictionary()
        self.explanation_text = None
        self.object_list_tree = None
        self.object_list_root = None
        self.name_to_object_list_item = {}
        self.main_grid = None
        self.selected_object_tree_item = None
        self.selected_object_name = None
        self.current_file_path = None
        self.use_si_units = True
        self.row_fields = None
        self.column_input_object_names = None
        self.name_to_column_number = {}
        self.field_to_row_number = {}
        self.field_name_to_display_name = {}
        self.jump_destination_list = None
        self.additional_sets_of_fields = 3  # extra sets of fields for grid to display for extensible objects
        self.object_list_show_groups = True
        self.jumps = {}
        self.unit_conversions = {}
        self.read_unit_conversions()
        self.current_file = {}
        self.changes_not_saved = False
        # search related
        self.search_field = None
        self.search_jump_notebook = None
        self.search_panel = None
        self.search_results = {}
        self.create_gui()

    def create_gui(self):

        # notify AUI which frame to use
        self._mgr.SetManagedWindow(self)
        self.create_list_of_objects()
        self.explanation_text = wx.TextCtrl(self, -1, "Explanation of the selected input object and field",
                                            wx.DefaultPosition, wx.Size(200, 150),
                                            wx.NO_BORDER | wx.TE_MULTILINE)

        text4 = wx.TextCtrl(self, -1, "Main content window",
                            wx.DefaultPosition, wx.Size(600, 650),
                            wx.NO_BORDER | wx.TE_MULTILINE)

        # add the panes to the manager
        self._mgr.AddPane(text4, aui.AuiPaneInfo().CenterPane().Name("text_content"))
        self._mgr.AddPane(self.explanation_text, aui.AuiPaneInfo().Top().Caption("Explanation"))

        self.main_grid = self.create_grid()
        self.Bind(wx.grid.EVT_GRID_CELL_LEFT_CLICK, self.handle_cell_left_click)
        self.Bind(wx.grid.EVT_GRID_SELECT_CELL, self.handle_cell_select_cell)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.handle_cell_changed)

        # clicking on grid columns was crashing so adding these to catch them
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_CLICK, self.handle_grid_label_click)
        self.Bind(wx.grid.EVT_GRID_LABEL_LEFT_DCLICK, self.handle_grid_label_click)
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_CLICK, self.handle_grid_label_click)
        self.Bind(wx.grid.EVT_GRID_LABEL_RIGHT_DCLICK, self.handle_grid_label_click)

        self._mgr.AddPane(self.main_grid, aui.AuiPaneInfo().Name("grid_content").
                          CenterPane().Hide().MinimizeButton(True))

        self.search_panel = self.create_jump_search_pane()
        self._mgr.AddPane(self.search_panel, aui.AuiPaneInfo().Bottom().Name("bottom_search").Caption("Jump and Search")
                          .MinSize(150, 150))

        # Layer(2) allows it to take all of left side
        self._mgr.AddPane(self.object_list_tree, aui.AuiPaneInfo().Left().Layer(2).Caption("List of Input Objects")
                          .MinSize(400, 400))

        # tell the manager to "commit" all the changes just made
        self._mgr.Update()

        # it works better to have TextCtrl for CenterPane shown and hidden and the grid being hidden then shown
        self._mgr.GetPane("grid_content").Show(True)
        self._mgr.GetPane("text_content").Show(False)
        self._mgr.Update()

        self.create_toolbar()

        self.Bind(wx.EVT_CLOSE, self.handle_close)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.handle_select_object_list_item, self.object_list_tree)

        # select first object in list
        all_object_names = list(self.name_to_object_list_item.keys())
        self.object_list_tree.SelectItem(self.name_to_object_list_item[all_object_names[0]])

    def create_list_of_objects(self):
        self.object_list_tree = wx.TreeCtrl(self, style=wx.TR_HIDE_ROOT)
        self.object_list_root = self.object_list_tree.AddRoot("All Input Objects")
        self.object_list_tree.SetItemData(self.object_list_root, None)
        self.object_list_show_groups = hasattr(self.data_dictionary['Version'], 'group')
        if self.object_list_show_groups:
            current_group_name = ''
            group_root = None
            for name_of_class in self.data_dictionary.keys():
                if self.data_dictionary[name_of_class].group != current_group_name:
                    current_group_name = self.data_dictionary[name_of_class].group
                    group_root = self.object_list_tree.AppendItem(self.object_list_root, current_group_name)
                child = self.object_list_tree.AppendItem(group_root, self.object_list_format(name_of_class, 0))
                self.object_list_tree.Expand(child)
                self.name_to_object_list_item[name_of_class] = child
                self.object_list_tree.Expand(group_root)
        else:
            for name_of_class in self.data_dictionary.keys():
                child = self.object_list_tree.AppendItem(self.object_list_root, self.object_list_format(name_of_class,
                                                                                                        0))
                self.object_list_tree.Expand(child)
                self.name_to_object_list_item[name_of_class] = child

    def create_grid(self):
        #        grid = wx.grid.Grid(self, -1, wx.Point(0, 0), wx.Size(150, 250),
        #                            wx.NO_BORDER | wx.WANTS_CHARS)
        grid = EditorGrid(self)
        grid.CreateGrid(5, 5)
        return grid

    def create_toolbar(self):
        # create some toolbars
        tool_main = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize,
                                   agwStyle=aui.AUI_TB_TEXT)
        tool_main.SetToolBitmapSize(wx.Size(48, 48))
        # tool_main.AddSimpleTool(10, "New", wx.ArtProvider.GetBitmap(wx.ART_NEW))

        tb_open_file = tool_main.AddSimpleTool(11, "Open", wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN))
        self.Bind(wx.EVT_TOOL, self.handle_open_file, tb_open_file)

        tb_save_file = tool_main.AddSimpleTool(12, "Save", wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE))
        self.Bind(wx.EVT_TOOL, self.handle_save_file, tb_save_file)

        tb_save_as_file = tool_main.AddSimpleTool(13, "Save As", wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS))
        self.Bind(wx.EVT_TOOL, self.handle_save_as_file, tb_save_as_file)

        # tool_main.AddSeparator()
        # tool_main.AddSimpleTool(14, "Undo", wx.ArtProvider.GetBitmap(wx.ART_UNDO))
        # tool_main.AddSimpleTool(15, "Redo", wx.ArtProvider.GetBitmap(wx.ART_REDO))
        tool_main.AddSeparator()

        tb_new_object = tool_main.AddSimpleTool(16, "New Obj", wx.ArtProvider.GetBitmap(wx.ART_PLUS))
        self.Bind(wx.EVT_TOOL, self.handle_new_object, tb_new_object)

        tb_duplicate_object = tool_main.AddSimpleTool(17, "Dup Obj", wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD))
        self.Bind(wx.EVT_TOOL, self.handle_duplicate_object, tb_duplicate_object)

        # tb_dup_change_object=tool_main.AddSimpleTool(18, "Dup Obj + Chg", wx.ArtProvider.GetBitmap(wx.ART_GOTO_LAST))
        # self.Bind(wx.EVT_TOOL, self.handle_tb_dup_change_object, tb_dup_change_object)

        tb_delete_object = tool_main.AddSimpleTool(19, "Del Obj", wx.ArtProvider.GetBitmap(wx.ART_MINUS))
        self.Bind(wx.EVT_TOOL, self.handle_tb_delete_object, tb_delete_object)

        tb_copy_object = tool_main.AddSimpleTool(20, "Copy Obj", wx.ArtProvider.GetBitmap(wx.ART_COPY))
        self.Bind(wx.EVT_TOOL, self.handle_tb_copy_object, tb_copy_object)

        tb_paste_object = tool_main.AddSimpleTool(21, "Paste Obj", wx.ArtProvider.GetBitmap(wx.ART_PASTE))
        self.Bind(wx.EVT_TOOL, self.handle_tb_paste_object, tb_paste_object)

        # tool_main.AddSeparator()
        # tool_main.AddTool(22, "IP Units", wx.ArtProvider.GetBitmap(wx.ART_GO_UP), wx.NullBitmap, kind=wx.ITEM_RADIO)
        # tool_main.AddTool(23, "SI Units", wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN), wx.NullBitmap, kind=wx.ITEM_RADIO)

        tool_main.AddSeparator()
        tb_settings = tool_main.AddSimpleTool(25, "Settings", wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE))
        self.Bind(wx.EVT_TOOL, self.handle_settings_toolbar_button, tb_settings)
        tb_help = tool_main.AddSimpleTool(26, "Help", wx.ArtProvider.GetBitmap(wx.ART_HELP))
        tool_main.SetToolDropDown(26, True)
        self.Bind(wx.EVT_TOOL, self.handle_tb_help_menu, tb_help)
        tool_main.Realize()
        self._mgr.AddPane(tool_main, aui.AuiPaneInfo().Name("tool_main").Caption("Primary Toolbar").
                          ToolbarPane().Top())
        self._mgr.Update()

    def create_jump_search_pane(self):
        # set up the pane that contains the Jump and Search tabs and toolbar
        search_panel = wx.Panel(self)
        search_sizer = wx.BoxSizer(wx.VERTICAL)

        tools_search = aui.AuiToolBar(search_panel, -1, wx.DefaultPosition, wx.DefaultSize,
                                      agwStyle=aui.AUI_TB_PLAIN_BACKGROUND)
        tools_search.SetToolBitmapSize(wx.Size(24, 24))

        tools_search.AddLabel(-1, "Find:", 25)
        self.search_field = wx.ComboBox(tools_search, value='', size=(200, 20),
                                        style=wx.CB_DROPDOWN | wx.TE_PROCESS_ENTER)

        tools_search.AddControl(self.search_field)
        self.Bind(wx.EVT_COMBOBOX, self.handle_find_button, self.search_field)
        self.Bind(wx.EVT_TEXT_ENTER, self.handle_find_button, self.search_field)

        find_button = tools_search.AddSimpleTool(-2, "Find", wx.ArtProvider.GetBitmap(wx.ART_FIND))
        self.Bind(wx.EVT_TOOL, self.handle_find_button, find_button)
        tools_search.AddSpacer(20)
        # jump_button = wx.Button(tools_search, id=wx.ID_ANY, label="Jump", size=(60, 20))
        # jump_button.Bind(wx.EVT_BUTTON, self.handle_jump_button)
        # tools_search.AddControl(jump_button)
        # tools_search.AddSpacer(20)
        # tools_search.AddLabel(-1, "Replace:", 40)
        # replace_field = wx.ComboBox(tools_search, value='', choices=['zone', 'building', 'lighting'], size=(200, 20))
        # tools_search.AddControl(replace_field)
        # replace_single_button = wx.Button(tools_search, id=wx.ID_ANY, label="Single", size=(50, 20))
        # tools_search.AddControl(replace_single_button)
        # replace_all_button = wx.Button(tools_search, id=wx.ID_ANY, label="All", size=(50, 20))
        # tools_search.AddControl(replace_all_button)

        tools_search.Realize()
        search_sizer.Add(tools_search, 0, flag=wx.TOP)

        self.search_jump_notebook = aui.AuiNotebook(search_panel)

        self.jump_destination_list = wx.ListCtrl(search_panel, -1, style=wx.LC_REPORT)
        self.jump_destination_list.AppendColumn('Object', width=200)
        self.jump_destination_list.AppendColumn('Class', width=200)
        self.jump_destination_list.AppendColumn('Field', width=200)
        self.jump_destination_list.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.handle_jump_double_click)

        self.search_jump_notebook.AddPage(self.jump_destination_list, "Jump")

        search_sizer.Add(self.search_jump_notebook, 1, flag=wx.EXPAND)
        search_panel.SetSizer(search_sizer)
        return search_panel

    def handle_find_button(self, _):
        search_term = self.search_field.GetValue()
        if search_term:
            # check if the search term has already been used
            new_page_label = f"Search: {search_term}"
            page_index = self.find_page_in_search_jump_notebook(new_page_label)
            if page_index == -1:  # not found
                self.search_results[search_term] = wx.ListCtrl(self.search_panel, -1, style=wx.LC_REPORT)
                self.search_results[search_term].AppendColumn('Found Item', width=80)
                self.search_results[search_term].AppendColumn('Type', width=80)
                self.search_results[search_term].AppendColumn('Class', width=80)
                self.search_results[search_term].AppendColumn('Object', width=80)
                self.search_results[search_term].AppendColumn('Field', width=80)
                classes_found = self.find_class(search_term)
                for class_found in classes_found:
                    self.search_results[search_term].Append((class_found, "Class Names"))
                field_names_found = self.find_field_names(search_term)
                for (field_name_found, class_found) in field_names_found:
                    self.search_results[search_term].Append((field_name_found, "Field Names", class_found))
                field_values_found = self.find_field_values(search_term)
                for (field_value_found, class_found, object_found, field_name_found) in field_values_found:
                    self.search_results[search_term].Append((field_value_found, "Field Values", class_found,
                                                             object_found, field_name_found))
                for column_index in range(self.search_results[search_term].GetColumnCount()):
                    self.search_results[search_term].SetColumnWidth(column_index, wx.LIST_AUTOSIZE)
                self.search_results[search_term].Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.handle_search_double_click)
                self.search_jump_notebook.AddPage(self.search_results[search_term], new_page_label, select=True)
                self.search_field.Append(search_term)

    def find_class(self, find_text):
        names_of_classes = list(self.data_dictionary.keys())
        found_classes = [s for s in names_of_classes if find_text.upper() in s.upper()]
        return found_classes

    def find_field_names(self, find_text):
        found_field_names = []
        for class_name, schema_object in self.data_dictionary.items():
            for field_name, field_details in schema_object.input_fields.items():
                if 'field_name_with_spaces' in field_details:
                    search_in_field = field_details['field_name_with_spaces']
                else:
                    search_in_field = field_name
                if find_text.upper() in search_in_field.upper():
                    found_field_names.append((search_in_field, class_name))
        return found_field_names

    def find_field_values(self, find_text):
        found_field_values = []
        for class_name, object_dict in self.current_file.items():
            extension_field_group = ''
            if self.data_dictionary[class_name].extensible_size > 0:
                extension_field_group = self.data_dictionary[class_name].extension
            for object_name, field_dict in object_dict.items():
                for field_name, field_value in field_dict.items():
                    if field_name != extension_field_group:
                        if find_text.upper() in str(field_value).upper():
                            field_name_to_use = field_name
                            # find the normal field name with upper case and no underscores
                            schema_input_fields = self.data_dictionary[class_name].input_fields
                            if 'field_name_with_spaces' in schema_input_fields[field_name]:
                                field_name_to_use = schema_input_fields[field_name]['field_name_with_spaces']
                            found_field_values.append((field_value, class_name, object_name, field_name_to_use))
                    else:
                        for counter, extensible_dict in enumerate(field_value, start=1):
                            for extensible_field_name, extensible_field_value in extensible_dict.items():
                                if find_text.upper() in str(extensible_field_value).upper():
                                    field_name_to_use = extensible_field_name
                                    # find the normal field name with upper case and no underscores
                                    schema_input_fields = self.data_dictionary[class_name].input_fields[
                                        extension_field_group]
                                    if 'field_name_with_spaces' in schema_input_fields[extensible_field_name]:
                                        field_name_to_use = schema_input_fields[extensible_field_name][
                                            'field_name_with_spaces']
                                    display_name = field_name_to_use + "-" + str(counter).zfill(3)
                                    found_field_values.append((extensible_field_value, class_name, object_name,
                                                               display_name))

        return found_field_values

    def handle_open_file(self, _):
        if self.changes_not_saved:
            if wx.MessageBox("Do you want an opportunity to save the changes you made prior to clearing this file?",
                             "Please confirm", wx.ICON_QUESTION | wx.YES_NO) != wx.NO:
                return
        with wx.FileDialog(self, "Open EnergyPlus epJSON file", wildcard="epJSON files (*.epJSON)|*.epJSON",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind
            path_name = fileDialog.GetPath()
            try:
                self.load_current_file(path_name)
            except IOError:
                wx.LogError(f"Cannot open file {path_name}")

    def handle_settings_toolbar_button(self, _):
        settings_dialog = SettingsDialog(None, title='Settings')
        settings_dialog.set_settings(self.use_si_units)
        return_value = settings_dialog.ShowModal()
        if return_value == wx.ID_OK:
            self.use_si_units = settings_dialog.use_si_units
        print(self.use_si_units)
        settings_dialog.Destroy()
        self.update_grid(self.selected_object_name)

    def handle_jump_double_click(self, _):
        selected_destination = self.jump_destination_list.GetFirstSelected()
        if selected_destination != -1:
            print(selected_destination)
            name_of_object = self.jump_destination_list.GetItemText(selected_destination, 0)
            input_object_destination = self.jump_destination_list.GetItemText(selected_destination, 1)
            field_destination = self.jump_destination_list.GetItemText(selected_destination, 2)
            print(name_of_object, input_object_destination, field_destination)
            self.go_to_cell(input_object_destination, name_of_object, field_destination)

    def handle_search_double_click(self, _):
        index = self.search_jump_notebook.GetPageIndex(self.search_jump_notebook.GetCurrentPage())
        tab_name = self.search_jump_notebook.GetPageText(index)
        search_term = tab_name[8:]
        # print(f"notebook tab {search_term} - {index} - {tab_name}")
        selected_destination = self.search_results[search_term].GetFirstSelected()
        if selected_destination != -1:
            found_item = self.search_results[search_term].GetItemText(selected_destination, 0)
            type_of_find = self.search_results[search_term].GetItemText(selected_destination, 1)
            class_of_find = self.search_results[search_term].GetItemText(selected_destination, 2)
            object_name_of_find = self.search_results[search_term].GetItemText(selected_destination, 3)
            field_name_of_find = self.search_results[search_term].GetItemText(selected_destination, 4)
            print(found_item, type_of_find, class_of_find, object_name_of_find, field_name_of_find)
            if type_of_find == 'Class Names':
                object_list_item = self.name_to_object_list_item[found_item]
                self.object_list_tree.SelectItem(object_list_item)  # this triggers update_grid
            elif type_of_find == 'Field Names':
                self.go_to_cell(class_of_find, '', field_name_of_find)
            elif type_of_find == 'Field Values':
                self.go_to_cell(class_of_find, object_name_of_find, field_name_of_find)

    def go_to_cell(self, input_object, name_of_object, field_name):
        object_list_item = self.name_to_object_list_item[input_object]
        self.object_list_tree.SelectItem(object_list_item)  # this triggers update_grid
        column_number = -1
        if name_of_object:
            column_number = self.name_to_column_number[name_of_object]
        row_number = -1
        if field_name in self.field_to_row_number:
            row_number = self.field_to_row_number[field_name]
        if column_number >= 0 & row_number >= 0:
            self.main_grid.GoToCell(row_number, column_number)
            self.main_grid.SetFocus()
            self.enter_cell(row_number, column_number)

    def load_current_file(self, path_name):
        if os.path.exists(path_name):
            self.current_file_path = path_name
            with open(path_name) as input_file:
                self.current_file = json.load(input_file)
                self.gather_active_references()
                self.update_list_of_object_counts()
                self.update_dict_of_jumps()
                self.check_file_with_schema()
            self.changes_not_saved = False
            self.update_title()
            self.update_grid(self.selected_object_name)
            self.Refresh()

    def check_file_with_schema(self):
        validation_errors = self.validator.check_if_valid(self.current_file)
        page_label = "Validation"
        validation_page = self.find_page_in_search_jump_notebook("Validation")
        if validation_page > -1:
            self.search_results[page_label].DeleteAllItems()
        if validation_errors:
            validation_page = self.find_page_in_search_jump_notebook("Validation")
            if validation_page == -1:
                self.search_results[page_label] = wx.ListCtrl(self.search_panel, -1, style=wx.LC_REPORT)
                self.search_results[page_label].AppendColumn('Error', width=80)
                self.search_results[page_label].AppendColumn('Class', width=80)
                self.search_results[page_label].AppendColumn('Object', width=80)
                self.search_results[page_label].AppendColumn('Field', width=80)
            for (error_message, error_path) in validation_errors:
                if len(error_path) == 3:
                    class_name, object_name, field_name = error_path
                    self.search_results[page_label].Append((error_message, class_name, object_name, field_name))
                else:
                    self.search_results[page_label].Append((error_message, error_path))
            if validation_page == -1:
                self.search_jump_notebook.AddPage(self.search_results[page_label], page_label, select=True)

    def find_page_in_search_jump_notebook(self, page_name):
        for page_index in range(0, self.search_jump_notebook.GetPageCount()):
            page_label = self.search_jump_notebook.GetPageText(page_index)
            if page_name == page_label:
                self.search_jump_notebook.SetSelection(page_index)
                return page_index
        return -1

    def update_title(self):
        if os.path.exists(self.current_file_path):
            if self.changes_not_saved:
                self.SetTitle(f"epJSON Editor - {self.current_file_path} *")
            else:
                self.SetTitle(f"epJSON Editor - {self.current_file_path}")

    def handle_save_file(self, _):
        try:
            self.save_current_file(self.current_file_path)
        except IOError:
            wx.LogError(f"Cannot save current data in file {self.current_file_path}")

    def handle_save_as_file(self, _):
        default_file_path = ""
        if self.current_file_path is not None:
            default_file_path = self.current_file_path
        with wx.FileDialog(self, "Save EnergyPlus epJSON file", wildcard="epJSON files (*.epJSON)|*.epJSON",
                           style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
                           defaultFile=default_file_path) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return  # the user changed their mind
            pathname = fileDialog.GetPath()
            try:
                self.save_current_file(pathname)
            except IOError:
                wx.LogError(f"Cannot save current data in file {pathname}")
            self.changes_not_saved = False
            self.update_title()
            self.Refresh()

    def save_current_file(self, path_name):
        self.current_file_path = path_name
        self.changes_not_saved = False
        self.update_title()
        with open(path_name, 'w') as output_file:
            json.dump(self.current_file, output_file, indent=4)
        self.check_file_with_schema()
        self.Refresh()

    def handle_close(self, event):
        if event.CanVeto() and self.changes_not_saved:
            if wx.MessageBox("Do you want an opportunity to save the changes you made prior to clearing this file?",
                             "Please confirm",
                             wx.ICON_QUESTION | wx.YES_NO) != wx.NO:
                event.Veto()
                return
        # de-initialize the frame manager
        self._mgr.UnInit()
        event.Skip()

    def handle_select_object_list_item(self, event):
        selected_line = self.object_list_tree.GetItemText(event.GetItem())
        current_object_name = selected_line[7:]  # remove the bracketed number
        if current_object_name in self.name_to_object_list_item:
            self.selected_object_tree_item = event.GetItem()
            self.selected_object_name = current_object_name
            self.display_explanation(self.selected_object_name)
            self.jump_destination_list.DeleteAllItems()
            self.update_grid(self.selected_object_name)
            self.Refresh()

    def update_list_of_object_counts(self):
        # first make all items grey
        for tree_item in self.name_to_object_list_item.values():
            self.object_list_tree.SetItemTextColour(tree_item, "GREY")
        for object_name, object_dict in self.current_file.items():
            self.update_list_of_object_count(object_name, len(object_dict))
        self.Refresh()
        return

    def update_list_of_object_count(self, object_name, count):
        tree_item = self.name_to_object_list_item[object_name]
        self.object_list_tree.SetItemText(tree_item, self.object_list_format(object_name, count))
        if count > 0:
            self.object_list_tree.SetItemTextColour(tree_item, "BLACK")
        return

    @staticmethod
    def object_list_format(name, count):
        count_string = str(count).zfill(4)
        return f"[{count_string}] {name}"

    def display_explanation(self, object_name, row_number=-1):
        explanation = f"Object Description: {object_name}" + os.linesep + os.linesep + \
                      self.data_dictionary[object_name].memo
        if row_number != -1:
            current_field = self.row_fields[row_number]
            if 'display_field_name' in current_field:
                explanation += os.linesep + os.linesep + f"Field Description: {current_field['display_field_name']}"
            if 'note' in current_field:
                explanation += os.linesep + os.linesep + current_field['note'] + os.linesep
            if 'default' in current_field:
                default_value = self.convert_unit_to_ip_using_row_index(current_field['default'], row_number)
                explanation += os.linesep + f"Default value: {str(default_value)}"
            if 'minimum' in current_field or 'maximum' in current_field:
                range_string = "Range: "
                if 'minimum' in current_field:
                    minimum_value = self.convert_unit_to_ip_using_row_index(current_field['minimum'], row_number)
                    range_string += str(minimum_value)
                    if 'exclusiveMinimum' in current_field:
                        range_string += " < "
                    else:
                        range_string += " <= "
                else:
                    range_string += 'No minimum but'
                range_string += " X "
                if 'maximum' in current_field:
                    if 'exclusiveMaximum' in current_field:
                        range_string += " < "
                    else:
                        range_string += " <= "
                    maximum_value = self.convert_unit_to_ip_using_row_index(current_field['maximum'], row_number)
                    range_string += str(maximum_value)
                else:
                    range_string += 'but no maximum.'
                explanation += os.linesep + range_string
            if 'is_required' in current_field:
                if current_field['is_required']:
                    explanation += os.linesep + "This field is required"
        self.explanation_text.Value = explanation

    def update_grid(self, selected_object_name):
        self.set_grid_settings()
        print(selected_object_name)
        selected_object_dict = self.data_dictionary[selected_object_name]
        self.field_name_to_display_name = {}
        self.field_to_row_number = {}
        # construct list that contains field dictionary for each row of the grid
        self.row_fields = self.create_row_by_row_field_list(selected_object_dict, selected_object_name)
        new_columns = 1
        if selected_object_name in self.current_file:
            new_columns = len(self.current_file[selected_object_name]) + 1
        self.resize_grid_rows_columns(len(self.row_fields), new_columns)
        # add field names and units
        for row_counter, row_field in enumerate(self.row_fields):
            self.main_grid.SetRowLabelValue(row_counter, row_field["display_field_name"])
            self.field_to_row_number[row_field["display_field_name"]] = row_counter
            self.field_name_to_display_name[row_field["field_name"]] = row_field["display_field_name"]
            self.main_grid.SetCellValue(row_counter, 0, self.display_unit(row_field))
            self.main_grid.SetReadOnly(row_counter, 0, True)
        # populate the grid with the field values from the current file
        max_row = self.main_grid.GetNumberRows()
        max_col = self.main_grid.GetNumberCols()
        if selected_object_name in self.current_file:
            active_input_objects = self.current_file[selected_object_name]
            self.column_input_object_names = ['skip column zero', ]  # we never need the first element
            for column_counter, active_input_object_name in enumerate(active_input_objects, start=1):
                self.column_input_object_names.append(active_input_object_name)
                self.name_to_column_number[active_input_object_name] = column_counter
                for row_counter, row_field in enumerate(self.row_fields):
                    if column_counter < max_col and row_counter < max_row:
                        display_value, unconverted_value = self.display_cell_value(row_counter,
                                                                                   active_input_object_name,
                                                                                   active_input_objects)
                        self.main_grid.SetCellValue(row_counter, column_counter, display_value)
                        if self.is_value_valid(row_counter, unconverted_value):
                            self.main_grid.SetCellBackgroundColour(row_counter, column_counter, "white")
                        else:
                            self.main_grid.SetCellBackgroundColour(row_counter, column_counter, "tan")
        # self.main_grid.AutoSizeColumns()
        self.resize_auto_plus_all_columns()
        self.main_grid.SetRowLabelSize(wx.grid.GRID_AUTOSIZE)
        self.main_grid.SetRowLabelAlignment(wx.ALIGN_LEFT, wx.ALIGN_TOP)

    def set_grid_settings(self):
        self.main_grid.ClearGrid()
        self.main_grid.FreezeTo(0, 1)
        self.main_grid.SetCornerLabelValue("Field")
        self.main_grid.SetColLabelValue(0, "Units")

    def resize_auto_plus_all_columns(self):
        self.main_grid.AutoSizeColumns()
        for col in range(1, self.main_grid.GetNumberCols()):
            self.main_grid.SetColSize(col, self.main_grid.GetColSize(col) + 50)

    def create_row_by_row_field_list(self, object_dict, object_name):
        row_fields = []
        for item in object_dict.input_fields:
            current_field = object_dict.input_fields[item]
            current_field["field_name"] = item
            if "field_name_with_spaces" in current_field:
                current_field["display_field_name"] = current_field["field_name_with_spaces"]
            row_fields.append(current_field)
        if object_dict.extensible_size > 0:  # add extensible fields if present
            last_field_name = row_fields[-1]["field_name"]

            repeat_extension_fields = self.maximum_repeats_of_extensible_fields(object_name, last_field_name) + self. \
                additional_sets_of_fields
            row_fields.pop()  # for extensible object don't need last item
            for repeat_field_group in range(repeat_extension_fields):
                for item in object_dict.input_fields[last_field_name]:
                    if item != "field_name":
                        current_field = object_dict.input_fields[last_field_name][item]
                        current_field["field_name"] = item
                        current_field["display_field_name"] = current_field["field_name_with_spaces"] + "-" + str(
                            repeat_field_group + 1).zfill(3)
                        current_field["extensible_root_field_name"] = last_field_name
                        current_field["extensible_repeat_group"] = repeat_field_group
                        row_fields.append(current_field.copy())
        return row_fields

    def display_unit(self, input_field):
        unit_string = ""
        if "units" in input_field:
            if self.use_si_units:
                unit_string = input_field["units"]
            else:
                if input_field["units"] in self.unit_conversions:
                    if "ip_unit" in self.unit_conversions[input_field["units"]]:
                        unit_string = self.unit_conversions[input_field["units"]]["ip_unit"]
                    else:
                        print("ip-unit missing: " + input_field["units"])
                else:
                    print("ip-unit missing: " + input_field["units"])
        return unit_string

    def resize_grid_rows_columns(self, number_of_rows, number_of_columns):
        # resize the number of rows in the grid to correspond to longest object
        current_rows = self.main_grid.GetNumberRows()
        if number_of_rows < current_rows:
            self.main_grid.DeleteRows(0, current_rows - number_of_rows, True)
        if number_of_rows > current_rows:
            self.main_grid.AppendRows(number_of_rows - current_rows)
        # resize the number of columns to be the number of input objects
        current_columns = self.main_grid.GetNumberCols()
        if number_of_columns < current_columns:
            self.main_grid.DeleteCols(0, current_columns - number_of_columns, True)
        if number_of_columns > current_columns:
            self.main_grid.AppendCols(number_of_columns - current_columns)
        for counter in range(1, number_of_columns):
            self.main_grid.SetColLabelValue(counter, f"Obj{counter}")

    def display_cell_value(self, row_index, active_input_object_name, active_input_objects):
        cell_value = ""
        row_field = self.row_fields[row_index]
        if row_field["field_name"] == "name":
            cell_value = active_input_object_name
        elif row_field["field_name"] in active_input_objects[active_input_object_name]:
            cell_value = active_input_objects[active_input_object_name][row_field["field_name"]]
        elif "extensible_root_field_name" in row_field:
            if active_input_object_name in active_input_objects:
                if row_field["extensible_root_field_name"] in active_input_objects[active_input_object_name]:
                    extensible_field_list = active_input_objects[active_input_object_name][
                        row_field["extensible_root_field_name"]]
                    if row_field["extensible_repeat_group"] < len(extensible_field_list):
                        extensible_field = extensible_field_list[row_field["extensible_repeat_group"]]
                        if row_field["field_name"] in extensible_field:
                            cell_value = extensible_field[row_field["field_name"]]
        if not self.use_si_units:
            cell_value_string = str(self.convert_unit_to_ip_using_row_index(cell_value, row_index))
        else:
            cell_value_string = str(cell_value)
        return cell_value_string, cell_value

    def is_value_valid(self, row_index, value):
        row_field = self.row_fields[row_index]
        if 'type' in row_field:
            if (row_field['type'] == 'number' or row_field['type'] == 'number_or_string') and value != '':
                if self.is_convertible_to_float(value):
                    numeric_value = float(value)
                    if not self.use_si_units:
                        numeric_value = self.convert_unit_to_si_using_row_index(numeric_value, row_index)
                    if 'minimum' in row_field:
                        if 'exclusiveMinimum' in row_field:
                            if numeric_value <= row_field['minimum']:
                                return False
                        else:
                            if numeric_value < row_field['minimum']:
                                return False
                    if 'maximum' in row_field:
                        if 'exclusiveMaximum' in row_field:
                            if numeric_value >= row_field['maximum']:
                                return False
                        else:
                            if numeric_value > row_field['maximum']:
                                return False
            elif 'enum' in row_field:
                if value:  # don't check enums if blank
                    if value not in row_field['enum']:
                        return False
        else:
            print(f'type not found in row field for {row_index} and value {value} may be due to anyOf')
        return True

    @staticmethod
    def is_convertible_to_float(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def convert_unit_to_ip_using_row_index(self, value_to_convert, row_index):
        row_field = self.row_fields[row_index]
        converted_value = value_to_convert  # return value is input unless converted
        if self.use_si_units:
            return converted_value
        if type(value_to_convert) is float or type(value_to_convert) is int:
            if "type" in row_field:
                if row_field["type"] == "number" or row_field["type"] == "number_or_string":
                    if "units" in row_field and not self.use_si_units:
                        if "ip_unit" in row_field:
                            unit_lookup = row_field["units"] + "___" + row_field["ip_unit"]
                        else:
                            unit_lookup = row_field["units"]
                        converted_value = self.convert_using_unit_string_to_ip(value_to_convert, unit_lookup)
        return converted_value

    def convert_using_unit_string_to_ip(self, value_to_convert, unit_string):
        converted_value = value_to_convert * self.unit_conversions[unit_string]["multiplier"]
        if "offset" in self.unit_conversions[unit_string]:
            converted_value = converted_value + self.unit_conversions[unit_string]["offset"]
        return converted_value

    def convert_unit_to_si_using_row_index(self, value_to_convert, row_index):
        row_field = self.row_fields[row_index]
        converted_value = value_to_convert  # return value is input unless converted
        if self.use_si_units:
            return converted_value
        if type(value_to_convert) is float or type(value_to_convert) is int:
            if "type" in row_field:
                if row_field["type"] == "number" or row_field["type"] == "number_or_string":
                    if "units" in row_field and not self.use_si_units:
                        if "ip_unit" in row_field:
                            unit_lookup = row_field["units"] + "___" + row_field["ip_unit"]
                        else:
                            unit_lookup = row_field["units"]
                        converted_value = self.convert_using_unit_string_to_si(value_to_convert, unit_lookup)
        return converted_value

    def convert_using_unit_string_to_si(self, value_to_convert, unit_string):
        converted_value = value_to_convert
        if "offset" in self.unit_conversions[unit_string]:
            converted_value = converted_value - self.unit_conversions[unit_string]["offset"]
        converted_value = converted_value / self.unit_conversions[unit_string]["multiplier"]
        return converted_value

    def handle_grid_label_click(self, event):
        cell_column = event.GetCol()
        if cell_column > 0:
            self.main_grid.SelectCol(cell_column)

    def handle_cell_left_click(self, event):
        cell_row = event.GetRow()
        cell_column = event.GetCol()
        if cell_column > 0:
            self.enter_cell(cell_row, cell_column)
        event.Skip()

    def handle_cell_select_cell(self, event):
        cell_row = event.GetRow()
        cell_column = event.GetCol()
        if cell_column > 0:
            self.enter_cell(cell_row, cell_column)
        event.Skip()

    def enter_cell(self, cell_row, cell_column):
        # active_field = self.row_fields[cell_row]
        # object_name = self.main_grid.GetCellValue(0, cell_column)
        value_string = self.main_grid.GetCellValue(cell_row, cell_column)
        # print(f"left click ({cell_row}, {cell_column}) for field {active_field['display_field_name']} "
        #       f"for object {object_name} with a value of {value_string}")
        self.display_explanation(self.selected_object_name, row_number=cell_row)
        self.set_cell_choices(cell_row, cell_column)
        self.populate_jump_list(value_string)
        # the following code was an attempt to get the cell selection, pull down, and keystroke input to work like
        # the classic IDF Editor.
        # if self.main_grid.CanEnableCellControl():
        #    self.main_grid.EnableCellEditControl()
        # self.main_grid.GoToCell(cell_row, cell_column)
        # cell_editor = self.main_grid.GetCellEditor(cell_row, cell_column)
        # cell_editor.BeginEdit(cell_row, cell_column, self.main_grid)
        # cell_editor.Show(True)

    def handle_cell_changed(self, event):
        # remove the characters after the pipe character | that are shown in the dropdown list.
        cell_row = event.GetRow()
        cell_column = event.GetCol()
        original_string = event.GetString()
        changed_string = self.remove_pipe_and_after(self.main_grid.GetCellValue(cell_row, cell_column))
        print(f" original_string: '{original_string}'  changed_string: '{changed_string}'  and if they are equal: "
              f"{original_string == changed_string}")
        if original_string != changed_string:
            self.set_file_value(cell_row, cell_column, changed_string)
            self.changes_not_saved = True
            self.update_title()
        self.main_grid.SetCellValue(cell_row, cell_column, changed_string)
        if self.is_value_valid(cell_row, changed_string):
            self.main_grid.SetCellBackgroundColour(cell_row, cell_column, "white")
        else:
            self.main_grid.SetCellBackgroundColour(cell_row, cell_column, "tan")

    def set_file_value(self, cell_row, cell_column, new_cell_value_string):
        active_input_objects = self.current_file[self.selected_object_name]
        current_input_object_name = self.column_input_object_names[cell_column]
        active_input_object = active_input_objects[current_input_object_name]
        row_field = self.row_fields[cell_row]
        updated_cell_value = new_cell_value_string
        if self.is_convertible_to_float(new_cell_value_string) and row_field['type'] == 'number' or \
                row_field['type'] == 'number_or_string':
            updated_cell_value = float(updated_cell_value)
            if not self.use_si_units:
                updated_cell_value = self.convert_unit_to_si_using_row_index(updated_cell_value, cell_row)
        # set the value in the json data structure
        if row_field['field_name'] == 'name':
            active_input_objects[updated_cell_value] = active_input_objects.pop(current_input_object_name)
            self.column_input_object_names[cell_column] = updated_cell_value
        elif "extensible_root_field_name" in row_field:
            if row_field["extensible_root_field_name"] in active_input_objects[current_input_object_name]:
                extensible_field_list = active_input_objects[current_input_object_name][
                    row_field["extensible_root_field_name"]]
            else:  # if no extensible fields exist at all for the object
                extensible_field_list = []
                active_input_objects[current_input_object_name][row_field["extensible_root_field_name"]] = \
                    extensible_field_list
            if row_field["extensible_repeat_group"] >= len(extensible_field_list):
                # if editing a field beyond the length of the existing object
                input_fields_of_object = self.data_dictionary[self.selected_object_name].input_fields
                if row_field['extensible_root_field_name'] in input_fields_of_object:
                    all_field_keys = input_fields_of_object[row_field['extensible_root_field_name']].keys()
                    blank_set_fields = {k: '' for k in all_field_keys if k != 'field_name'}
                    for i in range(len(extensible_field_list), row_field["extensible_repeat_group"] + 1):
                        extensible_field_list.append(blank_set_fields.copy())
                    # show the new lines added
                    self.update_grid(self.selected_object_name)
            extensible_field = extensible_field_list[row_field["extensible_repeat_group"]]
            extensible_field[row_field["field_name"]] = updated_cell_value
        else:
            active_input_object[row_field['field_name']] = updated_cell_value

    @staticmethod
    def remove_pipe_and_after(string_with_pipe):
        pipe_pos = string_with_pipe.find('|')
        return_string = string_with_pipe
        if pipe_pos > 0:
            # remove from one character before the pipe since also added a space
            return_string = string_with_pipe[:(pipe_pos - 1)]
        return return_string

    def set_cell_choices(self, cell_row, cell_column):
        row_field = self.row_fields[cell_row]
        choices = [str(self.main_grid.GetCellValue(cell_row, cell_column)) + " | current"]
        if 'enum' in row_field:
            for option in row_field['enum']:
                choices.append(str(option) + " | choice")
        if 'object_list' in row_field:
            for reference_list_name in row_field['object_list']:
                if reference_list_name in self.reference_names:
                    for referenced_name in self.reference_names[reference_list_name]:
                        choices.append(referenced_name + " | object")
        if 'default' in row_field:
            choices.append(str(self.convert_unit_to_ip_using_row_index(row_field['default'], cell_row)) + " | default")
        if 'minimum' in row_field:
            choices.append(str(self.convert_unit_to_ip_using_row_index(row_field['minimum'], cell_row)) + " | minimum")
        if 'maximum' in row_field:
            choices.append(str(self.convert_unit_to_ip_using_row_index(row_field['maximum'], cell_row)) + " | maximum")
        self.main_grid.SetCellEditor(cell_row, cell_column,
                                     wx.grid.GridCellChoiceEditor(choices, allowOthers=True))
        # the following code was an attempt to get the cell selection, pull down, and keystroke input to work like
        # the classic IDF Editor.
        # cell_editor = self.main_grid.GetCellEditor(cell_row, cell_column)
        # cell_editor.BeginEdit(cell_row, cell_column, self.main_grid)

    def maximum_repeats_of_extensible_fields(self, selected_object_name, field_name):
        max_repeat = 0
        if selected_object_name in self.current_file:
            active_input_objects = self.current_file[selected_object_name]
            for active_input_object in active_input_objects.keys():
                if active_input_object in active_input_objects:
                    if field_name in active_input_objects[active_input_object]:
                        max_repeat = max(max_repeat, len(active_input_objects[active_input_object][field_name]))
        return max_repeat

    def create_data_dictionary(self):
        """
         Create the simplified version of the Energy+.schema.epJSON that
         is closer to what is needed for displaying the grid elements
        """
        locate_schema = LocateSchema()
        path_to_schema = locate_schema.get_schema_path()
        print(f"Schema found: {path_to_schema}")
        if path_to_schema:
            with open(path_to_schema) as schema_file:
                ep_schema_for_validation = json.load(schema_file)
                self.validator = ValidateEpJson(ep_schema_for_validation)
            with open(path_to_schema) as schema_file:
                ep_schema = json.load(schema_file)
                for object_name, json_properties in ep_schema["properties"].items():
                    self.data_dictionary[object_name] = SchemaInputObject(json_properties)
                references_from_data_dictionary = ReferencesFromDataDictionary(self.data_dictionary)
                self.cross_references = references_from_data_dictionary.reference_fields
        else:
            print("No Energy+.schema.epJSON file found.")

    def read_unit_conversions(self):
        """
         Read the unit conversion file as a dictionary
        """
        with open(os.path.join(application_path, "support", "unit_conversions.json")) as unit_conversion_file:
            self.unit_conversions = json.load(unit_conversion_file)

    def gather_active_references(self):
        for reference_list_name in self.cross_references.keys():
            current_reference_list = self.get_active_reference_list(reference_list_name)
            if current_reference_list:
                self.reference_names[reference_list_name] = current_reference_list

    def get_active_reference_list(self, reference_list_name):
        list_object_field = self.cross_references[reference_list_name]
        current_reference_list = []
        for object_field in list_object_field:
            (object_name, field_name) = object_field
            if object_name in self.current_file:
                active_objects = self.current_file[object_name]
                if field_name == 'name':
                    current_reference_list.extend(list(active_objects.keys()))
                else:
                    print(f"Objects that use fields other than 'name' for reference lists {active_objects} "
                          f"and the field is {field_name}")
        return current_reference_list

    def populate_jump_list(self, value_string):
        self.jump_destination_list.DeleteAllItems()
        if value_string in self.jumps:
            destinations = self.jumps[value_string]
            for destination in destinations:
                self.jump_destination_list.Append(destination)
        return

    def update_dict_of_jumps(self):
        start = time.time()
        for object_name, object_instances in self.current_file.items():
            input_fields_of_object = self.data_dictionary[object_name].input_fields
            for input_field, field_description in input_fields_of_object.items():
                if 'field_name_with_spaces' in field_description:
                    field_name_no_underscore = field_description['field_name_with_spaces']
                else:
                    field_name_no_underscore = input_field
                if 'type' in field_description:
                    if (field_description['type'] == 'string' or field_description['type'] == 'number_or_string') \
                            and 'enum' not in field_description:
                        for cur_name, cur_fields in object_instances.items():
                            if input_field in cur_fields:
                                jump_string = cur_fields[input_field]
                                self.add_jump_string(jump_string, object_name, cur_name, field_name_no_underscore)

                            elif 'name' in input_fields_of_object:
                                self.add_jump_string(cur_name, object_name, cur_name, 'Name')
        # remove items from list of jump that are singles
        to_deletes = []
        for jump_name, destination_of_jump in self.jumps.items():
            if len(destination_of_jump) == 1:
                to_deletes.append(jump_name)
        for to_delete in to_deletes:
            del self.jumps[to_delete]
        end = time.time()
        print(f"time for update_dict_of_jumps is {end - start}")
        return

    def add_jump_string(self, jump_string, object_name, cur_name, input_field):
        destination_of_jump = (cur_name, object_name, input_field)
        if jump_string not in self.jumps:
            self.jumps[jump_string] = []
        if destination_of_jump not in self.jumps[jump_string]:
            self.jumps[jump_string].append(destination_of_jump)

    def handle_new_object(self, _):
        all_objects_in_class = {}
        count_of_objects = 0
        if self.selected_object_name in self.current_file:
            all_objects_in_class = self.current_file[self.selected_object_name]
            count_of_objects = len(all_objects_in_class)
        new_object = {}
        fields_of_object = self.data_dictionary[self.selected_object_name].input_fields
        for field_name, field_details in fields_of_object.items():
            if 'default' in field_details:
                new_object[field_name] = field_details['default']
            elif 'enum' in field_details:
                new_object[field_name] = field_details['enum'][0]
            else:
                if 'type' in field_details:
                    if field_details['type'] == 'string':
                        new_object[field_name] = ''
                if 'is_required' in field_details:
                    if field_details['is_required']:
                        if 'minimum' in field_details:
                            new_object[field_name] = field_details['minimum']
                        elif 'maximum' in field_details:
                            new_object[field_name] = field_details['maximum']
        all_objects_in_class[f'new-{count_of_objects + 1}'] = new_object
        if count_of_objects == 0:
            self.current_file[self.selected_object_name] = all_objects_in_class
        self.update_grid(self.selected_object_name)
        self.update_list_of_object_counts()
        self.changes_not_saved = True
        self.update_title()

    def handle_duplicate_object(self, _):
        columns_selected = self.main_grid.GetSelectedCols()
        if self.selected_object_name in self.current_file:
            all_objects_in_class = self.current_file[self.selected_object_name]
            for column_selected in columns_selected:
                object_name = self.main_grid.GetCellValue(0, column_selected)
                original_object = all_objects_in_class[object_name]
                duplicated_object = original_object.copy()
                all_objects_in_class[object_name + "-copy"] = duplicated_object
            self.update_grid(self.selected_object_name)
            self.update_list_of_object_counts()
            self.changes_not_saved = True
            self.update_title()

    def handle_tb_delete_object(self, _):
        columns_selected = self.main_grid.GetSelectedCols()
        if self.selected_object_name in self.current_file:
            all_objects_in_class = self.current_file[self.selected_object_name]
            for column_selected in columns_selected:
                object_name = self.column_input_object_names[column_selected]
                if object_name in all_objects_in_class:
                    del all_objects_in_class[object_name]
                else:
                    object_name = self.main_grid.GetCellValue(0, column_selected)
                    if object_name in all_objects_in_class:
                        del all_objects_in_class[object_name]
            self.update_grid(self.selected_object_name)
            self.update_list_of_object_counts()
            self.changes_not_saved = True
            self.update_title()

    def handle_tb_copy_object(self, _):
        to_copy = {}
        instances_to_copy = {}
        columns_selected = self.main_grid.GetSelectedCols()
        if self.selected_object_name in self.current_file:
            all_objects_in_class = self.current_file[self.selected_object_name]
            for column_selected in columns_selected:
                object_name = self.main_grid.GetCellValue(0, column_selected)
                if object_name in all_objects_in_class:
                    instances_to_copy[object_name] = all_objects_in_class[object_name].copy()
            to_copy[self.selected_object_name] = instances_to_copy
            text_to_copy = json.dumps(to_copy, indent=4)
            if wx.TheClipboard.Open():
                wx.TheClipboard.SetData(wx.TextDataObject(text_to_copy))
                wx.TheClipboard.Close()

    def handle_tb_paste_object(self, _):
        text_data = wx.TextDataObject()
        success = False
        if wx.TheClipboard.Open():
            success = wx.TheClipboard.GetData(text_data)
            wx.TheClipboard.Close()
        if success:
            text_from_clipboard = text_data.GetText()
            try:
                dict_from_clipboard = json.loads(text_from_clipboard)
            except ValueError:
                print("Trying to paste something that is not JSON text from clipboard")
                print(text_from_clipboard)
                return
            print(dict_from_clipboard)
            for class_name, object_instances in dict_from_clipboard.items():
                if class_name in self.data_dictionary:
                    self.selected_object_name = class_name
                    if class_name in self.current_file:
                        for object_name, fields in object_instances.items():
                            if object_name in self.current_file[class_name]:
                                self.current_file[class_name][object_name + "-copy"] = fields
                            else:
                                self.current_file[class_name][object_name] = fields
                    else:
                        self.current_file[class_name] = object_instances
            object_list_item = self.name_to_object_list_item[self.selected_object_name]
            self.object_list_tree.SelectItem(object_list_item)  # this triggers update_grid
            self.update_grid(self.selected_object_name)
            self.update_list_of_object_counts()
            self.changes_not_saved = True
            self.update_title()

    def handle_tb_help_menu(self, _):
        help_menu = wx.Menu()
        tb_help_about = help_menu.Append(wx.NewId(), "About")
        self.Bind(wx.EVT_MENU, self.handle_tb_help_about, tb_help_about)
        self.PopupMenu(help_menu)

    def handle_tb_help_about(self, _):
        print('tb help about')
        text = """
epJSON Editor

Version 1.0
Copyright (c) 2021-2022, Oak Ridge National Laboratory, managed by UT-Battelle, GARD Analytics, Inc, and contributors

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
        """
        with wx.MessageDialog(self, text, 'About epJSON Editor', wx.OK | wx.ICON_INFORMATION) as dlg:
            dlg.ShowModal()
