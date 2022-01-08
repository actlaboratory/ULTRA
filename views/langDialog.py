# -*- coding: utf-8 -*-
# language select dialog

import wx
import globalVars
import views.ViewCreator
from logging import getLogger
from views.baseDialog import *
import constants

class langDialog(BaseDialog):
	def __init__(self):
		#まだglobalVars.appが未精製の状態での軌道の可能性があるのであえて呼ばない
		#super().__init__()
		self.lang_code = list(constants.SUPPORTING_LANGUAGE.keys())
		self.lang_name = list(constants.SUPPORTING_LANGUAGE.values())
		self.identifier="languageSelectDialog"
		self.log=getLogger("%s.%s" % (constants.LOG_PREFIX,self.identifier))
		self.value=None
		self.viewMode="white"

	def Initialize(self):
		self.log.debug("created")
		super().Initialize(None,"language settings")
		self.InstallControls()
		return True

	def InstallControls(self):
		"""いろんなwidgetを設置する。"""
		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.VERTICAL,20)
		#翻訳
		self.langSelect,static = self.creator.combobox("select language", self.lang_name, None, state=0)
		self.ok = self.creator.okbutton("OK", None)

	def Destroy(self, events = None):
		self.log.debug("destroy")
		self.wnd.Destroy()

	def GetData(self):
		select = self.langSelect.GetSelection()
		return self.lang_code[select]

