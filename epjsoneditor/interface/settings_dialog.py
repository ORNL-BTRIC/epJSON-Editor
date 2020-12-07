import wx


class SettingsDialog(wx.Dialog):

    CLOSE_SIGNAL_OK = 0
    CLOSE_SIGNAL_CANCEL = 1

    use_si_units = None

    def __init__(self, *args, **kwargs):
        super(SettingsDialog, self).__init__(*args, **kwargs)
        self.initialize_ui()
        self.SetSize((300, 250))
        self.SetTitle("Settings")

    def initialize_ui(self):
        vbox = wx.BoxSizer(wx.VERTICAL)

        unit_options = ["SI/metric", "Inch-Pound"]
        self.units_radio_box = wx.RadioBox(self, -1, "Unit System", wx.DefaultPosition, wx.DefaultSize, unit_options, 1, wx.RA_SPECIFY_COLS)
        self.units_radio_box.SetSelection(0)
        self.Bind(wx.EVT_RADIOBOX, self.handle_unit_option_event, self.units_radio_box)

        hbox_ok_cancel = wx.BoxSizer(wx.HORIZONTAL)
        ok_button = wx.Button(self, wx.ID_OK, label='Ok')
        ok_button.Bind(wx.EVT_BUTTON, self.handle_close_ok)
        self.SetAffirmativeId(ok_button.GetId())

        cancel_button = wx.Button(self, wx.ID_CANCEL, label='Cancel')
        cancel_button.Bind(wx.EVT_BUTTON, self.handle_close_cancel)

        hbox_ok_cancel.Add(ok_button, flag=wx.RIGHT, border=5)
        hbox_ok_cancel.Add(cancel_button, flag=wx.LEFT, border=5)

        vbox.Add(self.units_radio_box, flag=wx.ALIGN_TOP | wx.ALL, border=10)
        vbox.Add(hbox_ok_cancel, flag=wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, border=10)

        self.SetSizer(vbox)
        self.Show(True)

    def set_settings(self, use_si_units):
        self.use_si_units = use_si_units
        if self.use_si_units:
            self.units_radio_box.SetSelection(0)
        else:
            self.units_radio_box.SetSelection(1)

    def handle_unit_option_event(self, event):
        print(self.units_radio_box.GetStringSelection())
        self.use_si_units = event.GetInt() == 0
        print(self.use_si_units)

    def handle_close_ok(self, e):
        # Do some saving here before closing it
        self.EndModal(e.EventObject.Id)
        self.use_si_units = self.units_radio_box.GetSelection() == 0

    def handle_close_cancel(self, e):
        self.EndModal(SettingsDialog.CLOSE_SIGNAL_CANCEL)
