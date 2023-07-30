# -*- coding: utf-8 -*-
#Application Main

import win32api
import win32event
import winerror
import AppBase
import update
import os
import globalVars
import pipe
import proxyUtil
import notificationHandler
import threading
import sys

class Main(AppBase.MainBase):
	def __init__(self):
		super().__init__()

	def isDevelopmentMode(self):
		# コマンドライン引数に`dev`を渡すと、開発中モードとして動作する。
		return "dev" in sys.argv

	def OnInit(self):
		#多重起動防止
		if self.isDevelopmentMode():
			# 開発モードでは多重起動防止とパイプの処理を抑制
			return True
		globalVars.mutex = win32event.CreateMutex(None, 1, "ULTRA")
		if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
			globalVars.mutex = None
			pipe.sendPipe()
			return False
		else:
			pipe.startServer()
			return True

	def initialize(self):
		self.setGlobalVars()
		# プロキシの設定を適用
		self.proxyEnviron = proxyUtil.virtualProxyEnviron()
		self.setProxyEnviron()
		# スレッドで例外が起きてもsys.exceptHookが呼ばれるようにする
		self.installThreadExcepthook()
		# タスクバーアイコンの準備
		import views.tbIcon
		self.tb = views.tbIcon.TaskbarIcon()
		# アップデートを実行
		if self.config.getboolean("general", "update"):
			globalVars.update.update(True)
		# メインビューを表示
		from views import main
		self.hMainView=main.MainView()
		self.notificationHandler = notificationHandler.NotificationHandler()
		if self.config.getint("general", "fileVersion", 100) == 100:
			# 録画形式設定
			from sources import twitcasting
			ext = self.config.getstring("record", "extension", "ts")
			source = twitcasting.Twitcasting
			if ext in source.getAvailableFiletypes():
				source.setFiletype(ext)
			else:
				source.setFiletype(source.getDefaultFiletype())
				import simpleDialog
				simpleDialog.dialog(_("録画形式の設定"), _("%(source)sの録画形式として%(ext)s形式が使用できなくなりました。規定値の%(ext_default)s形式に変更します。") % {"source": source.friendlyName, "ext": ext.upper(), "ext_default": source.getDefaultFiletype().upper()})
			self.config.remove_option("record", "extension")
			self.config["general"]["fileVersion"] = 101
		from sources import twitcasting
		self.tc = twitcasting.Twitcasting()
		# 「ツイキャスの監視を有効化」の設定値を確認
		if self.config.getboolean("twitcasting", "enable", True) and self.tc.initialize():
			self.tc.start()
		from sources import ydl
		self.ydl = ydl.YDL()
		if self.config.getboolean("ydl", "enable", True) and self.ydl.initialize():
			self.ydl.start()
		self.hMainView.Show()
		if self.config.getboolean("general", "autoHide", False):
			self.hMainView.events.hide()
		return True

	def setProxyEnviron(self):
		if self.config.getboolean("proxy", "usemanualsetting", False) == True:
			self.proxyEnviron.set_environ(self.config["proxy"]["server"], self.config.getint("proxy", "port", 8080, 0, 65535))
		else:
			self.proxyEnviron.set_environ()

	def setGlobalVars(self):
		globalVars.update = update.update()
		return

	def installThreadExcepthook(self):
		_init = threading.Thread.__init__

		def init(self, *args, **kwargs):
			_init(self, *args, **kwargs)
			_run = self.run

			def run(*args, **kwargs):
				try:
					_run(*args, **kwargs)
				except:
					sys.excepthook(*sys.exc_info())
			self.run = run

		threading.Thread.__init__ = init

	def OnExit(self):
		#設定の保存やリソースの開放など、終了前に行いたい処理があれば記述できる
		#ビューへのアクセスや終了の抑制はできないので注意。

		if self.isDevelopmentMode():
			# 開発モードでは、mutexやパイプの処理は不要
			# アップデート
			globalVars.update.runUpdate()
			#戻り値は無視される
			return 0
		self._releaseMutex()
		pipe.stopServer()

		# アップデート
		globalVars.update.runUpdate()

		#戻り値は無視される
		return 0

	def _releaseMutex(self):
		if globalVars.mutex != None:
			try: win32event.ReleaseMutex(globalVars.mutex)
			except Exception as e:
				return
			globalVars.mutex = None
			self.log.info("mutex object released.")

	def __del__(self):
		self._releaseMutex()
		pipe.stopServer()

	def getProxyInfo(self):
		"""プロキシサーバーの情報を取得

		:return: (URL, port)のタプル
		:rtype: tuple
		"""
		data = os.environ.get("HTTP_PROXY")
		self.log.debug("Retrieving proxy information from environment variable...")
		if data == None:
			self.log.info("Proxy information could not be found.")
			return (None, None)
		self.log.debug("configured data: %s" %data)
		separator = data.rfind(":")
		if separator == -1:
			self.log.info("Validation Error.")
			return (None, None)
		url = data[:separator]
		port = data[separator + 1:]
		try:
			port = int(port)
		except ValueError:
			self.log.info("Validation Error.")
			return (None, None)
		self.log.info("Proxy URL: %s, Port: %s." %(url, port))
		return (url, port)
