# -*- coding: utf-8 -*-
# settings dialog

import os
import wx

import constants
import errorCodes
import simpleDialog
import views.ViewCreator

from enum import Enum,auto
from views.baseDialog import *


class configType(Enum):
	BOOL = auto()
	INT = auto()
	STRING = auto()
	DIC = auto()


class Dialog(BaseDialog):
	colorModeSelection = {
		"white": _("標準"),
		"dark": _("ダーク")
	}
	languageSelection = constants.SUPPORTING_LANGUAGE

	def __init__(self):
		super().__init__("settingsDialog")
		self.iniDic = {}			#iniファイルと作ったオブジェクトの対応

	def Initialize(self):
		self.log.debug("created")
		super().Initialize(self.app.hMainView.hFrame,_("設定"))
		self.InstallControls()
		self.load()
		self.checkBoxStatusChanged()	#初期値を反映する為一度呼び出しておく
		return True

	def InstallControls(self):
		"""いろんなwidgetを設置する。"""

		# tab
		self.creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.VERTICAL,20)
		self.tab = self.creator.tabCtrl(_("カテゴリ選択"))

		# general
		creator=views.ViewCreator.ViewCreator(self.viewMode,self.tab,None,wx.VERTICAL,label=_("一般"),space=20,style=wx.ALL,margin=20)
		self.autohide = creator.checkbox(_("起動時にウィンドウを隠す(&H)"))
		self.minimizeonexit = creator.checkbox(_("終了時にタスクトレイに最小化(&M)"))

		# view
		creator=views.ViewCreator.ViewCreator(self.viewMode,self.tab,None,views.ViewCreator.GridBagSizer,label=_("表示/言語"),style=wx.ALL,margin=20)
		self.language, static = creator.combobox(_("言語(&L)"), list(self.languageSelection.values()))
		self.colormode, static = creator.combobox(_("画面表示モード(&D)"), list(self.colorModeSelection.values()))

		# notification
		creator=views.ViewCreator.ViewCreator(self.viewMode,self.tab,None,wx.VERTICAL,space=20,label=_("通知"),style=wx.ALL|wx.EXPAND,margin=20)
		self.baloon = creator.checkbox(_("バルーン通知"))
		self.record = creator.checkbox(_("録画"))
		self.openbrowser = creator.checkbox(_("ブラウザで開く"))
		self.sound = creator.checkbox(_("サウンドを再生"), self.checkBoxStatusChanged)
		creator=views.ViewCreator.ViewCreator(self.viewMode,creator.GetPanel(),creator.GetSizer(),wx.HORIZONTAL,space=5,style=wx.ALL|wx.EXPAND,margin=0)
		self.soundfile, static = creator.inputbox(_("再生するサウンド"), proportion=1,textLayout=wx.VERTICAL)
		self.soundfile.hideScrollBar(wx.HORIZONTAL)
		self.soundfileBrowse = creator.button(_("参照"), self.browse,sizerFlag=wx.BOTTOM|wx.ALIGN_BOTTOM,margin=10)

		# record
		creator=views.ViewCreator.ViewCreator(self.viewMode,self.tab,None,wx.VERTICAL,space=20,label=_("録画"),style=wx.ALL|wx.EXPAND,margin=20)
		dirArea=views.ViewCreator.ViewCreator(self.viewMode,creator.GetPanel(),creator.GetSizer(),wx.HORIZONTAL,space=5,style=wx.ALL|wx.EXPAND,margin=0)
		self.dir, static = dirArea.inputbox(_("保存先フォルダ(&F)"),proportion=1,textLayout=wx.VERTICAL)
		self.dir.hideScrollBar(wx.HORIZONTAL)
		self.dirBrowse = dirArea.button(_("参照"), self.browseDir,sizerFlag=wx.BOTTOM|wx.ALIGN_BOTTOM,margin=10)

		self.createsubdir = creator.checkbox(_("ユーザごとにサブフォルダを作成(&S)"))
		self.filename, static = creator.inputbox(_("保存ファイル名(&N)"),sizerFlag=wx.EXPAND)
		self.filename.hideScrollBar(wx.HORIZONTAL)

		# network
		creator=views.ViewCreator.ViewCreator(self.viewMode,self.tab,None,wx.VERTICAL,space=20,label=_("ネットワーク"),style=wx.ALL,margin=20)
		self.update = creator.checkbox(_("起動時に更新を確認(&U)"))
		self.usemanualsetting = creator.checkbox(_("プロキシサーバーの情報を手動で設定する(&M)"), self.checkBoxStatusChanged)
		self.server, static = creator.inputbox(_("サーバーURL"))
		self.server.hideScrollBar(wx.HORIZONTAL)
		self.port, static = creator.spinCtrl(_("ポート番号"), 0, 65535, defaultValue=8080)

		# buttons
		creator=views.ViewCreator.ViewCreator(self.viewMode,self.panel,self.sizer,wx.HORIZONTAL,style=wx.ALIGN_RIGHT)
		self.okbtn = creator.okbutton("OK", self.onOkButton, proportion=1)
		self.cancelBtn = creator.cancelbutton(_("キャンセル"), proportion=1)

	def load(self):
		# general
		self._setValue(self.autohide,"general","autohide",configType.BOOL,False)
		self._setValue(self.minimizeonexit, "general", "minimizeOnExit", configType.BOOL, True)

		# view
		self._setValue(self.language,"general","language",configType.DIC,self.languageSelection)
		self._setValue(self.colormode,"view","colormode",configType.DIC,self.colorModeSelection)

		# notification
		self._setValue(self.baloon, "notification", "baloon", configType.BOOL, True)
		self._setValue(self.record, "notification", "record", configType.BOOL, True)
		self._setValue(self.openbrowser, "notification", "openBrowser", configType.BOOL, False)
		self._setValue(self.sound, "notification", "sound", configType.BOOL, False)
		self._setValue(self.soundfile, "notification", "soundFile", configType.STRING, "")

		# record
		self._setValue(self.dir, "record", "dir", configType.STRING, "output")
		self._setValue(self.createsubdir, "record", "createSubDir", configType.BOOL, True)
		self._setValue(self.filename, "record", "filename", configType.STRING, "%user%_%year%%month%%day%_%hour%%minute%%second%")

		# network
		self._setValue(self.update, "general", "update", configType.BOOL)
		self._setValue(self.usemanualsetting, "proxy", "usemanualsetting", configType.BOOL)
		self._setValue(self.server, "proxy", "server", configType.STRING)
		self._setValue(self.port, "proxy", "port", configType.STRING)

	def onOkButton(self, event):
		result = self._save()
		event.Skip()

	def checkBoxStatusChanged(self, event=None):
		# proxy
		result = self.usemanualsetting.GetValue()
		self.server.Enable(result)
		self.port.Enable(result)
		# sound
		result = self.sound.GetValue()
		self.soundfile.GetParent().Enable(result)
		self.soundfileBrowse.Enable(result)

	def _setValue(self, obj, section, key, t, prm=None, prm2=None):
		assert isinstance(obj,wx.Window)
		assert type(section)==str
		assert type(key)==str
		assert type(t)==configType

		conf=self.app.config

		if t==configType.DIC:
			assert type(prm) == dict
			assert isinstance(obj,wx.ComboBox)
			obj.SetValue(prm[conf.getstring(section,key,prm2,prm.keys())])
		elif t==configType.BOOL:
			if prm==None:
				prm = True
			assert type(prm) == bool
			obj.SetValue(conf.getboolean(section,key,prm))
		elif t==configType.STRING:
			if prm==None:
				prm = ""
			assert type(prm) == str
			obj.SetValue(conf.getstring(section,key,prm,prm2))
		self.iniDic[obj]=(t,section,key,prm,prm2)

	def _save(self):
		conf = self.app.config
		for obj,v in self.iniDic.items():
			if v[0]==configType.DIC:
				conf[v[1]][v[2]] = list(v[3].keys())[obj.GetSelection()]
			else:
				conf[v[1]][v[2]] = obj.GetValue()
		if conf.write() != errorCodes.OK:
			simpleDialog.errorDialog(_("設定の保存に失敗しました。下記のファイルへのアクセスが可能であることを確認してください。") + "\n" + os.path.abspath(constants.SETTING_FILE_NAME))

	def browse(self, event):
		target = self.soundfile
		dialog = wx.FileDialog(self.wnd, _("効果音ファイルを選択"), wildcard=_("音声ファイル（.wav/.mp3/.ogg）") + "|*.wav;*.mp3;*.ogg", style=wx.FD_OPEN)
		result = dialog.ShowModal()
		if result == wx.ID_CANCEL:
			return
		target.SetValue(dialog.GetPath())

	def browseDir(self, event):
		target = self.dir
		dialog = wx.DirDialog(self.wnd, _("保存先フォルダを選択"))
		result = dialog.ShowModal()
		if result == wx.ID_CANCEL:
			return
		target.SetValue(dialog.GetPath())
