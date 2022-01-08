# -*- coding: utf-8 -*-
#dialogs base class
#Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>

import wx
import _winxptheme

import constants
import globalVars
import views.ViewCreator

from logging import getLogger


class BaseDialog(object):
	"""モーダルダイアログの基本クラス。"""
	def __init__(self,identifier):
		self.identifier=identifier
		self.log=getLogger("%s.%s" % (constants.LOG_PREFIX,self.identifier))
		self.app=globalVars.app
		self.value=None
		self.viewMode=views.ViewCreator.ViewCreator.config2modeValue(
			globalVars.app.config.getstring("view","colorMode","white",("white","dark")),
			globalVars.app.config.getstring("view","textWrapping","off",("on","off"))
		)

	def Initialize(self, parent,ttl,style=wx.CAPTION | wx.SYSTEM_MENU | wx.BORDER_DEFAULT):
		"""タイトルを指定して、ウィンドウを初期化し、親の中央に配置するように設定。"""
		self.wnd=wx.Dialog(parent,-1, ttl,style = style)
		_winxptheme.SetWindowTheme(self.wnd.GetHandle(),"","")
		self.wnd.SetEscapeId(wx.ID_NONE)
		self.wnd.Bind(wx.EVT_CLOSE,self.OnClose)

		self.panel = wx.Panel(self.wnd,wx.ID_ANY)
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.panel.SetSizer(self.sizer)

	#ウィンドウを中央に配置してモーダル表示する
	#ウィンドウ内の部品を全て描画してから呼び出す
	def Show(self, modal=True):
		self.panel.Layout()
		self.sizer.Fit(self.wnd)
		self.wnd.Centre()
		if modal:
			result=self.wnd.ShowModal()
			if result!=wx.ID_CANCEL:
				self.value=self.GetData()
			self.Destroy()
		else:
			result=self.wnd.Show()
		self.log.debug("show(modal=%s) result=%s" % (str(modal),str(result)))
		return result

	def Destroy(self):
		self.log.debug("destroy")
		self.wnd.Destroy()

	def GetValue(self):
		self.log.debug("Value:%s" % str(self.value))
		return self.value

	def GetData(self):
		return None

	#closeイベントで呼ばれる。Alt+F4対策
	def OnClose(self,event):
		if self.wnd.GetWindowStyleFlag() & wx.CLOSE_BOX==wx.CLOSE_BOX:
			event.Skip()
		else:
			event.Veto()
