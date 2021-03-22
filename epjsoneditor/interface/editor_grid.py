import wx.grid as gridlib
import wx.lib.mixins.grid as mixins


class EditorGrid(gridlib.Grid, mixins.GridAutoEditMixin):

    def __init__(self, parent):
        gridlib.Grid.__init__(self, parent, -1)
        # , wx.Point(0, 0), wx.Size(150, 250),
        #                wx.NO_BORDER | wx.WANTS_CHARS)
        mixins.GridAutoEditMixin.__init__(self)
