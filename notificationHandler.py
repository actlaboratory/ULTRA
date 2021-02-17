# notification handler for ultra

import webbrowser
import globalVars

class NotificationHandler:
	def loadSettings(self):
		"""通知方法の設定を読み込む
		"""
		self.baloon = globalVars.app.config.getboolean("notification", "baloon", True)
		self.sound = globalVars.app.config.getboolean("notification", "sound", False)
		self.openBrowser = globalVars.app.config.getboolean("notification", "openBrowser", False)
		self.record = globalVars.app.config.getboolean("notification", "record", False)

	def notify(self, userName, displayName, link, stream):
		"""新着ライブの通知

		:param userName: 配信者のユーザ名
		:type userName: str
		:param displayName: 配信者の表示名
		:type displayName: str
		:param link: 配信ページへのリンク
		:type link: str
		:param stream: ストリーミングのURL
		:type stream: str
		"""
		self.loadSettings()
		if self.baloon:
			# バルーンを出す
			pass
		if self.sound:
			self.playSound()
		if self.openBrowser:
			webbrowser.open_new(link)
		if self.record:
			# 録画処理に渡す
			pass

	def playSound(self):
		"""通知音を鳴らす
		"""
		# dummy
		# とりあえずビープを鳴らすようにしておく
		import winsound
		winsound.Beep(800, 100)
