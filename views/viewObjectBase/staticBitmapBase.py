# staticBitmapBase for ViewCreator
#Copyright (C) 2023 yamahubuki <itiro.ishino@gmail.com>

import wx
from views.viewObjectBase import viewObjectUtil, controlBase

class staticBitmap(controlBase.controlBase, wx.StaticBitmap):
	def __init__(self, *pArg, **kArg):
		self.focusFromKbd = False
		return super().__init__(*pArg, **kArg)
