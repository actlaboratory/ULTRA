# -*- coding: utf-8 -*-
#ツイキャス：ユーザーの管理
#Copyright (C) 2020 yamahubuki <itiro.ishino@gmail.com>
#Note: All comments except these top lines will be written in Japanese. 

from typing import Set
import views.KeyValueSettingDialogBase
import wx
import constants
import globalVars

class Dialog(views.KeyValueSettingDialogBase.KeyValueSettingDialogBase):
	def __init__(self):
		columnInfo = [
			(_("ユーザID"), 0, 200),
			(_("ユーザ名"), 0, 200),
			(_("専用設定"), 0, 200),
			(_("バルーン通知"), 0, 200),
			(_("録画"), 0, 100),
			(_("ブラウザで開く"), 0, 200),
			(_("サウンドを再生"), 0, 200),
			(_("再生するサウンド"), 0, 200)
		]
		user = {}
		specific = {}
		baloon = {}
		record = {}
		openBrowser = {}
		sound = {}
		soundFile = {}
		globalVars.app.tc.loadUserList()
		for k, v in globalVars.app.tc.users.items():
			user[k] = v["user"]
			specific[k] = v["specific"]
			if v["specific"]:
				baloon[k] = v["baloon"]
				record[k] = v["record"]
				openBrowser[k] = v["openBrowser"]
				sound[k] = v["sound"]
				soundFile[k] = v["soundFile"]
			else:
				baloon[k] = globalVars.app.config.getboolean("notification", "baloon", True)
				record[k] = globalVars.app.config.getboolean("notification", "record", True)
				openBrowser[k] = globalVars.app.config.getboolean("notification", "openBrowser", False)
				sound[k] = globalVars.app.config.getboolean("notification", "sound", False)
				soundFile[k] = globalVars.app.config["notification"]["soundFile"]
		super().__init__("tcManageUser", SettingDialog, columnInfo, user, specific, baloon, record, openBrowser, sound, soundFile)
		for i in range(len(columnInfo)):
			self.SetCheckResultValueString(i, _("有効"), _("無効"))

	def Initialize(self):
		super().Initialize(self.app.hMainView.hFrame,_("ユーザの管理"))
		return

	def GetValue(self):
		data = super().GetValue()
		ret = {}
		for i in data[0]:
			ret[i] = {
				"user": data[0][i],
				"specific": data[1][i],
				"baloon": data[2][i],
				"record": data[3][i],
				"openBrowser": data[4][i],
				"sound": data[5][i],
				"soundFile": data[6][i],
			}
		return ret

class SettingDialog(views.KeyValueSettingDialogBase.SettingDialogBase):
	"""設定内容を入力するダイアログ"""

	def __init__(self, parent, key="", user="", specific=False, baloon=None, record=None, openBrowser=None, sound=None, soundFile=None):
		if baloon == None:
			baloon = globalVars.app.config.getboolean("notification", "baloon", True)
		if record == None:
			record = globalVars.app.config.getboolean("notification", "record", True)
		if openBrowser == None:
			openBrowser = globalVars.app.config.getboolean("notification", "openBrowser", False)
		if sound == None:
			sound = globalVars.app.config.getboolean("notification", "sound", False)
		if soundFile == None:
			soundFile = globalVars.app.config["notification"]["soundFile"]
		super().__init__(
			parent,
			[
				(_("ユーザID"), None),
				(_("ユーザ名"), user == ""),
				("", _("専用設定を使用")),
				("", _("バルーン通知")),
				("", _("録画")),
				("", _("ブラウザで開く")),
				("", _("サウンドを再生")),
				(_("再生するサウンド"), True),
			],
			[None] * 8,
			key, user, specific, baloon, record, openBrowser, sound, soundFile
		)

	def Initialize(self):
		return super().Initialize(_("通知設定"))

	def OkButtonEvent(self, event):
		return self.Validation(event)

	def Validation(self, event):
		user = globalVars.app.tc.getUserIdFromScreenId(self.edits[1].GetValue())
		if user == constants.NOT_FOUND:
			return
		self.edits[0].SetValue(user)
		event.Skip()

	def InstallControls(self):
		super().InstallControls()
		self.edits[2].Bind(wx.EVT_CHECKBOX, self.onSpecifyChanged)
		self.onSpecifyChanged()

	def onSpecifyChanged(self, event=None):
		state = self.edits[2].GetValue()
		for i in range(3, len(self.edits)):
			self.edits[i].GetParent().Enable(state)
