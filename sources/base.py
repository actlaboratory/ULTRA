# -*- coding: utf-8 -*-
# source base

import threading

class SourceBase(threading.Thread):
	"""各サービスのライブ監視などを行う際のベースクラス
	"""

	def __init__(self):
		"""コンストラクタ。このメソッドをオーバーライドして、スレッドを使う必要がある場合には、必ずsuper().__init__()を呼ぶこと。
		"""
		super().__init__(daemon=True)

	def initialize(self):
		"""アカウントの認証など、準備として必要な作業を行う。
		"""
		return True

	def run(self):
		"""スレッドを使う場合、ライブの監視などメインの作業をここに書く。
		"""
		pass

	def onRecord(self, path):
		"""録画を始めたタイミングで呼ばれる

		:param path: 録画の保存先パス
		:type path: str
		"""
		pass
