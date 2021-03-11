# Taskbar Icon

import wx
import wx.adv
import globalVars
import constants
from views.base import BaseMenu


class TaskbarIcon(wx.adv.TaskBarIcon):
	def __init__(self):
		super().__init__()
		icon = wx.Icon()
		self.SetIcon(icon, constants.APP_NAME)
		self.Bind(wx.adv.EVT_TASKBAR_LEFT_DCLICK, self.onDoubleClick)

	def CreatePopupMenu(self):
		bm = BaseMenu("mainView")
		menu = wx.Menu()
		menu.Bind(wx.EVT_MENU, globalVars.app.hMainView.events.OnMenuSelect)
		bm.RegisterMenuCommand(menu, "EXIT")
		return menu

	def onDoubleClick(self, event):
		globalVars.app.hMainView.hFrame.Show()