# -*- coding: utf-8 -*-
# URL入力

import wx
import globalVars
import views.ViewCreator
from logging import getLogger
from views.baseDialog import *

class Dialog(BaseDialog):
	def __init__(self):
		super().__init__("urlEditDialog")

	def Initialize(self):
		self.log.debug("created")
		super().Initialize(self.app.hMainView.hFrame,_("URLを入力"))
		self.InstallControls()
		return True


	def InstallControls(self):
		"""いろんなwidgetを設置する。"""
		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.VERTICAL,20,style=wx.ALL,margin=20)
		self.edit, self.static = self.creator.inputbox("URL")
		self.okButton = self.creator.okbutton("OK")
		self.cancelButton = self.creator.cancelbutton(_("キャンセル"))

	def getData(self):
		return self.edit.GetValue()
