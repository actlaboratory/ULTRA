# notification handler for ultra

import webbrowser
import globalVars
import wx.adv
from soundPlayer import fxPlayer
import recorder

class NotificationHandler:
	def loadSettings(self, config):
		"""通知方法の設定を読み込む

		:param config: 通知条件。Noneならばデフォルト値を適用。
		:type config: dict
		"""
		if type(config) == dict:
			self.baloon = config["baloon"]
			self.sound = config["sound"]
			self.soundFile = config["soundFile"]
			self.openBrowser = config["openBrowser"]
			self.record = config["record"]
		else:
			self.baloon = globalVars.app.config.getboolean("notification", "baloon", True)
			self.sound = globalVars.app.config.getboolean("notification", "sound", False)
			self.soundFile = globalVars.app.config["notification"]["soundFile"]
			self.openBrowser = globalVars.app.config.getboolean("notification", "openBrowser", False)
			self.record = globalVars.app.config.getboolean("notification", "record", False)

	def notify(self, userName, displayName, link, stream, time, config=None):
		"""新着ライブの通知

		:param userName: 配信者のユーザ名
		:type userName: str
		:param displayName: 配信者の表示名
		:type displayName: str
		:param link: 配信ページへのリンク
		:type link: str
		:param stream: ストリーミングのURL
		:type stream: str
		:param time: 放送開始日時のUnixタイムスタンプまたはdatetime.datetimeオブジェクト
		:type time: int/datetime.datetime
		:param config: 通知条件の設定。指定しなければデフォルト値が読み込まれる。
		:type config: dict
		"""
		self.loadSettings(config)
		if self.baloon:
			b = wx.adv.NotificationMessage("ULTRA", _("配信開始：%s") %(userName))
			b.Show()
		if self.sound:
			fxPlayer.playFx(self.soundFile)
		if self.openBrowser:
			webbrowser.open_new(link)
		if self.record:
			r = recorder.Recorder(stream, userName, time)
			r.start()
