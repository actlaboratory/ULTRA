# -*- coding: utf-8 -*-
#Application Main

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

	def initialize(self):
		self.setGlobalVars()
		# プロキシの設定を適用
		if self.config.getboolean("network", "auto_proxy"):
			self.proxyEnviron = proxyUtil.virtualProxyEnviron()
			self.proxyEnviron.set_environ()
		else:
			self.proxyEnviron = None
		self.installThreadExcepthook()
		# アップデートを実行
		if self.config.getboolean("general", "update"):
			globalVars.update.update(True)
		# メインビューを表示
		from views import main
		self.hMainView=main.MainView()
		self.notificationHandler = notificationHandler.NotificationHandler()
		self.tc = twitcasting.Twitcasting()
		# 「ツイキャスの監視を有効化」の設定値を確認
		if self.config.getboolean("twitcasting", "checkLive", False):
			self.tc.start()
		self.hMainView.Show()
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


		#戻り値は無視される
		return 0
