# -*- coding: utf-8 -*-
#main view
#Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>
#Copyright (C) 2019-2020 yamahubuki <itiro.ishino@gmail.com>

import logging
import os
import sys
import wx
import re
import ctypes
import pywintypes

import constants
import errorCodes
import globalVars
import menuItemsStore

from .base import *
from simpleDialog import *

from views import mkDialog
from views import sample
from views import urlEdit
from views import userEdit
from views import tcManageUser
from views import versionDialog

class MainView(BaseView):
	def __init__(self):
		super().__init__("mainView")
		self.log.debug("created")
		self.app=globalVars.app
		self.events=Events(self,self.identifier)
		title=constants.APP_NAME
		super().Initialize(
			title,
			self.app.config.getint(self.identifier,"sizeX",800,400),
			self.app.config.getint(self.identifier,"sizeY",600,300),
			self.app.config.getint(self.identifier,"positionX",50,0),
			self.app.config.getint(self.identifier,"positionY",50,0)
		)
		self.InstallMenuEvent(Menu(self.identifier),self.events.OnMenuSelect)


class Menu(BaseMenu):
	def Apply(self,target):
		"""指定されたウィンドウに、メニューを適用する。"""

		#メニュー内容をいったんクリア
		self.hMenuBar=wx.MenuBar()

		#メニューの大項目を作る
		self.hFileMenu=wx.Menu()
		self.hTwitcastingMenu=wx.Menu()
		self.hHelpMenu=wx.Menu()

		#ファイルメニュー
		self.RegisterMenuCommand(self.hFileMenu,[
				"FILE_EXAMPLE",
		])

		# ツイキャスメニューの中身
		self.RegisterCheckMenuCommand(self.hTwitcastingMenu, "TC_ENABLE")
		self.RegisterMenuCommand(self.hTwitcastingMenu, [
			"TC_RECORD_ARCHIVE", "TC_RECORD_USER", "TC_MANAGE_USER"
		])

		#ヘルプメニューの中身
		self.RegisterMenuCommand(self.hHelpMenu,[
				"HELP_UPDATE",
				"HELP_VERSIONINFO",
		])

		#メニューバーの生成
		self.hMenuBar.Append(self.hFileMenu,_("ファイル(&F)"))
		self.hMenuBar.Append(self.hTwitcastingMenu, "&TwitCasting")
		self.hMenuBar.Append(self.hHelpMenu,_("ヘルプ(&H)"))
		target.SetMenuBar(self.hMenuBar)

class Events(BaseEvents):
	def OnMenuSelect(self,event):
		"""メニュー項目が選択されたときのイベントハンドら。"""
		#ショートカットキーが無効状態のときは何もしない
		if not self.parent.shortcutEnable:
			event.Skip()
			return

		selected=event.GetId()#メニュー識別しの数値が出る

		if selected==menuItemsStore.getRef("FILE_EXAMPLE"):
			d = sample.Dialog()
			d.Initialize()
			r = d.Show()

		# ツイキャス連携の有効化
		if selected == menuItemsStore.getRef("TC_ENABLE"):
			if event.IsChecked():
				if globalVars.app.tc.initialize():
					globalVars.app.tc.start()
			else:
				globalVars.app.tc.exit()
			globalVars.app.config["twitcasting"]["enable"] = event.IsChecked()

		# ツイキャス：過去ライブの録画
		if selected == menuItemsStore.getRef("TC_RECORD_ARCHIVE"):
			d = urlEdit.Dialog()
			d.Initialize()
			if d.Show() == wx.ID_CANCEL: return
			globalVars.app.tc.downloadArchive(d.getData())

		# ツイキャス：ユーザ名を指定して録画
		if selected == menuItemsStore.getRef("TC_RECORD_USER"):
			d = userEdit.Dialog()
			d.Initialize()
			if d.Show() == wx.ID_CANCEL: return
			globalVars.app.tc.record(d.getData())

		# ツイキャス：ユーザの管理
		if selected == menuItemsStore.getRef("TC_MANAGE_USER"):
			d = tcManageUser.Dialog()
			d.Initialize()
			if d.Show() == wx.ID_CANCEL:
				return
			globalVars.app.tc.users = d.GetValue()
			globalVars.app.tc.saveUserList()

		if selected == menuItemsStore.getRef("HELP_UPDATE"):
			globalVars.update.update()

		if selected==menuItemsStore.getRef("HELP_VERSIONINFO"):
			d = versionDialog.dialog()
			d.Initialize()
			r = d.Show()
