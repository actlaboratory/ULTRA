# notification handler for ultra

import webbrowser
import globalVars
import wx.adv

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
			b = wx.adv.NotificationMessage("ULTRA", _("配信開始：%s") %(userName))
			b.Show()
		if self.sound:
			# dummy
			# とりあえずビープを鳴らすようにしておく
			import winsound
			winsound.Beep(800, 100)
		if self.openBrowser:
			webbrowser.open_new(link)
		if self.record:
			# 録画処理に渡す
			pass
