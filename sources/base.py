# -*- coding: utf-8 -*-
# source base

import threading
import globalVars
import wx
from views.base import BaseMenu
import constants


class SourceBase(threading.Thread):
	"""各サービスのライブ監視などを行う際のベースクラス
	"""
	# サービスの名前（録画時に使う場合がある）
	name = ""
	# ユーザに見せるサービスの名前
	friendlyName = ""
	# 動作状況リストで使うインデックス
	index = 0
	# 録画可能な形式
	# {"拡張子": _("メニューに表示する名前"),...}の形式
	filetypes = {}
	# 規定の録画形式
	# filetypes.keys()に存在するものでなければならない
	defaultFiletype = ""
	if len(filetypes) > 0:
		assert defaultFiletype in filetypes.keys()

	def __init__(self):
		"""コンストラクタ。このメソッドをオーバーライドして、スレッドを使う必要がある場合には、必ずsuper().__init__()を呼ぶこと。
		"""
		globalVars.app.hMainView.statusList.InsertItem(self.index, self.friendlyName)
		self.initThread()

	def initThread(self):
		super().__init__(daemon=True)

	def initialize(self):
		"""アカウントの認証など、準備として必要な作業を行う。
		"""
		return True

	def run(self):
		"""スレッドを使う場合、ライブの監視などメインの作業をここに書く。
		"""
		pass

	def onRecord(self, path, movie):
		"""録画を始めたタイミングで呼ばれる

		:param path: 録画の保存先パス
		:type path: str
		:param movie: 録画を始める動画の識別子
		:type movie: str
		"""
		pass

	def setStatus(self, status):
		"""動作状況表示を更新

		:param status: 現在の状況
		:type status: str
		"""
		wx.CallAfter(globalVars.app.hMainView.statusList.SetItem, self.index, 1, status)

	def onRecordError(self, movie):
		"""[summary]

		:param movie: エラーが起きた動画の識別子
		:type movie: str
		:return: 再試行するかどうか
		:rtype: bool
		"""
		return False

	def getActiveSourceCount(self, includeSelf=False):
		count = 0
		t = threading.enumerate()
		for i in t:
			if isinstance(i, SourceBase):
				if i != self:
					count += 1
				elif includeSelf:
					count += 1
		return count

	@classmethod
	def getFiletype(cls):
		ext = globalVars.app.config.getstring(cls.name.lower(), "filetype")
		if ext not in cls.filetypes.keys():
			ext = cls.getDefaultFiletype()
			cls.setFiletype(ext)
		return ext

	@classmethod
	def getDefaultFiletype(cls):
		return cls.defaultFiletype

	@classmethod
	def setFiletype(cls, filetype):
		globalVars.app.config[cls.name.lower()]["filetype"] = filetype

	@classmethod
	def getAvailableFiletypes(cls):
		return cls.filetypes

	@classmethod
	def getFiletypesMenu(cls, menu: wx.Menu):
		menu.Bind(wx.EVT_MENU, cls.onFiletypeSelected)
		for i in range(menu.GetMenuItemCount()):
			menu.DestroyItem(menu.FindItemByPosition(0))
		ext_default = cls.getFiletype()
		count = 0
		for ext, name in cls.getAvailableFiletypes().items():
			id = constants.FILETYPES_MENU_INDEX + cls.index * 100 + count
			menu.AppendRadioItem(id, name)
			if ext == ext_default:
				menu.Check(id, True)
			count += 1

	@classmethod
	def onFiletypeSelected(cls, event):
		id = event.GetId()
		index = id - constants.FILETYPES_MENU_INDEX - cls.index * 100
		ext = tuple(cls.getAvailableFiletypes().keys())[index]
		cls.setFiletype(ext)
		event.Skip()
