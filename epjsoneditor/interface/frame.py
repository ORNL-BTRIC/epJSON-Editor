import wx
import wx.lib.agw.aui as aui
import os
import json

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
        self._mgr.AddPane(text4, aui.AuiPaneInfo().CenterPane())
        self._mgr.AddPane(self.explanation_text, aui.AuiPaneInfo().Top().Caption("Explanation"))
        self._mgr.AddPane(text3, aui.AuiPaneInfo().Bottom().Caption("Search"))
        # Layer(2) allows it to take all of left side
        self._mgr.AddPane(self.object_list_tree, aui.AuiPaneInfo().Left().Layer(2).Caption("List of Input Objects"))

        # tell the manager to "commit" all the changes just made
        self._mgr.Update()

        self.Bind(wx.EVT_CLOSE, self.OnClose)
        self.Bind(wx.EVT_TREE_SEL_CHANGED, self.select_object_list_item, self.object_list_tree)

    def OnClose(self, event):
        # deinitialize the frame manager
        self._mgr.UnInit()
        event.Skip()

    def select_object_list_item(self, event):
        selected_object_name = self.object_list_tree.GetItemText(event.GetItem())
        explanation = selected_object_name + os.linesep + os.linesep \
                      + self.data_dictionary[selected_object_name].memo
        self.explanation_text.Value = explanation

    def create_data_dictionary(self):
        """
         Create the simplified version of the Energy+.schema.epJSON that
         is closer to what is needed for displaying the grid elements
        """
        with open("c:/EnergyPlusV9-4-0/Energy+.schema.epJSON") as schema_file:
            epschema = json.load(schema_file)
            for object_name, json_properties in epschema["properties"].items():
                self.data_dictionary[object_name] = SchemaInputObject(json_properties)
