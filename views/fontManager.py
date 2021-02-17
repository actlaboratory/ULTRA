# -*- coding: utf-8 -*-
#Copyright (C) 2019 yamahubuki <itiro.ishino@gmail.com>

import logging
import wx
from logging import getLogger
#from .base import *
import constants
import DefaultSettings
import globalVars
from simpleDialog import *


class FontManager():
	def __init__(self):
		self.identifier="FontManager"
		self.log=getLogger("%s.%s" % (constants.APP_NAME,self.identifier))
		self.log.debug("created")
		self.app=globalVars.app

		# 設定ファイルの情報を基にfontを生成
		self.font=wx.Font();
		if self.app:
			if not self.font.SetNativeFontInfoUserDesc(self.app.config.get("view","font")):
				dialog(_("エラー"),_("設定されているフォント情報が不正です。デフォルトのフォントを適用します。"))
				self.log.warning("fontString error. SetNativeFontInfoUserDesc("+self.app.config.get("view","font")+") returned false.")
				self.font.SetNativeFontInfoUserDesc(DefaultSettings.get("view","font"))
				self.app.config.set("view","font",DefaultSettings.get("view","font"))
				with open(constants.SETTING_FILE_NAME, "w") as f: self.config.write(f)
		else:
			self.font.SetNativeFontInfoUserDesc("bold 'ＭＳ ゴシック' 22")

	# フォント設定ダイアログを表示
	# 引数に親ウィンドウを指定
	def ShowSettingDialog(self,parent):
		# FontDataを生成し、設定を行う
		fontData=wx.FontData()
		fontData.EnableEffects(False)		#取り消し線などは設定できない
		fontData.SetAllowSymbols(False)		#シンボルフォントの設定は認めない
		fontData.SetRange(constants.FONT_MIN_SIZE,constants.FONT_MAX_SIZE)
		fontData.SetInitialFont(self.font)

		fontchooser=wx.FontDialog(parent,fontData)
		if (fontchooser.ShowModal()==wx.ID_OK):
			font=fontchooser.GetFontData().GetChosenFont()
		else:
			self.log.info("font change was canceled.")
		#アサーションエラーの対策
		if not font.IsOk():
			dialog(_("エラー"),_("原因不明のエラーにより、フォントの変更に失敗しました。"))
			self.log.warning("font change error. IsOK() returned False.")
			return false
		self.font=font
		return True

	def GetFont(self):
		return self.font

	def GetName(self):
		return self.font.GetFaceName()

	def GetSize(self):
		return self.font.GetPointSize()

	def GetInfo(self):
		return self.font.GetNativeFontInfoUserDesc()
