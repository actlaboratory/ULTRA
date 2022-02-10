# -*- coding: utf-8 -*-
# Twitterアカウントの管理

import os
import wx
from logging import getLogger

from .baseDialog import *
import globalVars
import views.ViewCreator
import simpleDialog


class Dialog(BaseDialog):

	def __init__(self):
		super().__init__("spacesTokenManager")
		self._shouldExit = False

	def Initialize(self):
		self.log.debug("created")
		self.app = globalVars.app
		super().Initialize(self.app.hMainView.hFrame, _("Twitterアカウントの管理"))
		self.InstallControls()
		return True

	def InstallControls(self):
		"""いろんなwidgetを設置する。"""

		# 情報の表示
		self.creator = views.ViewCreator.ViewCreator(self.viewMode, self.panel, self.sizer, wx.VERTICAL, 20, style=wx.EXPAND | wx.ALL)
		self.hListCtrl, self.hListStatic = self.creator.virtualListCtrl(_("アカウント"), None, wx.LC_REPORT | wx.BORDER_RAISED, (800, 300), wx.ALL | wx.ALIGN_CENTER_HORIZONTAL)
		self.hListCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED, self.ItemSelected)
		self.hListCtrl.Bind(wx.EVT_LIST_ITEM_DESELECTED, self.ItemSelected)
		self.hListCtrl.AppendColumn(_("ユーザ名"), format=wx.LIST_FORMAT_LEFT, width=250)
		self.hListCtrl.AppendColumn(_("名前"),format=wx.LIST_FORMAT_LEFT,width=250)
		self.hListCtrl.AppendColumn(_("規定のアカウント"), format=wx.LIST_FORMAT_LEFT, width=250)
		self.hListCtrl.AppendColumn(_("ID"), format=wx.LIST_FORMAT_LEFT, width=110)
		self.hListCtrl.SetColumnsOrder([0, 1, 2])

		# 処理ボタン
		self.creator = views.ViewCreator.ViewCreator(self.viewMode, self.panel, self.creator.GetSizer(), wx.HORIZONTAL, 20, "", wx.ALIGN_RIGHT)
		g1 = views.ViewCreator.ViewCreator(self.viewMode, self.panel, self.creator.GetSizer(), wx.VERTICAL, 20, "")
		g1r1 = views.ViewCreator.ViewCreator(self.viewMode, self.panel, g1.GetSizer(), wx.HORIZONTAL, 20, "", wx.EXPAND)
		g1r2 = views.ViewCreator.ViewCreator(self.viewMode, self.panel, g1.GetSizer(), wx.HORIZONTAL, 20, "", wx.EXPAND)
		self.addButton = g1r1.button(_("追加(&A)"), self.add, proportion=1)
		self.deleteButton = g1r1.button(_("削除(&D)"), self.delete, proportion=1)
		self.deleteButton.Enable(False)
		self.setDefaultButton = g1r2.button(_("規定のアカウントに設定(&F)"), self.setDefault)
		self.setDefaultButton.Enable(False)

		g2 = views.ViewCreator.ViewCreator(self.viewMode, self.panel, self.creator.GetSizer(), wx.VERTICAL, 0)
		self.bClose = self.creator.closebutton(_("閉じる"), self.onCloseButton)
		self.refreshList()

	def refreshList(self):
		cursor = self.hListCtrl.GetFocusedItem()
		self.hListCtrl.DeleteAllItems()
		data = globalVars.app.spaces.tokenManager.getData()
		for i in data:
			if data[i]["default"]:
				state = _("設定中")
			else:
				state = ""
			self.hListCtrl.Append([
				data[i]["user"]["username"],
				data[i]["user"]["name"],
				state,
				str(i),
			])
		if cursor >= 0:
			try:
				self.hListCtrl.Focus(cursor)
				self.hListCtrl.Select(cursor)
			except:
				pass
		else:
			self.ItemSelected(None)

	def ItemSelected(self, event):
		self.deleteButton.Enable(self.hListCtrl.GetFocusedItem() >= 0)
		self.setDefaultButton.Enable(self.hListCtrl.GetFocusedItem() >= 0 and not globalVars.app.spaces.tokenManager.isDefaultAccount(int(self.hListCtrl.GetItemText(self.hListCtrl.GetFocusedItem(), 3))))

	def add(self, event):
		q = simpleDialog.yesNoDialog(_("アカウントの追加"), _("ブラウザを開いてアカウントの認証作業を行います。よろしいですか？"))
		if q == wx.ID_NO:
			return
		self.wnd.Enable(False)
		globalVars.app.spaces.tokenManager.addUser()
		self.wnd.Enable(True)
		self.refreshList()
		self.hListCtrl.SetFocus()

	def setDefault(self, event):
		key = int(self.hListCtrl.GetItemText(self.hListCtrl.GetFocusedItem(), 3))
		globalVars.app.spaces.tokenManager.setDefaultAccount(key)
		self.refreshList()
		self.hListCtrl.SetFocus()

	def delete(self, event):
		idx = self.hListCtrl.GetFocusedItem()
		key = int(self.hListCtrl.GetItemText(self.hListCtrl.GetFocusedItem(), 3))
		self.hListCtrl.DeleteItem(idx)
		globalVars.app.spaces.tokenManager.deleteUser(key)
		self.setDefaultButton.Enable(False)
		self.deleteButton.Enable(False)
		self.hListCtrl.SetFocus()

	def onCloseButton(self, event):
		if self.hListCtrl.GetItemCount() == 0:
			d = simpleDialog.yesNoDialog(_("確認"), _("Twitterアカウントの情報が設定されていません。Twitterとの連携を停止しますか？"))
			if d == wx.ID_YES:
				self._shouldExit = True
				event.Skip()
			else:
				return
		result = globalVars.app.spaces.tokenManager.hasDefaultAccount()
		if not result and self.hListCtrl.GetItemCount() > 0:
			simpleDialog.errorDialog(_("規定のアカウントが設定されていません。"))
			return
		event.Skip()

	def shouldExit(self):
		return self._shouldExit
