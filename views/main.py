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
from views import settingsDialog
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
		# 状況表示用リストを作成
		self.listCtrl, self.static = self.creator.listCtrl(_("動作状況"), style=wx.LC_REPORT)
		self.listCtrl.AppendColumn(_("タイトル"))
		self.listCtrl.AppendColumn(_("詳細"))
		self.listCtrl.AppendColumn(_("ソース"))

	def addLog(self, title, detail, source=""):
		"""状況表示用リストに項目を追加

		:param title: 「配信通知」など、通知のタイトル
		:type title: str
		:param detail: 「○○さんが配信を開始しました」など
		:type detail: str
		:param source: 「ツイキャス」など
		:type source: str
		"""
		self.listCtrl.Append([
			title,
			detail,
			source
		])


class Menu(BaseMenu):
	def Apply(self,target):
		"""指定されたウィンドウに、メニューを適用する。"""

		#メニュー内容をいったんクリア
		self.hMenuBar=wx.MenuBar()

		#メニューの大項目を作る
		self.hFileMenu=wx.Menu()
		self.hServicesMenu = wx.Menu()
		self.hTwitcastingMenu=wx.Menu()
		self.hOptionMenu = wx.Menu()
		self.hHelpMenu=wx.Menu()

		#ファイルメニュー
		self.RegisterMenuCommand(self.hFileMenu,[
				"FILE_EXAMPLE", "HIDE", "EXIT",
		])

		# サービスメニューの中身
		self.RegisterMenuCommand(self.hServicesMenu, "TC_SUB", subMenu=self.hTwitcastingMenu)
		# ツイキャスメニューの中身
		self.RegisterCheckMenuCommand(self.hTwitcastingMenu, "TC_ENABLE")
		self.RegisterMenuCommand(self.hTwitcastingMenu, [
			"TC_RECORD_ARCHIVE", "TC_RECORD_USER", "TC_MANAGE_USER"
		])

		# オプションメニュー
		self.RegisterMenuCommand(self.hOptionMenu, [
			"OP_SETTINGS",
		])

		#ヘルプメニューの中身
		self.RegisterMenuCommand(self.hHelpMenu,[
				"HELP_UPDATE",
				"HELP_VERSIONINFO",
		])

		#メニューバーの生成
		self.hMenuBar.Append(self.hFileMenu,_("ファイル(&F)"))
		self.hMenuBar.Append(self.hServicesMenu, _("サービス(&S)"))
		self.hMenuBar.Append(self.hOptionMenu, _("オプション(&O)"))
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

		# ウィンドウを隠す
		if selected == menuItemsStore.getRef("HIDE"):
			self.hide()
		
		# ウィンドウを表示
		if selected == menuItemsStore.getRef("SHOW"):
			self.show()

		# 終了
		if selected == menuItemsStore.getRef("EXIT"):
			self.parent.hFrame.Close(True)
			globalVars.app.tb.Destroy()

		# ツイキャス連携の有効化
		if selected == menuItemsStore.getRef("TC_ENABLE"):
			if event.IsChecked():
				if not globalVars.app.tc.initialize():
					self.parent.menu.CheckMenu("TC_ENABLE", False)
					return
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

		# 設定
		if selected == menuItemsStore.getRef("OP_SETTINGS"):
			d = settingsDialog.Dialog()
			d.Initialize()
			d.Show()

		if selected == menuItemsStore.getRef("HELP_UPDATE"):
			globalVars.update.update()

		if selected==menuItemsStore.getRef("HELP_VERSIONINFO"):
			d = versionDialog.dialog()
			d.Initialize()
			r = d.Show()

	def Exit(self, event):
		if event.CanVeto():
			self.hide()
		else:
			super().Exit(event)

	def hide(self):
		self.parent.hFrame.Hide()

	def show(self):
		self.parent.hFrame.Show()
