# -*- coding: utf-8 -*-
# source base

import threading
import globalVars

class SourceBase(threading.Thread):
	"""各サービスのライブ監視などを行う際のベースクラス
	"""
	# サービスの名前（録画時に使う場合がある）
	name = ""
	# ユーザに見せるサービスの名前
	friendlyName = ""
	# 動作状況リストで使うインデックス
	index = 0

	def __init__(self):
		"""コンストラクタ。このメソッドをオーバーライドして、スレッドを使う必要がある場合には、必ずsuper().__init__()を呼ぶこと。
		"""
		globalVars.app.hMainView.statusList.InsertItem(self.index, self.friendlyName)
		self.initThread()

	def initThread(self):
		super().__init__(daemon=True)

	def initialize(self):
		"""アカウントの認証など、準備として必要な作業を行う。
		"""
		return True

	def run(self):
		"""スレッドを使う場合、ライブの監視などメインの作業をここに書く。
		"""
		pass

	def onRecord(self, path, movie):
		"""録画を始めたタイミングで呼ばれる

		:param path: 録画の保存先パス
		:type path: str
		:param movie: 録画を始める動画の識別子
		:type movie: str
		"""
		pass

	def setStatus(self, status):
		"""動作状況表示を更新

		:param status: 現在の状況
		:type status: str
		"""
		globalVars.app.hMainView.statusList.SetItem(self.index, 1, status)

	def onRecordError(self, movie):
		"""[summary]

		:param movie: エラーが起きた動画の識別子
		:type movie: str
		:return: 再試行するかどうか
		:rtype: bool
		"""
		return False
