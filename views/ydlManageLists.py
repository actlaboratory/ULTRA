# -*- coding: utf-8 -*-
#ydl：一括ダウンロードリストの管理
#Copyright (C) 2020 yamahubuki <itiro.ishino@gmail.com>
#Note: All comments except these top lines will be written in Japanese. 

from typing import Set
import views.KeyValueSettingDialogBase
import wx
import constants
import globalVars
import re
import simpleDialog

class Dialog(views.KeyValueSettingDialogBase.KeyValueSettingDialogBase):
	def __init__(self):
		self.ydl = globalVars.app.ydl
		self.listManager = self.ydl.listManager
		columnInfo = [
			(_("ID"), 0, 300),
			(_("タイトル"), 0, 300),
			(_("URL"), 0, 300),
			(_("データ取得間隔"), 0, 300),
		]
		titles = {}
		urls = {}
		intervals = {}
		data = self.listManager.getData()
		for key in data:
			titles[key] = data[key]["title"]
			urls[key] = data[key]["url"]
			intervals[key] = data[key]["interval"]
		super().__init__("ydlManageLists", SettingDialog, columnInfo, titles, urls, intervals)

	def Initialize(self):
		super().Initialize(self.app.hMainView.hFrame,_("一括ダウンロードURLの管理"))
		self.hListCtrl.SetColumnsOrder([1, 2, 3])
		return

	def GetValue(self):
		data = super().GetValue()
		ret = {}
		for key in data[0]:
			ret[key] = {
				"title": data[0][key],
				"url": data[1][key],
				"interval": data[2][key],
			}
		return ret

class SettingDialog(views.KeyValueSettingDialogBase.SettingDialogBase):
	"""設定内容を入力するダイアログ"""

	def __init__(self, parent, key="", title="", url="", interval="3600"):
		self.ydl = globalVars.app.ydl
		self.listManager = self.ydl.listManager
		super().__init__(
			parent,
			[
				(_("ID"), None),
				(_("タイトル"), None),
				(_("URL"), url == ""),
				(_("データ取得間隔（秒）"), True)
			],
			[None] * 4,
			key, title, url, interval
		)

	def Initialize(self):
		return super().Initialize(_("登録内容編集"))

	def OkButtonEvent(self, event):
		return self.Validation(event)

	def Validation(self, event):
		# データ取得間隔は数値のみ
		if not re.fullmatch("[0-9]+", self.edits[3].GetValue()):
			simpleDialog.errorDialog(_("データ取得間隔には数値（秒数）を指定してください。"))
			return
		# プレイリストURLであることの確認
		# すでにデータを取得済みならば確認不要
		if self.edits[0].GetValue() != "":
			event.Skip()
			return
		url = self.edits[2].GetValue()
		try:
			info = self.ydl.extractInfo(url)
		except Exception as e:
			simpleDialog.errorDialog(_("不正なURLが入力されました。\n詳細：%s" % e))
			return
		_type = info.get("_type", "video")
		if _type == "video":
			simpleDialog.errorDialog(_("この機能では、動画のURLを直接指定することができません。プレイリストやチャンネルページのURLを入力してください。"))
			return
		entry = self.listManager.convertInfoToEntry(info, int(self.edits[3].GetValue()))
		key = tuple(entry.keys())[0]
		self.edits[0].SetValue(key)
		self.edits[1].SetValue(entry[key]["title"])
		event.Skip()

