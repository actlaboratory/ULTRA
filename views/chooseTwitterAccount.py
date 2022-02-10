# -*- coding: utf-8 -*-
# choose account dialog

import wx
import globalVars
import views.ViewCreator
from logging import getLogger
from views.baseDialog import *


class Dialog(BaseDialog):
	def __init__(self, tokenManager):
		super().__init__("chooseTwitterAccountDialog")
		self.tokenManager = tokenManager
		self.data = {}
		data = tokenManager.getData()
		for i in data:
			self.data[data[i]["user"]["username"]] = i

	def Initialize(self):
		self.log.debug("created")
		super().Initialize(self.app.hMainView.hFrame, _("Twitterアカウントを選択"))
		self.InstallControls()
		return True

	def InstallControls(self):
		"""いろんなwidgetを設置する。"""
		self.creator = views.ViewCreator.ViewCreator(self.viewMode, self.panel, self.sizer, wx.VERTICAL, 20, style=wx.ALL | wx.EXPAND, margin=20)
		self.combobox, tmp = self.creator.combobox(_("アカウント"), list(self.data.keys()), state=0)
		self.creator = views.ViewCreator.ViewCreator(self.viewMode, self.panel, self.sizer, wx.HORIZONTAL, 20, "", wx.ALIGN_RIGHT | wx.ALL, margin=20)
		self.bOk = self.creator.okbutton(_("ＯＫ"))
		self.bCancel = self.creator.cancelbutton(_("キャンセル"), None)

	def GetData(self):
		return self.data[self.combobox.GetValue()]
