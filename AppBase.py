﻿# -*- coding: utf-8 -*-
#Application Initializer

import accessible_output2.outputs
import datetime
import gettext
import glob
import locale
import logging
import logging.handlers
import os
import sys
import traceback
import win32api
import wx

from accessible_output2.outputs.base import OutputError

import constants
import DefaultSettings
import views.langDialog
import simpleDialog


class MaiｎBase(wx.App):
	def __init__(self):
		"""アプリを初期化する。"""
		super().__init__()

		#実行環境の取得(exeファイルorインタプリタ)
		self.frozen=hasattr(sys,"frozen")

		#各種初期設定
		self.InitLogger()
		self.LoadSettings()
		# localeは「ja_JP」のような形式。設定ファイルの定義ミスにより「_」ではなく「-」を使っていたため、必要に応じて最初に設定ファイルを書き換える。
		locale_old = self.config["general"]["locale"]
		if "-" in locale_old:
			locale_new = locale_old.replace("-", "_")
			self.log.warn("Fixed locale setting: %s -> %s" % (locale_old, locale_new))
			self.config["general"]["locale"] = locale_new
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
		try:
			self._InitSpeech()
		except OutputError as e:
			self.log.error("Failed to initialize speech output.")
			self.log.error(traceback.format_exc())
			simpleDialog.winDialog(_("音声エンジンエラー"), _("音声読み上げ機能の初期化に失敗したため、読み上げ機能を使用できません。出力先の変更をお試しください。"))
			self.speech = accessible_output2.outputs.nospeech.NoSpeech()

	def _InitSpeech(self):
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
			self.deleteAllLogs()
			self.hLogHandler=logging.handlers.RotatingFileHandler(constants.LOG_FILE_NAME, mode="w", encoding="UTF-8", maxBytes=2**20*256, backupCount=5)
			self.hLogHandler.setLevel(logging.DEBUG)
			self.hLogFormatter=logging.Formatter("%(name)s - %(levelname)s - %(message)s (%(asctime)s)")
			self.hLogHandler.setFormatter(self.hLogFormatter)
			logger=logging.getLogger(constants.LOG_PREFIX)
			logger.setLevel(logging.DEBUG)
			logger.addHandler(self.hLogHandler)
		except Exception as e:
			traceback.print_exc()
		self.log=logging.getLogger(constants.LOG_PREFIX+".Main")
		r="executable" if self.frozen else "interpreter"
		self.log.info("Starting"+constants.APP_NAME+" "+constants.APP_VERSION+" as %s!" % r)

	def deleteAllLogs(self):
		for i in glob.glob("%s*" % constants.LOG_FILE_NAME):
			os.remove(i)

	def LoadSettings(self):
		"""設定ファイルを読み込む。なければデフォルト設定を適用し、設定ファイルを書く。"""
		self.config = DefaultSettings.DefaultSettings.get()
		if not self.config.read(constants.SETTING_FILE_NAME):
			#初回起動
			self.config.read_dict(DefaultSettings.initialValues)
			self.config.write()
		if self.log.hasHandlers():
			self.hLogHandler.setLevel(self.config.getint("general","log_level",20,0,50))

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

	def getAppPath(self):
		"""アプリの絶対パスを返す
		"""
		if self.frozen:
			# exeファイルで実行されている
			return sys.executable
		else:
			# pyファイルで実行されている
			return os.path.join(os.path.dirname(__file__), os.path.basename(sys.argv[0]))
