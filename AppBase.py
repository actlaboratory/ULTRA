# -*- coding: utf-8 -*-
#Application Initializer

import accessible_output2.outputs
import sys
import gettext
import logging
import wx
import locale
import win32api
import datetime
from logging import getLogger, FileHandler, Formatter

import constants
import DefaultSettings
import views.langDialog
import simpleDialog
import os
import traceback

class MaiｎBase(wx.App):
	def __init__(self):
		"""アプリを初期化する。"""
		super().__init__()

		#実行環境の取得(exeファイルorインタプリタ)
		self.frozen=hasattr(sys,"frozen")

		#各種初期設定
		self.InitLogger()
		self.LoadSettings()
		try:
			if self.config["general"]["locale"]!=None:
				locale.setlocale(locale.LC_TIME,self.config["general"]["locale"])
			else:
				locale.setlocale(locale.LC_TIME)
		except:
			locale.setlocale(locale.LC_TIME)
			self.config["general"]["locale"]=""
		self.SetTimeZone()
		self.InitTranslation()
		self.InitSpeech()
		# ログのファイルハンドラーが利用可能でなければ警告を出す
		if not self.log.hasHandlers():
			simpleDialog.errorDialog(_("ログ機能の初期化に失敗しました。下記のファイルへのアクセスが可能であることを確認してください。") + "\n" + os.path.abspath(constants.LOG_FILE_NAME))

	def InitSpeech(self):
		# 音声読み上げの準備
		reader=self.config["speech"]["reader"]
		if(reader=="PCTK"):
			self.log.info("use reader 'PCTalker'")
			self.speech=accessible_output2.outputs.pc_talker.PCTalker()
		elif(reader=="NVDA"):
			self.log.info("use reader 'NVDA'")
			self.speech=accessible_output2.outputs.nvda.NVDA()
		#SAPI4はバグってるっぽいので無効にしておく
#		elif(reader=="SAPI4"):
#			self.log.info("use reader 'SAPI4'")
#			self.speech=accessible_output2.outputs.sapi4.Sapi4()
		elif(reader=="SAPI5"):
			self.log.info("use reader 'SAPI5'")
			self.speech=accessible_output2.outputs.sapi5.SAPI5()
		elif(reader=="AUTO"):
			self.log.info("use reader 'AUTO'")
			self.speech=accessible_output2.outputs.auto.Auto()
		elif(reader=="JAWS"):
			self.log.info("use reader 'JAWS'")
			self.speech=accessible_output2.outputs.jaws.Jaws()
		elif(reader=="CLIPBOARD"):
			self.log.info("use reader 'CLIPBOARD'")
			self.speech=accessible_output2.outputs.clipboard.Clipboard()
		elif(reader=="NOSPEECH"):
			self.log.info("use reader 'NOSPEECH'")
			self.speech=accessible_output2.outputs.nospeech.NoSpeech()
		else:
			self.config.set("speech","reader","AUTO")
			self.log.warning("Setting missed! speech.reader reset to 'AUTO'")
			self.speech=accessible_output2.outputs.auto.Auto()

	def InitLogger(self):
		"""ログ機能を初期化して準備する。"""
		try:
			self.hLogHandler=FileHandler(constants.LOG_FILE_NAME, mode="w", encoding="UTF-8")
			self.hLogHandler.setLevel(logging.DEBUG)
			self.hLogFormatter=Formatter("%(name)s - %(levelname)s - %(message)s (%(asctime)s)")
			self.hLogHandler.setFormatter(self.hLogFormatter)
			logger=getLogger(constants.LOG_PREFIX)
			logger.setLevel(logging.DEBUG)
			logger.addHandler(self.hLogHandler)
		except Exception as e:
			traceback.print_exc()
		self.log=getLogger(constants.LOG_PREFIX+".Main")
		r="executable" if self.frozen else "interpreter"
		self.log.info("Starting"+constants.APP_NAME+" as %s!" % r)

	def LoadSettings(self):
		"""設定ファイルを読み込む。なければデフォルト設定を適用し、設定ファイルを書く。"""
		self.config = DefaultSettings.DefaultSettings.get()
		if not self.config.read(constants.SETTING_FILE_NAME):
			#初回起動
			self.config.read_dict(DefaultSettings.initialValues)
			self.config.write()

	def InitTranslation(self):
		"""翻訳を初期化する。"""
		loc = locale.getdefaultlocale()[0].replace("_", "-")
		lang=self.config.getstring("general","language","",constants.SUPPORTING_LANGUAGE.keys())
		if lang == "":
			if loc in list(constants.SUPPORTING_LANGUAGE.keys()):
				self.config["general"]["language"] = loc
			else:
				# 言語選択を表示
				langSelect = views.langDialog.langDialog()
				langSelect.Initialize()
				langSelect.Show()
				self.config["general"]["language"] = langSelect.GetValue()
			lang = self.config["general"]["language"]
		self.translator=gettext.translation("messages","locale", languages=[lang], fallback=True)
		self.translator.install()

	def GetFrozenStatus(self):
		"""コンパイル済みのexeで実行されている場合はTrue、インタプリタで実行されている場合はFalseを帰す。"""
		return self.frozen

	def say(self,s,interrupt=False):
		"""スクリーンリーダーでしゃべらせる。"""
		self.speech.speak(s, interrupt=interrupt)
		self.speech.braille(s)

	def SetTimeZone(self):
		bias=win32api.GetTimeZoneInformation(True)[1][0]*-1
		hours=bias//60
		minutes=bias%60
		self.timezone=datetime.timezone(datetime.timedelta(hours=hours,minutes=minutes))
