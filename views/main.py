# -*- coding: utf-8 -*-
#main view
#Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>
#Copyright (C) 2019-2020 yamahubuki <itiro.ishino@gmail.com>

import os
import sys
import wx
import datetime
import win32com

import constants
import errorCodes
import globalVars
import menuItemsStore

from .base import *
from recorder import getRecordingUsers
from simpleDialog import *

from views import SimpleInputDialog
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
		# 履歴表示用リストを作成
		self.logList, self.logStatic = self.creator.listCtrl(_("動作履歴"), style=wx.LC_REPORT)
		self.logList.AppendColumn(_("日時"))
		self.logList.AppendColumn(_("タイトル"))
		self.logList.AppendColumn(_("詳細"))
		self.logList.AppendColumn(_("サービス"))
		# 状況表示のリスト
		self.statusList, self.statusStatic = self.creator.listCtrl(_("動作状況"), style=wx.LC_REPORT)
		self.statusList.AppendColumn(_("サービス"))
		self.statusList.AppendColumn(_("状態"))
		# 「準備完了」を表示
		self.addLog(_("準備完了"), _("%sを起動しました。") %constants.APP_NAME)

	def addLog(self, title, detail, source=""):
		"""状況表示用リストに項目を追加

		:param title: 「配信通知」など、通知のタイトル
		:type title: str
		:param detail: 「○○さんが配信を開始しました」など
		:type detail: str
		:param source: 「ツイキャス」など
		:type source: str
		"""
		timestamp = datetime.datetime.now()
		timestamp = timestamp.strftime("%Y/%m/%d %H:%M:%S")
		self.logList.Append([
			timestamp,
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
				"HIDE",
				"EXIT",
		])

		# サービスメニューの中身
		self.RegisterMenuCommand(self.hServicesMenu, "TC_SUB", subMenu=self.hTwitcastingMenu)
		# ツイキャスメニューの中身
		self.RegisterCheckMenuCommand(self.hTwitcastingMenu, "TC_ENABLE")
		self.RegisterCheckMenuCommand(self.hTwitcastingMenu, "TC_SAVE_COMMENTS")
		self.RegisterMenuCommand(self.hTwitcastingMenu, [
			"TC_RECORD_ARCHIVE",
			"TC_UPDATE_USER",
			"TC_RECORD_USER",
			"TC_REMOVE_TOKEN",
			"TC_SET_TOKEN",
			"TC_MANAGE_USER",
		])

		# オプションメニュー
		self.RegisterMenuCommand(self.hOptionMenu, [
			"OP_SETTINGS",
			"OP_STARTUP",
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

		# ウィンドウを隠す
		if selected == menuItemsStore.getRef("HIDE"):
			self.hide()
		
		# ウィンドウを表示
		if selected == menuItemsStore.getRef("SHOW"):
			self.show()

		# 終了
		if selected == menuItemsStore.getRef("EXIT"):
			self.exitWithConfirmation()

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

		# ツイキャス：コメント保存
		if selected == menuItemsStore.getRef("TC_SAVE_COMMENTS"):
			globalVars.app.config["twitcasting"]["savecomments"] = event.IsChecked()

		# ツイキャス：ユーザ情報を更新
		if selected == menuItemsStore.getRef("TC_UPDATE_USER"):
			globalVars.app.tc.updateUser()

		# ツイキャス：過去ライブの録画
		if selected == menuItemsStore.getRef("TC_RECORD_ARCHIVE"):
			d = SimpleInputDialog.Dialog(_("URLを入力"), _("再生ページのURL"))
			d.Initialize()
			if d.Show() == wx.ID_CANCEL: return
			globalVars.app.tc.downloadArchive(d.GetData())

		# ツイキャス：ユーザ名を指定して録画
		if selected == menuItemsStore.getRef("TC_RECORD_USER"):
			d = SimpleInputDialog.Dialog(_("ユーザ名を入力"), _("ユーザ名"))
			d.Initialize()
			if d.Show() == wx.ID_CANCEL: return
			globalVars.app.tc.record(d.GetData())

		# ツイキャス：トークンを削除
		if selected == menuItemsStore.getRef("TC_REMOVE_TOKEN"):
			if not os.path.exists(constants.AC_TWITCASTING):
				errorDialog(_("すでに削除されています。"))
				return
			d = yesNoDialog(_("アクセストークンの削除"), _("ツイキャス連携機能を無効化し、アクセストークンを削除します。よろしいですか？"))
			if d == wx.ID_NO:
				return
			if globalVars.app.tc.running:
				globalVars.app.tc.exit()
			os.remove(constants.AC_TWITCASTING)
			dialog(_("完了"), _("アクセストークンを削除しました。"))

		# ツイキャス：トークンを再設定
		if selected == menuItemsStore.getRef("TC_SET_TOKEN"):
			globalVars.app.tc.setToken()

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

		# スタートアップに登録
		if selected == menuItemsStore.getRef("OP_STARTUP"):
			self.registerStartup()

		# 更新の確認
		if selected == menuItemsStore.getRef("HELP_UPDATE"):
			globalVars.update.update()

		# バージョン情報
		if selected==menuItemsStore.getRef("HELP_VERSIONINFO"):
			d = versionDialog.dialog()
			d.Initialize()
			r = d.Show()

	def Exit(self, event):
		if event.CanVeto():
			# Alt+F4が押された
			if globalVars.app.config.getboolean("general", "minimizeOnExit", True):
				self.hide()
			else:
				super().Exit(event)
				globalVars.app.tb.Destroy()
		else:
			super().Exit(event)
			globalVars.app.tb.Destroy()

	def hide(self):
		self.parent.hFrame.Hide()

	def show(self):
		self.parent.hFrame.Show()

	def exitWithConfirmation(self):
		if getRecordingUsers() != []:
			d = yesNoDialog(_("確認"), _("録画処理を実行中です。このまま終了すると、録画は中断されます。終了してもよろしいですか？"))
			if d == wx.ID_NO:
				return
		self.parent.hFrame.Close(True)

	def registerStartup(self):
		target = os.path.join(
			os.environ["appdata"],
			"Microsoft",
			"Windows",
			"Start Menu",
			"Programs",
			"Startup",
			"%s.lnk" %constants.APP_NAME
		)
		if os.path.exists(target):
			d = yesNoDialog(_("確認"), _("Windows起動時の自動起動はすでに設定されています。設定を解除しますか？"))
			if d == wx.ID_YES:
				os.remove(target)
				dialog(_("完了"), _("Windows起動時の自動起動を無効化しました。"))
			return
		ws = win32com.client.Dispatch("wscript.shell")
		shortCut = ws.CreateShortcut(target)
		shortCut.TargetPath = globalVars.app.getAppPath()
		shortCut.Save()
		dialog(_("完了"), _("Windows起動時の自動起動を設定しました。"))
