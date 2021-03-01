# -*- coding: utf-8 -*-
# update dialog
# Copyright (C) 2020 Hiroki Fujii <hfujii@hisystron.com>

import wx

import constants
import globalVars
import simpleDialog
import views.ViewCreator

from logging import getLogger
from views.baseDialog import *

class updateDialog(BaseDialog):
	def __init__(self):
		self.running = False
		self.info = globalVars.update.info
		super().__init__("update_dialog")

	def Initialize(self):
		self.log.debug("created")
		super().Initialize(None,_("アップデート - %s") % constants.APP_NAME,)
		self.InstallControls()
		return True

	def InstallControls(self):
		"""いろんなwidgetを設置する。"""

		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.VERTICAL,5,style=wx.ALL,margin=20)
		if self.info["code"] == 200:
			self.infoStatic = self.creator.staticText(_("version %s にアップデートできます。") % (self.info["update_version"]))
			self.gauge, self.gaugeStatic = self.creator.gauge(_("進行状況"),x=600,style=wx.TOP,margin=5, textLayout=None)
			self.gauge.Disable()
			self.infoEdit, self.infoEditStatic = self.creator.inputbox(_("version %s アップデート情報") % (self.info["update_version"]), defaultValue = self.info["update_description"], x=600, style = wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_RAISED)
			self.infoEdit.SetMinSize((600, 200))
			self.infoEdit.SetMaxSize((600, 200))
			creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.creator.GetSizer(),wx.HORIZONTAL,20,style=wx.ALIGN_RIGHT|wx.TOP,margin=20)
			self.startBtn = creator.button(_("アップデート"), self.run_update)
		elif self.info["code"] == 205:
			self.infoEdit, self.infoEditStatic = self.creator.inputbox(_("緊急のお知らせがあります。"), defaultValue = self.info["info_description"], style = wx.TE_MULTILINE | wx.TE_READONLY | wx.BORDER_RAISED)

			creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.creator.GetSizer(),wx.HORIZONTAL,20,style=wx.ALIGN_RIGHT)
			self.openBtn = creator.button(_("お知らせページへ"), self.open_browser)
		self.cancelBtn = creator.cancelbutton(_("キャンセル"), self.cancel)

	def cancel(self, events):
		if self.running:
			globalVars.update.exit()
			return
		self.end()

	def open_browser(self, events):
		globalVars.update.open_site()
		self.end()

	def run_update(self, events):
		self.running = True
		self.infoStatic.SetLabel(_("アップデートをダウンロード中..."))
		self.startBtn.Disable()
		self.gauge.Enable()
		self.cancelBtn.SetFocus()
		globalVars.update.start()

	def updater_notFound(self):
		simpleDialog.dialog(_("エラー"), _("updater.exeが見つかりませんでした。誤って削除したかなどをご確認ください。"))
		self.end()

	def end(self):
		self.wnd.EndModal(wx.ID_OK)

	#def GetData(self):
		return None
