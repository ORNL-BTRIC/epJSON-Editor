import wx.grid as grid_lib
import wx.lib.mixins.grid as mixins


class EditorGrid(grid_lib.Grid, mixins.GridAutoEditMixin):

    def __init__(self, parent):
        grid_lib.Grid.__init__(self, parent, -1)
        # , wx.Point(0, 0), wx.Size(150, 250),
        #                wx.NO_BORDER | wx.WANTS_CHARS)
        mixins.GridAutoEditMixin.__init__(self)
