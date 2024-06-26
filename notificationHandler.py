# notification handler for ultra

import constants
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
			self.record = globalVars.app.config.getboolean("notification", "record", True)

	def notify(self, source, userName, link, stream, time, config=None, movie="", header={}):
		"""新着ライブの通知

		:param source: SourceBaseクラスを継承したオブジェクト
		:param source: source
		:param userName: 配信者のユーザ名
		:type userName: str
		:param link: 配信ページへのリンク
		:type link: str
		:param stream: ストリーミングのURL
		:type stream: str
		:param time: 放送開始日時のUnixタイムスタンプまたはdatetime.datetimeオブジェクト
		:type time: int/datetime.datetime
		:param config: 通知条件の設定。指定しなければデフォルト値が読み込まれる。
		:type config: dict
		:param movie: 通知対象の動画を識別するための文字列
		:type movie: str
		:param header: 録画時に送信するHTTPヘッダー
		:type movie: dict
		"""
		self.loadSettings(config)
		if self.baloon:
			b = wx.adv.NotificationMessage(constants.APP_NAME, _("配信開始：%s、サービス：%s") %(userName, source.friendlyName))
			b.Show()
			b.Close()
		if self.sound:
			fxPlayer.playFx(self.soundFile)
		if self.openBrowser:
			webbrowser.open_new(link)
		if self.record:
			r = recorder.Recorder(source, stream, userName, time, movie, header=header)
			r.start()
