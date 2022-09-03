# -*- coding: utf-8 -*-
# Simple input dialog view
# Copyright (C) 2019-2020 yamahubuki <itiro.ishino@gmail.com>
# Note: All comments except these top lines will be written in Japanese. 

import re
import wx

import views.ViewCreator

from logging import getLogger
from views.baseDialog import *

DEFAULT_STYLE=wx.BORDER_RAISED|wx.TE_DONTWRAP

class Dialog(BaseDialog):
	def __init__(self,title,detail,parent=None,validationPattern=None,defaultValue="",style=0):
		super().__init__("SimpleInputDialog")
		self.title=title
		self.detail=detail
		self.default=defaultValue
		if parent!=None:
			self.parent=parent
		else:
			self.parent=self.app.hMainView.hFrame
		self.validationPattern = validationPattern
		self.style=style

	def Initialize(self):
		super().Initialize(self.parent,self.title)
		self.InstallControls()
		return True

	def InstallControls(self):
		"""いろんなwidgetを設置する。"""
		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.VERTICAL,20,style=wx.ALL|wx.EXPAND,margin=20)
		self.edit,self.static=self.creator.inputbox(self.detail,defaultValue=self.default,x=-1,style=DEFAULT_STYLE|self.style,sizerFlag=wx.EXPAND)
		self.edit.hideScrollBar(wx.HORIZONTAL)

		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.HORIZONTAL,20,style=wx.ALIGN_RIGHT)
		self.bOk=self.creator.okbutton(_("ＯＫ"),self.ok)
		self.bCancel=self.creator.cancelbutton(_("キャンセル"),None)

	def ok(self,event):
		if self.validationPattern:
			if not re.fullmatch(self.validationPattern,self.edit.GetLineText(0)):
				return
		event.Skip()

	def GetData(self):
		return self.edit.GetLineText(0)
