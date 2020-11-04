import wx

from epjsoneditor.interface.frame import EpJsonEditorFrame


class EpJsonEditorApplication(wx.App):

    def __init__(self, x):
        super(EpJsonEditorApplication, self).__init__(x)
        self.frame_epjsoneditor = None  # This is purely to get flake8 to hush about where the instantiation occurs

    def OnInit(self):
        self.frame_epjsoneditor = EpJsonEditorFrame(None)
        self.SetTopWindow(self.frame_epjsoneditor)
        self.frame_epjsoneditor.Show()
        return True


