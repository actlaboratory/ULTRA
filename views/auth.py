# -*- coding: utf-8 -*-
# 認証関係のビュー

from views.baseDialog import BaseDialog
from logging import getLogger
import views.ViewCreator
import wx

class waitingDialog(BaseDialog):
	def __init__(self):
		self.canceled = 0
		super().__init__("waitingDialog")

	def Initialize(self, title):
		self.log.debug("created")
		super().Initialize(self.app.hMainView.hFrame,title)
		self.InstallControls()
		return True

	def InstallControls(self):
		"""いろんなwidgetを設置する。"""
		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.VERTICAL,20)
		self.staticText = self.creator.staticText(_("ブラウザでの操作を待っています..."))
		self.bCancel=self.creator.cancelbutton(_("キャンセル"), self.onCancelBtn)

	def onCancelBtn(self, event):
		self.canceled = 1
		event.Skip()
