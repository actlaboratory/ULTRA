# Taskbar Icon

import wx
import wx.adv
import globalVars
import constants
from views.base import BaseMenu


class TaskbarIcon(wx.adv.TaskBarIcon):
	def __init__(self):
		super().__init__()
		self.icon = wx.Icon(constants.APP_ICON)
		self.SetIcon(self.icon, constants.APP_NAME)
		self.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.onDoubleClick)

	def CreatePopupMenu(self):
		bm = BaseMenu("mainView")
		menu = wx.Menu()
		menu.Bind(wx.EVT_MENU, globalVars.app.hMainView.events.OnMenuSelect)
		bm.RegisterMenuCommand(menu, [
			"SHOW", "EXIT",
		])
		return menu

	def onDoubleClick(self, event):
		globalVars.app.hMainView.events.show()

	def setAlternateText(self, text=""):
		"""タスクバーアイコンに表示するテキストを変更する。「アプリ名 - 指定したテキスト」の形になる。

		:param text: アプリ名に続けて表示するテキスト
		:type text: str
		"""
		if text != "":
			text = " - " + text
		self.SetIcon(self.icon, constants.APP_NAME + text)
