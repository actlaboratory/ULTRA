# notification handler for ultra

import webbrowser
import globalVars
import wx.adv

class NotificationHandler:
	def loadSettings(self, config):
		"""通知方法の設定を読み込む

		:param config: 通知条件。Noneならばデフォルト値を適用。
		:type config: dict
		"""
		if type(config) == dict:
			self.baloon = config["baloon"]
			self.sound = config["sound"]
			self.openBrowser = config["openBrowser"]
			self.record = config["record"]
		else:
			self.baloon = globalVars.app.config.getboolean("notification", "baloon", True)
			self.sound = globalVars.app.config.getboolean("notification", "sound", False)
			self.openBrowser = globalVars.app.config.getboolean("notification", "openBrowser", False)
			self.record = globalVars.app.config.getboolean("notification", "record", False)

	def notify(self, userName, displayName, link, stream, config=None):
		"""新着ライブの通知

		:param userName: 配信者のユーザ名
		:type userName: str
		:param displayName: 配信者の表示名
		:type displayName: str
		:param link: 配信ページへのリンク
		:type link: str
		:param stream: ストリーミングのURL
		:type stream: str
		:param config: 通知条件の設定。指定しなければデフォルト値が読み込まれる。
		:type config: dict
		"""
		self.loadSettings(config)
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
