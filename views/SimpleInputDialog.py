# -*- coding: utf-8 -*-
# Simple input dialog view
# Copyright (C) 2019-2020 yamahubuki <itiro.ishino@gmail.com>
# Note: All comments except these top lines will be written in Japanese. 

import wx
import views.ViewCreator
from logging import getLogger
from views.baseDialog import *

class Dialog(BaseDialog):
	def __init__(self,title,detail,parent=None):
		super().__init__("SimpleInputDialog")
		self.title=title
		self.detail=detail
		if parent!=None:
			self.parent=parent
		else:
			self.parent=self.app.hMainView.hFrame

	def Initialize(self):
		self.log.debug("created")
		super().Initialize(self.parent,self.title)
		self.InstallControls()
		self.log.debug("Finished creating view - %s" % self.title)
		return True

	def InstallControls(self):
		"""いろんなwidgetを設置する。"""
		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.VERTICAL,20,style=wx.ALL,margin=20)
		self.edit,self.static=self.creator.inputbox(self.detail,x=-1,style=wx.BORDER_RAISED|wx.TE_DONTWRAP,sizerFlag=wx.EXPAND)
		self.edit.hideScrollBar(wx.HORIZONTAL)

		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.HORIZONTAL,20,style=wx.ALIGN_RIGHT)
		self.bOk=self.creator.okbutton(_("ＯＫ"),None)
		self.bCancel=self.creator.cancelbutton(_("キャンセル"),None)

	def GetData(self):
		return self.edit.GetLineText(0)
