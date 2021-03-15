# -*- coding: utf-8 -*-
#ツイキャス：ユーザーの管理
#Copyright (C) 2020 yamahubuki <itiro.ishino@gmail.com>
#Note: All comments except these top lines will be written in Japanese. 

from typing import Set
import views.KeyValueSettingDialogBase
import wx
import constants
import globalVars
import simpleDialog

SPECIFIC_INDEX = 3
SOUND_INDEX = 7

class Dialog(views.KeyValueSettingDialogBase.KeyValueSettingDialogBase):
	def __init__(self):
		columnInfo = [
			(_("ユーザID"), 0, 300),
			(_("ユーザ名"), 0, 300),
			(_("名前"), 0, 200),
			(_("専用設定"), 0, 100),
			(_("バルーン通知"), 0, 100),
			(_("録画"), 0, 100),
			(_("ブラウザで開く"), 0, 100),
			(_("サウンドを再生"), 0, 100),
			(_("再生するサウンド"), 0, 200)
		]
		user = {}
		name = {}
		specific = {}
		baloon = {}
		record = {}
		openBrowser = {}
		sound = {}
		soundFile = {}
		globalVars.app.tc.loadUserList()
		for k, v in globalVars.app.tc.users.items():
			if "remove" in v.keys():
				continue
			user[k] = v["user"]
			name[k] = v["name"]
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
		super().__init__("tcManageUser", SettingDialog, columnInfo, user, name, specific, baloon, record, openBrowser, sound, soundFile)
		for i in range(len(columnInfo)):
			self.SetCheckResultValueString(i, _("有効"), _("無効"))

	def Initialize(self):
		super().Initialize(self.app.hMainView.hFrame,_("ユーザの管理"))
		self.hListCtrl.SetColumnsOrder([1,2,3,4,5,6,7,8])
		return

	def GetValue(self):
		data = super().GetValue()
		ret = {}
		for i in data[0]:
			ret[i] = {
				"user": data[0][i],
				"name": data[1][i],
				"specific": data[2][i],
				"baloon": data[3][i],
				"record": data[4][i],
				"openBrowser": data[5][i],
				"sound": data[6][i],
				"soundFile": data[7][i],
			}
		return ret

class SettingDialog(views.KeyValueSettingDialogBase.SettingDialogBase):
	"""設定内容を入力するダイアログ"""

	def __init__(self, parent, key="", user="", name="", specific=False, baloon=None, record=None, openBrowser=None, sound=None, soundFile=None):
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
				(_("名前"), None),
				("", _("専用設定を使用")),
				("", _("バルーン通知")),
				("", _("録画")),
				("", _("ブラウザで開く")),
				("", _("サウンドを再生")),
				(_("再生するサウンド"), True),
			],
			[None] * 8 + [(_("参照"), self.browse)],
			key, user, name, specific, baloon, record, openBrowser, sound, soundFile
		)

	def Initialize(self):
		return super().Initialize(_("通知設定"))

	def OkButtonEvent(self, event):
		return self.Validation(event)

	def Validation(self, event):
		if self.edits[1].GetValue() == "":
			simpleDialog.errorDialog(_("ユーザ名が入力されていません。"))
			return
		if self.edits[0].GetValue() != "":
			event.Skip()
			return
		user = globalVars.app.tc.getUserInfo(self.edits[1].GetValue())
		if user == None:
			return
		self.edits[0].SetValue(user["user"]["id"])
		self.edits[2].SetValue(user["user"]["name"])
		event.Skip()

	def InstallControls(self):
		super().InstallControls()
		self.edits[SPECIFIC_INDEX].Bind(wx.EVT_CHECKBOX, self.onSpecifyChanged)
		self.edits[SOUND_INDEX].Bind	(wx.EVT_CHECKBOX, self.onSoundChanged)
		self.onSpecifyChanged()

	def onSpecifyChanged(self, event=None):
		state = self.edits[SPECIFIC_INDEX].GetValue()
		for i in range(SPECIFIC_INDEX + 1, len(self.edits)):
			self.edits[i].GetParent().Enable(state)
		self.buttonObjects[SOUND_INDEX + 1].Enable(state)
		if state:
			self.onSoundChanged()

	def onSoundChanged(self, event=None):
		state = self.edits[SOUND_INDEX].GetValue()
		for i in range(SOUND_INDEX + 1, len(self.edits)):
			self.edits[i].GetParent().Enable(state)
		self.buttonObjects[SOUND_INDEX + 1].Enable(state)

	def browse(self, event):
		target = self.edits[SOUND_INDEX + 1]
		dialog = wx.FileDialog(self.wnd, _("効果音ファイルを選択"), wildcard="WAVE files (*.wav)|*.wav", style=wx.FD_OPEN)
		result = dialog.ShowModal()
		if result == wx.ID_CANCEL:
			return
		target.SetValue(dialog.GetPath())
