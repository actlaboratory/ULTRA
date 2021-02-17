# -*- coding: utf-8 -*-
#View Creator
#Copyright (C) 2019-2020 yamahubuki <itiro.ishino@gmail.com>
#Copyright (C) 2019-2020 Hiroki Fujii <hfujii@hisystron.com>

import wx
import win32api
import _winxptheme

from views import ViewCreatorBase
from views.ViewCreatorBase import *

class ViewCreator(ViewCreatorBase):
	def __init__(self, *pArg, **kArg):
		"""
		ViewCreator

		:param str mode: Set view mode.
		:param wx.Window parent: Set parent window.
		:param wx.Sizer parentSizer: Set parent sizer. Default is None.
		:param flag orient: Set Set widget layout. Default is wx.HORIZONTAL.
		:param int space: Set gap between items. Default is 0.
		:param str/int label: Set item label(str) or grid sizer's column count(int).
		:param flags style: Set sizer flags.
		:param int proportion: Set proportion.
		:param int margin: Set viewCreator's margin.
		"""
		

		super().__init__(*pArg, **kArg)

		# 標準オブジェクトの変更が必要ならば記述
		# self.winObject["object_name"] = newObject
