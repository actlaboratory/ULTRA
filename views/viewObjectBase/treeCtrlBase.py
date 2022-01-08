#treeCtrlBase for ViewCreator
#Copyright (C) 2019-2020 Hiroki Fujii <hfujii@hisystron.com>
#Copyright (C) 2021 yamahubuki <itiro.ishino@gmail.com>

import globalVars
import json
import wx
from views.viewObjectBase import viewObjectUtil, controlBase,listCtrlBase

class treeCtrl(controlBase.controlBase, wx.TreeCtrl):
	def __init__(self, *pArg, **kArg):
		self.focusFromKbd = viewObjectUtil.popArg(kArg, "enableTabFocus", True) #キーボードフォーカスの初期値
		return super().__init__(*pArg, **kArg)
