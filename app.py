# -*- coding: utf-8 -*-
#Application Main

import win32api
import win32event
import winerror
import AppBase
import update
import globalVars
import proxyUtil
import notificationHandler
from sources import twitcasting
import threading
import sys

class Main(AppBase.MainBase):
	def __init__(self):
		super().__init__()

	def OnInit(self):
		#多重起動防止
		globalVars.mutex = win32event.CreateMutex(None, 1, "ULTRA")
		if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
			globalVars.mutex = None
			return False
		return True

	def initialize(self):
		self.setGlobalVars()
		# プロキシの設定を適用
		if self.config.getboolean("network", "auto_proxy"):
			self.proxyEnviron = proxyUtil.virtualProxyEnviron()
			self.proxyEnviron.set_environ()
		else:
			self.proxyEnviron = None
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
		self.tc = twitcasting.Twitcasting()
		# 「ツイキャスの監視を有効化」の設定値を確認
		if self.config.getboolean("twitcasting", "enable", True) and self.tc.initialize():
			self.tc.start()
		self.hMainView.Show()
		if self.config.getboolean("general", "autoHide", False):
			self.hMainView.events.hide()
		return True

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

		self._releaseMutex()

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
