import wx
import wx.grid
import wx.lib.agw.aui as aui
import os
import json

from wx import Panel

from epjsoneditor.schemainputobject import SchemaInputObject


class EpJsonEditorFrame(wx.Frame):

    def __init__(self, parent, id=-1, title="epJSON Editor - ", pos=wx.DefaultPosition,
                 size=(1200, 800), style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)

        self._mgr = aui.AuiManager()

        self.data_dictionary = {}
        self.create_data_dictionary()

        self.object_list_tree = None
        self.object_list_root = None
        self.input_grid = None
        self.current_file  = {}
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

        text3 = wx.TextCtrl(self, -1, "Pane 3 - sample text",
                            wx.DefaultPosition, wx.Size(200, 150),
                            wx.NO_BORDER | wx.TE_MULTILINE)

        text4 = wx.TextCtrl(self, -1, "Main content window",
                            wx.DefaultPosition, wx.Size(600, 650),
                            wx.NO_BORDER | wx.TE_MULTILINE)


        # add the panes to the manager
        self._mgr.AddPane(text4, aui.AuiPaneInfo().CenterPane().Name("text_content"))
        self._mgr.AddPane(self.explanation_text, aui.AuiPaneInfo().Top().Caption("Explanation"))

        self.main_grid = self.create_grid()
        self._mgr.AddPane(self.main_grid, aui.AuiPaneInfo().Name("grid_content").
                          CenterPane().Hide().MinimizeButton(True))

        self._mgr.AddPane(text3, aui.AuiPaneInfo().Bottom().Caption("Search"))
        # Layer(2) allows it to take all of left side
        self._mgr.AddPane(self.object_list_tree, aui.AuiPaneInfo().Left().Layer(2).Caption("List of Input Objects"))

        # tell the manager to "commit" all the changes just made
        self._mgr.Update()

        # it works better to have TextCntrl for CenterPane shown and hidden and the grid being hidden then shown
        self._mgr.GetPane("grid_content").Show(True)
        self._mgr.GetPane("text_content").Show(False)
        self._mgr.Update()

        self.create_toolbar()

        self.Bind(wx.EVT_CLOSE, self.OnClose)
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

        tb1.AddSimpleTool(12, "Save", wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE))
        tb1.AddSimpleTool(13, "Save As", wx.ArtProvider.GetBitmap(wx.ART_FILE_SAVE_AS))
        tb1.AddSeparator()
        tb1.AddSimpleTool(14, "Undo", wx.ArtProvider.GetBitmap(wx.ART_UNDO))
        tb1.AddSimpleTool(15, "Redo", wx.ArtProvider.GetBitmap(wx.ART_REDO))
        tb1.AddSeparator()
        tb1.AddSimpleTool(16, "New Obj", wx.ArtProvider.GetBitmap(wx.ART_PLUS))
        tb1.AddSimpleTool(17, "Dup Obj", wx.ArtProvider.GetBitmap(wx.ART_GO_FORWARD)) # duplicate
        tb1.AddSimpleTool(18, "Dup Obj + Chg", wx.ArtProvider.GetBitmap(wx.ART_GOTO_LAST)) # duplicate and change
        tb1.AddSimpleTool(19, "Del Obj", wx.ArtProvider.GetBitmap(wx.ART_MINUS))
        tb1.AddSimpleTool(20, "Copy Obj", wx.ArtProvider.GetBitmap(wx.ART_COPY))
        tb1.AddSimpleTool(21, "Paste Obj", wx.ArtProvider.GetBitmap(wx.ART_PASTE))
        tb1.AddSeparator()
        tb1.AddTool(22, "IP Units", wx.ArtProvider.GetBitmap(wx.ART_GO_UP), wx.NullBitmap, kind=wx.ITEM_RADIO)

        tb1.AddTool(23, "SI Units", wx.ArtProvider.GetBitmap(wx.ART_GO_DOWN), wx.NullBitmap, kind=wx.ITEM_RADIO)
        tb1.AddSeparator()
        tb1.AddSimpleTool(25, "Settings", wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE))
        tb1.AddSimpleTool(26, "Help", wx.ArtProvider.GetBitmap(wx.ART_HELP))
        tb1.Realize()
        self._mgr.AddPane(tb1, aui.AuiPaneInfo().Name("tb1").Caption("Primary Toolbar").
                          ToolbarPane().Top())
        self._mgr.Update()

    def handle_open_file(self, event):
        with wx.FileDialog(self, "Open EnergyPlus epJSON file", wildcard="epJSON files (*.epJSON)|*.epJSON",
                           style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as fileDialog:
            if fileDialog.ShowModal() == wx.ID_CANCEL:
                return     # the user changed their mind
            path_name = fileDialog.GetPath()
            try:
               self.load_current_file(path_name)
            except IOError:
                wx.LogError(f"Cannot open file {path_name}")

    def load_current_file(self, path_name):
        if os.path.exists(path_name):
            self.current_file_path = path_name
            self.SetTitle(f"epJSON Editor - {path_name}")
            with open(path_name) as input_file:
                self.current_file = json.load(input_file)
            self.Refresh()

    def OnClose(self, event):
        # deinitialize the frame manager
        self._mgr.UnInit()
        event.Skip()

    def select_object_list_item(self, event):
        selected_object_name = self.object_list_tree.GetItemText(event.GetItem())
        explanation = selected_object_name + os.linesep + os.linesep \
                      + self.data_dictionary[selected_object_name].memo
        self.explanation_text.Value = explanation
        self.update_grid(selected_object_name)

    def update_grid(self, selected_object_name):
        self.main_grid.FreezeTo(0,1)
        self.main_grid.SetCornerLabelValue("Field")
        self.main_grid.SetColLabelValue(0,"Units")
        self.main_grid.SetColLabelValue(1,"Obj1")
        print(selected_object_name)
        selected_object_dict = self.data_dictionary[selected_object_name]
        input_fields = selected_object_dict.input_fields
        input_fields_keys = list(input_fields.keys())
        extension_fields = {}
        extension_field_keys = []
        if selected_object_dict.extensible_size > 0:
            last_input_field = input_fields_keys[-1]
            extension_fields = input_fields[last_input_field]
            extension_field_keys = list(extension_fields.keys())
            input_fields_keys.pop() # remove last item
        # resize the number of rows if necessary
        repeat_extension_fields = 4
        current_rows = self.main_grid.GetNumberRows()
        new_rows = len(input_fields) + len(extension_fields) * repeat_extension_fields
        if new_rows < current_rows:
            self.main_grid.DeleteRows(0, current_rows - new_rows, True)
        if new_rows > current_rows:
            self.main_grid.AppendRows(new_rows - current_rows)
        #resize the number of columns to be the number of input objects
        current_columns = self.main_grid.GetNumberCols()
        if selected_object_name in self.current_file:
            new_columns = len(self.current_file[selected_object_name]) + 1
        else:
            new_columns = 2
        if new_columns < current_columns:
            self.main_grid.DeleteCols(0, current_columns - new_columns, True)
        if new_columns > current_columns:
            self.main_grid.AppendCols(new_columns - current_columns)

        for counter, input_field in enumerate(input_fields_keys):
            current_field = input_fields[input_field]
            if "field_name_with_spaces" in current_field:
                self.main_grid.SetRowLabelValue(counter, current_field["field_name_with_spaces"])
            else:
                self.main_grid.SetRowLabelValue(counter, input_field)
            self.main_grid.SetCellValue(counter, 0, "")
            if "units" in current_field:
                self.main_grid.SetCellValue(counter, 0, current_field["units"])
            #self.main_grid.SetCellBackgroundColour(counter, 0, wx.LIGHT_GREY)

        field_count = len(input_fields)
        for repeat in range(1, repeat_extension_fields + 1):
            for counter, extension_field in enumerate(extension_field_keys):
                current_field = extension_fields[extension_field]
                if "field_name_with_spaces" in current_field:
                    self.main_grid.SetRowLabelValue(counter + field_count, current_field["field_name_with_spaces"] + "-" + str(repeat).zfill(3))
                else:
                    self.main_grid.SetRowLabelValue(counter + field_count, extension_fields + "-" + str(repeat).zfill(3))
                self.main_grid.SetCellValue(counter + field_count, 0, "")
                if "units" in current_field:
                    self.main_grid.SetCellValue(counter + field_count, 0, current_field["units"])
                #self.main_grid.SetCellBackgroundColour(counter + field_count, 0, wx.LIGHT_GREY)
            field_count += len(extension_fields)

        max_row = self.main_grid.GetNumberRows()
        max_col = self.main_grid.GetNumberCols()
        if selected_object_name in self.current_file:
            active_input_objects = self.current_file[selected_object_name]
            for input_object_counter, active_input_object in enumerate(active_input_objects):
                for field_counter, input_field in enumerate(input_fields_keys):
                    if input_object_counter < max_col:
                        if field_counter < max_row:
                            if input_field == "name":
                                self.main_grid.SetCellValue(field_counter, input_object_counter + 1, active_input_object)
                            elif input_field in active_input_objects[active_input_object]:
                                self.main_grid.SetCellValue(field_counter, input_object_counter + 1, str(active_input_objects[active_input_object][input_field]))


        self.main_grid.SetRowLabelSize(300)
        self.main_grid.SetRowLabelAlignment(wx.ALIGN_LEFT,wx.ALIGN_TOP)

    def create_data_dictionary(self):
        """
         Create the simplified version of the Energy+.schema.epJSON that
         is closer to what is needed for displaying the grid elements
        """
        with open("c:/EnergyPlusV9-4-0/Energy+.schema.epJSON") as schema_file:
            epschema = json.load(schema_file)
            for object_name, json_properties in epschema["properties"].items():
                self.data_dictionary[object_name] = SchemaInputObject(json_properties)
