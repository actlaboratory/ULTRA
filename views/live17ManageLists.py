# -*- coding: utf-8 -*-
#17LIVE：一括ダウンロードリストの管理
#Copyright (C) 2025 yamahubuki <itiro.ishino@gmail.com>
#Note: All comments except these top lines will be written in Japanese. 

from typing import Set
import views.KeyValueSettingDialogBase
import wx
import constants
import globalVars
import re
import simpleDialog

class Dialog(views.KeyValueSettingDialogBase.KeyValueSettingDialogBase):
	def __init__(self, data):
		titles = {}
		urls = {}
		intervals = {}
		for key in data:
			titles[key] = data[key]["title"]
			urls[key] = data[key]["url"]
			intervals[key] = str(data[key]["interval"])
		super().__init__(
			"live17ManageLists",
			SettingDialog,
			[
				(_("ID"), 0, 300),
				(_("タイトル"), 0, 300),
				(_("URL"), 0, 300),
				(_("ダウンロード間隔"), 0, 300),
			],
			titles,
			urls,
			intervals
		)

	def Initialize(self, parent):
		super().Initialize(parent, _("17LIVE：一括ダウンロードURLの管理"))
		self.hListCtrl.SetColumnsOrder([1, 2, 3])

	def GetValue(self):
		data = super().GetValue()
		ret = {}
		for key in data[0]:
			ret[key] = {
				"title": data[0][key],
				"url": data[1][key],
				"interval": int(data[2][key]),
			}
		return ret

class SettingDialog(views.KeyValueSettingDialogBase.SettingDialogBase):
	"""設定内容を入力するダイアログ"""

	def __init__(self, parent, key="", title="", url="", interval="3600"):
		self.live17 = globalVars.app.live17
		super().__init__(
			parent,
			[
				(_("ID"), None),
				(_("タイトル"), None if url == "" else True),
				(_("URL"), url == ""),
				(_("ダウンロード間隔（秒）"), True)
			],
			[None] * 4,
			key, title, url, interval
		)

	def Initialize(self):
		return super().Initialize(_("登録内容編集"))

	def OkButtonEvent(self, event):
		return self.Validation(event)

	def Validation(self, event):
		# ダウンロード間隔は数値のみ
		if not re.fullmatch("[0-9]+", self.edits[3].GetValue()):
			simpleDialog.errorDialog(_("ダウンロード間隔には数値（秒数）を指定してください。"))
			return

		# アーカイブ一覧ページURLであることの確認とユーザー情報の取得
		# すでにデータを取得済みならば確認不要
		if self.edits[0].GetValue() != "":
			event.Skip()
			return
		url = self.edits[2].GetValue()
		try:
			room_id = self.live17.parseRoomUrl(url)
			user_info = self.live17.getUserFromRoomId(room_id)
		except Exception as e:
			simpleDialog.errorDialog(_("不正なURLが入力されました。\n詳細：%s" % e))
			return

		self.edits[0].SetValue(user_info["user_id"])
		self.edits[1].SetValue(user_info["user_display_name"])
		event.Skip()
