import wx
import wx.grid
import wx.lib.agw.aui as aui
import os
import json

from epjsoneditor.schemainputobject import SchemaInputObject
from epjsoneditor.referencesfromdatadictionary import ReferencesFromDataDictionary
from epjsoneditor.interface.settings_dialog import SettingsDialog


class EpJsonEditorFrame(wx.Frame):

    def __init__(self, parent, id=-1, title="epJSON Editor - ", pos=wx.DefaultPosition,
                 size=(1200, 800), style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        self._mgr = aui.AuiManager()

        self.data_dictionary = {}
        self.cross_references = {}
        self.reference_names = {}
        self.create_data_dictionary()
        self.explanation_text = None
        self.object_list_tree = None
        self.object_list_root = None
        self.main_grid = None
        self.selected_object_name = None
        self.current_file_path = None
        self.use_si_units = True
        self.row_fields = None
        self.column_input_object_names = None
        self.unit_conversions = {}
        self.read_unit_conversions()
        self.current_file = {}
        self.create_gui()

    def create_gui(self):

        # notify AUI which frame to use
        self._mgr.SetManagedWindow(self)

        self.object_list_tree = wx.TreeCtrl(self, style=wx.TR_HIDE_ROOT)
        self.object_list_root = self.object_list_tree.AddRoot("All Input Objects")
        self.object_list_tree.SetItemData(self.object_list_root, None)
        for child in self.data_dictionary.keys():
            child = self.object_list_tree.AppendItem(self.object_list_root, child)
            self.object_list_tree.Expand(child)

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
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGED, self.handle_cell_changed)

        self._mgr.AddPane(self.main_grid, aui.AuiPaneInfo().Name("grid_content").
                          CenterPane().Hide().MinimizeButton(True))

        pnl = wx.Panel(self)
        pbox = wx.BoxSizer(wx.VERTICAL)

        tb_search = aui.AuiToolBar(pnl, -1, wx.DefaultPosition, wx.DefaultSize) # agwStyle=aui.AUI_TB_TEXT
        tb_search.SetToolBitmapSize(wx.Size(12, 12))
        tb_search.AddSimpleTool(10, "New", wx.ArtProvider.GetBitmap(wx.ART_NEW))

        tb_open_file = tb_search.AddSimpleTool(11, "Open", wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN))
        tb_save_file = tb_search.AddSimpleTool(12, "Save", wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE))
        tb_save_as_file = tb_search.AddSimpleTool(13, "Save As", wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS))
        tb_search.Realize()
        pbox.Add(tb_search, 0, flag=wx.TOP)

        notebook = aui.AuiNotebook(pnl)
        jump_panel = wx.Panel(notebook)
        text7 = wx.TextCtrl(jump_panel, -1, "jump panel in notebook1",
                            wx.DefaultPosition, wx.Size(100, 150),
                            wx.NO_BORDER | wx.TE_MULTILINE)
        notebook.AddPage(text7, "Jump1")
        text8 = wx.TextCtrl(jump_panel, -1, "jump panel in notebook2",
                            wx.DefaultPosition, wx.Size(100, 150),
                            wx.NO_BORDER | wx.TE_MULTILINE)
        notebook.AddPage(text8, "Jump2")
        jump_results = wx.ListCtrl(jump_panel, -1, style=wx.LC_REPORT)
        jump_results.InsertColumn(0,'result', width=100)
        jump_results.InsertColumn(1,'object', width=80)
        jump_results.Append(("first", "base"))
        jump_results.Append(("second", "base"))
        jump_results.Append(("third", "base"))
        jump_results.Append(("home", "plate"))
        notebook.AddPage(jump_results, "Jump3")
        pbox.Add(notebook, 1, flag=wx.EXPAND)


        #button1 = wx.Button(pnl, -1, "click me")
        #pbox.Add(button1, 1, flag=wx.ALL)

        #text5 = wx.TextCtrl(pnl, -1, "Bottom Text in Panel",
        #                    wx.DefaultPosition, wx.Size(200, 150),
        #                    wx.NO_BORDER | wx.TE_MULTILINE)
        #pbox.Add(text5, 1, flag=wx.EXPAND)
        pnl.SetSizer(pbox)
        self._mgr.AddPane(pnl, aui.AuiPaneInfo().Bottom().Name("bottom_search").Caption("Jump and Search"))

        # Layer(2) allows it to take all of left side
        self._mgr.AddPane(self.object_list_tree, aui.AuiPaneInfo().Left().Layer(2).Caption("List of Input Objects"))

        # tell the manager to "commit" all the changes just made
        self._mgr.Update()

        # it works better to have TextCntrl for CenterPane shown and hidden and the grid being hidden then shown
        self._mgr.GetPane("grid_content").Show(True)
        self._mgr.GetPane("text_content").Show(False)
        self._mgr.Update()

        self.create_toolbar()

        self.Bind(wx.EVT_CLOSE, self.handle_close)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.select_object_list_item, self.object_list_tree)

    def create_grid(self):
        grid = wx.grid.Grid(self, -1, wx.Point(0, 0), wx.Size(150, 250),
                            wx.NO_BORDER | wx.WANTS_CHARS)
        grid.CreateGrid(5, 5)
        return grid

    def create_toolbar(self):
        # create some toolbars
        tb1 = aui.AuiToolBar(self, -1, wx.DefaultPosition, wx.DefaultSize,
                             agwStyle=aui.AUI_TB_TEXT)
        tb1.SetToolBitmapSize(wx.Size(48, 48))
        tb1.AddSimpleTool(10, "New", wx.ArtProvider.GetBitmap(wx.ART_NEW))

        tb_open_file = tb1.AddSimpleTool(11, "Open", wx.ArtProvider.GetBitmap(wx.ART_FILE_OPEN))
        self.Bind(wx.EVT_TOOL, self.handle_open_file, tb_open_file)

        tb_save_file = tb1.AddSimpleTool(12, "Save", wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE))
        self.Bind(wx.EVT_TOOL, self.handle_save_file, tb_save_file)

        tb_save_as_file = tb1.AddSimpleTool(13, "Save As", wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS))
        self.Bind(wx.EVT_TOOL, self.handle_save_as_file, tb_save_as_file)

        tb1.AddSeparator()
        tb1.AddSimpleTool(14, "Undo", wx.ArtProvider.GetBitmap(wx.ART_UNDO))
        tb1.AddSimpleTool(15, "Redo", wx.ArtProvider.GetBitmap(wx.ART_REDO))
        tb1.AddSeparator()
        tb1.AddSimpleTool(16, "New Obj", wx.ArtProvider.GetBitmap(wx.ART_PLUS))
        tb1.AddSimpleTool(17, "Dup Obj", wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD))  # duplicate
        tb1.AddSimpleTool(18, "Dup Obj + Chg", wx.ArtProvider.GetBitmap(wx.ART_GOTO_LAST))  # duplicate and change
        tb1.AddSimpleTool(19, "Del Obj", wx.ArtProvider.GetBitmap(wx.ART_MINUS))
        tb1.AddSimpleTool(20, "Copy Obj", wx.ArtProvider.GetBitmap(wx.ART_COPY))
        tb1.AddSimpleTool(21, "Paste Obj", wx.ArtProvider.GetBitmap(wx.ART_PASTE))
        # tb1.AddSeparator()
        # tb1.AddTool(22, "IP Units", wx.ArtProvider.GetBitmap(wx.ART_GO_UP), wx.NullBitmap, kind=wx.ITEM_RADIO)
        # tb1.AddTool(23, "SI Units", wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN), wx.NullBitmap, kind=wx.ITEM_RADIO)
        tb1.AddSeparator()
        tb_settings = tb1.AddSimpleTool(25, "Settings", wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE))
        self.Bind(wx.EVT_TOOL, self.handle_settings_toolbar_button, tb_settings)
        tb1.AddSimpleTool(26, "Help", wx.ArtProvider.GetBitmap(wx.ART_HELP))
        tb1.Realize()
        self._mgr.AddPane(tb1, aui.AuiPaneInfo().Name("tb1").Caption("Primary Toolbar").
                          ToolbarPane().Top())
        self._mgr.Update()

    def handle_open_file(self, _):
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

    def load_current_file(self, path_name):
        if os.path.exists(path_name):
            self.current_file_path = path_name
            self.SetTitle(f"epJSON Editor - {path_name}")
            with open(path_name) as input_file:
                self.current_file = json.load(input_file)
                self.gather_active_references()
            self.Refresh()

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

    def save_current_file(self, path_name):
        self.current_file_path = path_name
        self.SetTitle(f"epJSON Editor - {path_name}")
        with open(path_name, 'w') as output_file:
            json.dump(self.current_file, output_file, indent=4)
        self.Refresh()

    def handle_close(self, event):
        # de-initialize the frame manager
        self._mgr.UnInit()
        event.Skip()

    def select_object_list_item(self, event):
        self.selected_object_name = self.object_list_tree.GetItemText(event.GetItem())
        self.display_explanation(self.selected_object_name)
        self.update_grid(self.selected_object_name)
        self.Refresh()

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
                default_value = self.convert_unit_using_row_index(current_field['default'], row_number)
                explanation += os.linesep + f"Default value: {str(default_value)}"
            if 'minimum' in current_field or 'maximum' in current_field:
                range_string = "Range: "
                if 'minimum' in current_field:
                    minimum_value = self.convert_unit_using_row_index(current_field['minimum'], row_number)
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
                    maximum_value = self.convert_unit_using_row_index(current_field['maximum'], row_number)
                    range_string += str(maximum_value)
                else:
                    range_string += 'but no maximum.'
                explanation += os.linesep + range_string
            if 'is_required' in current_field:
                explanation += os.linesep + "This field is required"
        self.explanation_text.Value = explanation

    def update_grid(self, selected_object_name):
        self.set_grid_settings()
        print(selected_object_name)
        selected_object_dict = self.data_dictionary[selected_object_name]
        # construct list that contains field dictionary for each row of the grid
        self.row_fields = self.create_row_by_row_field_list(selected_object_dict, selected_object_name)
        new_columns = 1
        if selected_object_name in self.current_file:
            new_columns = len(self.current_file[selected_object_name]) + 1
        self.resize_grid_rows_columns(len(self.row_fields), new_columns)
        # add field names and units
        for row_counter, row_field in enumerate(self.row_fields):
            self.main_grid.SetRowLabelValue(row_counter, row_field["display_field_name"])
            self.main_grid.SetCellValue(row_counter, 0, self.display_unit(row_field))
        # populate the grid with the field values from the current file
        max_row = self.main_grid.GetNumberRows()
        max_col = self.main_grid.GetNumberCols()
        if selected_object_name in self.current_file:
            active_input_objects = self.current_file[selected_object_name]
            self.column_input_object_names = ['skip column zero', ]  # we never need the first element
            for column_counter, active_input_object_name in enumerate(active_input_objects, start=1):
                self.column_input_object_names.append(active_input_object_name)
                for row_counter, row_field in enumerate(self.row_fields):
                    if column_counter < max_col and row_counter < max_row:
                        display_value, unconverted_value = self.display_cell_value(row_counter,
                                                                                   active_input_object_name,
                                                                                   active_input_objects)
                        self.main_grid.SetCellValue(row_counter, column_counter, display_value)
                        if not self.is_value_valid(row_counter, unconverted_value):
                            self.main_grid.SetCellBackgroundColour(row_counter, column_counter, "tan")
        # self.main_grid.AutoSizeColumns()
        self.resize_auto_plus_all_columns()
        self.main_grid.SetRowLabelSize(300)
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
            repeat_extension_fields = self.maximum_repeats_of_extensible_fields(object_name, last_field_name)
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
                unit_string = self.unit_conversions[input_field["units"]]["ip_unit"]
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
            extensible_field_list = active_input_objects[active_input_object_name][
                row_field["extensible_root_field_name"]]
            extensible_field = extensible_field_list[row_field["extensible_repeat_group"]]
            cell_value = extensible_field[row_field["field_name"]]
        cell_value_string = str(self.convert_unit_using_row_index(cell_value, row_index))
        return cell_value_string, cell_value

    def is_value_valid(self, row_index, value):
        row_field = self.row_fields[row_index]
        if row_field['type'] == 'number':
            numeric_value = float(value)
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
            if value not in row_field['enum']:
                return False
        return True

    def convert_unit_using_row_index(self, value_to_convert, row_index):
        row_field = self.row_fields[row_index]
        converted_value = value_to_convert  # return value is input unless converted
        if self.use_si_units:
            return converted_value
        if type(value_to_convert) is float or type(value_to_convert) is int:
            if "type" in row_field:
                if row_field["type"] == "number":
                    if "units" in row_field and not self.use_si_units:
                        if "ip_unit" in row_field:
                            unit_lookup = row_field["units"] + "___" + row_field["ip_unit"]
                        else:
                            unit_lookup = row_field["units"]
                        converted_value = self.convert_using_unit_string(value_to_convert, unit_lookup)
        return converted_value

    def convert_using_unit_string(self, value_to_convert, unit_string):
        converted_value = value_to_convert * self.unit_conversions[unit_string]["multiplier"]
        if "offset" in self.unit_conversions[unit_string]:
            converted_value = converted_value + self.unit_conversions[unit_string]["offset"]
        return converted_value

    def handle_cell_left_click(self, event):
        cell_row = event.GetRow()
        cell_column = event.GetCol()
        active_field = self.row_fields[cell_row]
        object_name = self.main_grid.GetCellValue(0, cell_column)
        print(f"left click ({cell_row}, {event.GetCol()}) for field {active_field['display_field_name']} "
              f"for object {object_name}")
        self.display_explanation(self.selected_object_name, row_number=cell_row)
        self.set_cell_choices(cell_row, cell_column)
        event.Skip()

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
        self.main_grid.SetCellValue(cell_row, cell_column, changed_string)
        if self.is_value_valid(cell_row, changed_string):
            self.main_grid.SetCellBackgroundColour(cell_row, cell_column, "white")
        else:
            self.main_grid.SetCellBackgroundColour(cell_row, cell_column, "tan")

    def set_file_value(self, cell_row, cell_column, new_cell_value):
        active_input_objects = self.current_file[self.selected_object_name]
        current_input_object_name = self.column_input_object_names[cell_column]
        active_input_object = active_input_objects[current_input_object_name]
        row_field = self.row_fields[cell_row]
        # set the value in the json data structure
        if row_field['field_name'] == 'name':
            active_input_objects[new_cell_value] = active_input_objects.pop(current_input_object_name)
            self.column_input_object_names[cell_column] = new_cell_value
        elif "extensible_root_field_name" in row_field:
            extensible_field_list = active_input_objects[current_input_object_name][
                row_field["extensible_root_field_name"]]
            extensible_field = extensible_field_list[row_field["extensible_repeat_group"]]
            extensible_field[row_field["field_name"]] = new_cell_value
        else:
            active_input_object[row_field['field_name']] = new_cell_value

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
                choices.append(option + " | choice")
        if 'object_list' in row_field:
            for reference_list_name in row_field['object_list']:
                if reference_list_name in self.reference_names:
                    for referenced_name in self.reference_names[reference_list_name]:
                        choices.append(referenced_name + " | object")
        if 'default' in row_field:
            choices.append(str(self.convert_unit_using_row_index(row_field['default'], cell_row)) + " | default")
        if 'minimum' in row_field:
            choices.append(str(self.convert_unit_using_row_index(row_field['minimum'], cell_row)) + " | minimum")
        if 'maximum' in row_field:
            choices.append(str(self.convert_unit_using_row_index(row_field['maximum'], cell_row)) + " | maximum")
        self.main_grid.SetCellEditor(cell_row, cell_column,
                                     wx.grid.GridCellChoiceEditor(choices, allowOthers=True))

    def maximum_repeats_of_extensible_fields(self, selected_object_name, field_name):
        max_repeat = 0
        if selected_object_name in self.current_file:
            active_input_objects = self.current_file[selected_object_name]
            for active_input_object in active_input_objects.keys():
                max_repeat = max(max_repeat, len(active_input_objects[active_input_object][field_name]))
        return max_repeat

    def create_data_dictionary(self):
        """
         Create the simplified version of the Energy+.schema.epJSON that
         is closer to what is needed for displaying the grid elements
        """
        with open("c:/EnergyPlusV9-4-0/Energy+.schema.epJSON") as schema_file:
            epschema = json.load(schema_file)
            for object_name, json_properties in epschema["properties"].items():
                self.data_dictionary[object_name] = SchemaInputObject(json_properties)
            references_from_data_dictionary = ReferencesFromDataDictionary(self.data_dictionary)
            self.cross_references = references_from_data_dictionary.reference_fields

    def read_unit_conversions(self):
        """
         Read the unit conversion file as a dictionary
        """
        with open("./support/unit_conversions.json") as unit_conversion_file:
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


# class JumpAndSearchPanel(wx.Panel):
#