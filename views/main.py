# -*- coding: utf-8 -*-
#main view
#Copyright (C) 2019 Yukio Nozawa <personal@nyanchangames.com>
#Copyright (C) 2019-2020 yamahubuki <itiro.ishino@gmail.com>

import os
import sys
import wx
import datetime
import win32com

import ConfigManager
import constants
import errorCodes
import globalVars
import hotkeyHandler
import menuItemsStore
import update
from .base import *
from recorder import getRecordingUsers
from simpleDialog import *

from views import globalKeyConfig
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
		self.InstallMenuEvent(Menu(self.identifier, self.events),self.events.OnMenuSelect)
		self.applyHotKey()

		# 履歴表示用リストを作成
		self.logList, self.logStatic = self.creator.listCtrl(_("動作履歴"), style=wx.LC_REPORT,sizerFlag=wx.EXPAND,proportion=2)
		self.logList.AppendColumn(_("タイトル"),width=200)
		self.logList.AppendColumn(_("詳細"),width=400)
		self.logList.AppendColumn(_("サービス"),width=300)
		self.logList.AppendColumn(_("日時"),width=250)
		# 状況表示のリスト
		self.creator.AddSpace(10)
		self.statusList, self.statusStatic = self.creator.listCtrl(_("動作状況"), style=wx.LC_REPORT,sizerFlag=wx.EXPAND,proportion=1)
		self.statusList.AppendColumn(_("サービス"),width=300)
		self.statusList.AppendColumn(_("状態"),width=500)
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
		timestamp = timestamp.strftime("%m/%d %H:%M:%S")
		data = [
			title,
			detail,
			source,
			timestamp,
		]
		self.logList.Append(data)
		self.log.info("display: " + ",".join(data))

	def applyHotKey(self):
		self.hotkey = hotkeyHandler.HotkeyHandler(None,hotkeyHandler.HotkeyFilter().SetDefault())
		if self.hotkey.addFile(constants.KEYMAP_FILE_NAME,["HOTKEY"])==errorCodes.OK:
			errors=self.hotkey.GetError("HOTKEY")
			if errors:
				tmp=_(constants.KEYMAP_FILE_NAME+"で設定されたホットキーが正しくありません。キーの重複、存在しないキー名の指定、使用できないキーパターンの指定などが考えられます。以下のキーの設定内容をご確認ください。\n\n")
				for v in errors:
					tmp+=v+"\n"
				dialog(_("エラー"),tmp)
			self.hotkey.Set("HOTKEY",self.hFrame)

class Menu(BaseMenu):
	def __init__(self, identifier, event, *, keyFilter=None):
		self.event = event
		super().__init__(identifier, keyFilter=keyFilter)

	def Apply(self,target):
		"""指定されたウィンドウに、メニューを適用する。"""

		#メニュー内容をいったんクリア
		self.hMenuBar=wx.MenuBar()

		#メニューの大項目を作る
		self.hFileMenu=wx.Menu()
		self.hServicesMenu = wx.Menu()
		self.hServicesMenu.Bind(wx.EVT_MENU_OPEN, self.event.OnMenuOpen)
		self.hTwitcastingMenu=wx.Menu()
		self.hTwitcastingFiletypesMenu = wx.Menu()
		self.hYDLMenu=wx.Menu()
		self.hOptionMenu = wx.Menu()
		self.hHelpMenu=wx.Menu()

		#ファイルメニュー
		self.RegisterMenuCommand(self.hFileMenu,[
				"HIDE",
				"EXIT",
		])

		# サービスメニューの中身
		self.RegisterMenuCommand(self.hServicesMenu, "TC_SUB", subMenu=self.hTwitcastingMenu)
		self.RegisterMenuCommand(self.hServicesMenu, "YDL_SUB", subMenu=self.hYDLMenu)
		# ツイキャスメニューの中身
		self.RegisterCheckMenuCommand(self.hTwitcastingMenu, "TC_ENABLE")
		self.RegisterCheckMenuCommand(self.hTwitcastingMenu, "TC_SAVE_COMMENTS")
		self.RegisterCheckMenuCommand(self.hTwitcastingMenu, "TC_LOGIN_TOGGLE")
		self.RegisterMenuCommand(self.hTwitcastingMenu, [
			"TC_RECORD_ARCHIVE",
			"TC_RECORD_ALL",
			"TC_UPDATE_USER",
			"TC_ADD_MULTIPLE",
			"TC_RECORD_USER",
			"TC_REMOVE_SESSION",
			"TC_REMOVE_TOKEN",
			"TC_SET_TOKEN",
			"TC_MANAGE_USER",
		])
		self.RegisterMenuCommand(self.hTwitcastingMenu, "TC_FILETYPES", subMenu=self.hTwitcastingFiletypesMenu)
		# yt-dlpメニューの中身
		self.RegisterMenuCommand(self.hYDLMenu, [
			"YDL_DOWNLOAD",
		])

		# オプションメニュー
		self.RegisterMenuCommand(self.hOptionMenu, [
			"OP_SETTINGS",
			"OP_SHORTCUT",
			"OP_HOTKEY",
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
		# 「ウィンドウを隠す」を無効化
		self.EnableMenu("HIDE", False)

class Events(BaseEvents):
	def OnMenuOpen(self, event):
		menu = event.GetMenu()
		if menu == self.parent.menu.hTwitcastingFiletypesMenu:
			globalVars.app.tc.getFiletypesMenu(menu)

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
			if globalVars.app.config.write() != errorCodes.OK:
				errorDialog(_("設定の保存に失敗しました。下記のファイルへのアクセスが可能であることを確認してください。") + "\n" + os.path.abspath(constants.SETTING_FILE_NAME))

		# ツイキャス：コメント保存
		if selected == menuItemsStore.getRef("TC_SAVE_COMMENTS"):
			globalVars.app.config["twitcasting"]["savecomments"] = event.IsChecked()
			if globalVars.app.config.write() != errorCodes.OK:
				errorDialog(_("設定の保存に失敗しました。下記のファイルへのアクセスが可能であることを確認してください。") + "\n" + os.path.abspath(constants.SETTING_FILE_NAME))

		# ツイキャス：ユーザ情報を更新
		if selected == menuItemsStore.getRef("TC_UPDATE_USER"):
			globalVars.app.tc.updateUser()

		# ツイキャス：一括追加
		if selected == menuItemsStore.getRef("TC_ADD_MULTIPLE"):
			globalVars.app.tc.addMultipleUsers()

		# ツイキャス：過去ライブの録画
		if selected == menuItemsStore.getRef("TC_RECORD_ARCHIVE"):
			d = SimpleInputDialog.Dialog(_("URLを入力"), _("再生ページのURL"))
			d.Initialize()
			if d.Show() == wx.ID_CANCEL: return
			globalVars.app.tc.downloadArchive(d.GetData())

		# ツイキャス：一括録画
		if selected == menuItemsStore.getRef("TC_RECORD_ALL"):
			d = SimpleInputDialog.Dialog(_("ユーザ名を入力"), _("ユーザ名"))
			d.Initialize()
			if d.Show() == wx.ID_CANCEL: return
			globalVars.app.tc.recordAll(d.GetData())

		# ツイキャス：ユーザ名を指定して録画
		if selected == menuItemsStore.getRef("TC_RECORD_USER"):
			d = SimpleInputDialog.Dialog(_("ユーザ名を入力"), _("ユーザ名"))
			d.Initialize()
			if d.Show() == wx.ID_CANCEL: return
			globalVars.app.tc.record(d.GetData())

		# ツイキャス：ログインの切り替え
		if selected == menuItemsStore.getRef("TC_LOGIN_TOGGLE"):
			globalVars.app.tc.toggleLogin()

		# ツイキャス：セッションを削除
		if selected == menuItemsStore.getRef("TC_REMOVE_SESSION"):
			globalVars.app.tc.removeSession()

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
				self.parent.menu.CheckMenu("TC_ENABLE", False)
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

		# yt-dlp：URLを指定してダウンロード
		if selected == menuItemsStore.getRef("YDL_DOWNLOAD"):
			d = SimpleInputDialog.Dialog(_("URLを入力"), _("URLの指定"))
			d.Initialize()
			if d.Show() == wx.ID_CANCEL: return
			globalVars.app.ydl.download(d.GetData())

		# 設定
		if selected == menuItemsStore.getRef("OP_SETTINGS"):
			d = settingsDialog.Dialog()
			d.Initialize()
			d.Show()

		# キーボードショートカットの設定
		if selected == menuItemsStore.getRef("OP_SHORTCUT"):
			if self.setKeymap("MainView",_("ショートカットキーの設定"),filter=keymap.KeyFilter().SetDefault(False,False)):
				#ショートカットキーの変更適用とメニューバーの再描画
				self.parent.menu.InitShortcut()
				self.parent.menu.ApplyShortcut(self.parent.hFrame)
				self.parent.menu.Apply(self.parent.hFrame)

		# グローバルホットキーの設定
		if selected==menuItemsStore.getRef("OP_HOTKEY"):
			if self.setKeymap("HOTKEY",_("グローバルホットキーの設定"), self.parent.hotkey,filter=self.parent.hotkey.filter):
				#変更適用
				self.parent.hotkey.UnSet("HOTKEY",self.parent.hFrame)
				self.parent.applyHotKey()

		# スタートアップに登録
		if selected == menuItemsStore.getRef("OP_STARTUP"):
			self.registerStartup()

		# 更新の確認
		if selected == menuItemsStore.getRef("HELP_UPDATE"):
			update.checkUpdate()
		# バージョン情報
		if selected==menuItemsStore.getRef("HELP_VERSIONINFO"):
			d = versionDialog.dialog()
			d.Initialize()
			r = d.Show()

	def OnExit(self, event):
		if event.CanVeto():
			# Alt+F4が押された
			if globalVars.app.config.getboolean("general", "minimizeOnExit", True) and globalVars.app.tc.running:
				self.hide()
			else:
				super().OnExit(event)
				globalVars.app.tb.Destroy()
		else:
			super().OnExit(event)
			globalVars.app.tb.Destroy()

	def hide(self):
		self.parent.hFrame.Hide()

	def show(self):
		self.parent.hFrame.Show()
		self.parent.hPanel.SetFocus()

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

	def setKeymap(self, identifier,ttl, keymap=None,filter=None):
		if keymap:
			try:
				keys=keymap.map[identifier.upper()]
			except KeyError:
				keys={}
		else:
			try:
				keys=self.parent.menu.keymap.map[identifier.upper()]
			except KeyError:
				keys={}
		keyData={}
		menuData={}
		for refName in defaultKeymap.defaultKeymap[identifier.upper()].keys():
			title=menuItemsDic.getValueString(refName)
			prefix = ""
			if refName.startswith("TC_"):
				prefix = _("ツイキャス")
			if prefix:
				title = prefix + ":" + title
			if refName in keys:
				keyData[title]=keys[refName]
			else:
				keyData[title]=_("なし")
			menuData[title]=refName

		entries=[]
		for map in (self.parent.menu.keymap,self.parent.hotkey):
			for i in map.entries.keys():
				if identifier.upper()!=i:	#今回の変更対象以外のビューのものが対象
					entries.extend(map.entries[i])
		d=views.globalKeyConfig.Dialog(keyData,menuData,entries,filter)
		d.Initialize(ttl)
		if d.Show()==wx.ID_CANCEL: return False

		result={}
		keyData,menuData=d.GetValue()

		#キーマップの既存設定を置き換える
		newMap=ConfigManager.ConfigManager()
		newMap.read(constants.KEYMAP_FILE_NAME)
		for name,key in keyData.items():
			if key!=_("なし"):
				newMap[identifier.upper()][menuData[name]]=key
			else:
				newMap[identifier.upper()][menuData[name]]=""
		if newMap.write() != errorCodes.OK:
			errorDialog(_("設定の保存に失敗しました。下記のファイルへのアクセスが可能であることを確認してください。") + "\n" + os.path.abspath(constants.KEYMAP_FILE_NAME))
		return True
