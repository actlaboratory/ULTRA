# -*- coding: utf-8 -*-
# ストリーミング録画モジュール

import wx
import constants
import subprocess
import simpleDialog
import datetime
from time import sleep
import threading
import globalVars
import os
from logging import getLogger

# debug
# 0:何もしない、1:ffmpegのログをカレントディレクトリに保存
DEBUG = 0


class Recorder(threading.Thread):
	def __init__(self, source, stream, userName, time, movie="", *, header={}, userAgent="Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko", skipExisting=False, ext=None):
		"""コンストラクタ

		:param source: SourceBaseクラスを継承したオブジェクト。
		:type source: Source
		:param stream: ストリーミングURL
		:type stream: str
		:param userName: 配信者のユーザ名
		:type user: str
		:param time: 放送開始日時のUnixタイムスタンプまたはdatetime.datetimeオブジェクト
		:type time: int/datetime.datetime
		:param movie: 録画対象の動画を識別できる文字列
		:type movie: str
		:param header: ストリーミングのダウンロード時に追加で指定するHTTPヘッダ
		:type header: dict
		:param user-agent: 相手サーバに通知するユーザエージェント(省略時はIE11となる)
		:type userAgent: str
		:param skipExisting: 保存先ファイルが存在する場合、録画処理を中断するかどうか
		:type skipExisting: bool
		"""
		# 配信開始日時がとれなかったことを示すフラグ
		self.timeIsNone = time is None
		if type(time) in (int, float):
			time = datetime.datetime.fromtimestamp(time)
		elif time is None:
			time = datetime.datetime.now()
		self.stream = stream
		self.userName = userName
		self.time = time
		self.log = getLogger("%s.%s" % (constants.LOG_PREFIX, "recorder"))
		self.source = source
		self.movie = movie
		self.cookies = ""
		self.processHeader(header)
		self.userAgent = userAgent
		self.skipExisting = skipExisting
		if ext is None:
			self.ext = self.source.getFiletype()
		else:
			self.ext = ext
		# アプリの終了時の処理が途中で中断されないように、`daemon=False`とする
		super().__init__(daemon=False)
		self.log.info("stream URL: %s" % self.stream)
		self._exitFlag = False
		# ffmpegのpopenオブジェクト
		self.subProc: subprocess.Popen = None

	def processHeader(self, header):
		self.log.debug("Processing HTTP headers...")
		# key: valueの形式でリストに格納
		tmplst = []
		for key, value in header.items():
			if key.lower() == "cookie":
				self.log.debug("Processing cookies")
				cookieList = value.split(";")
				self.log.debug(f"cookie: {value} -> {cookieList}")
				self.cookies = "\r\n".join(cookieList)
				continue
			itemStr = f"{key}: {value}"
			tmplst.append(itemStr)
		# 改行区切りの文字列としてインスタンス変数に格納
		self.header = "\r\n".join(tmplst)

	def getOutputFile(self):
		"""設定値を元に、出力ファイルのパスを取得
		"""
		lst = []
		lst.append(self.replaceUnusableChar(globalVars.app.config["record"]["dir"]))
		if globalVars.app.config.getboolean("record", "createSubDir", True):
			lst.append(self.replaceUnusableChar(globalVars.app.config["record"]["subDirName"]))
		fname = self.replaceUnusableChar(globalVars.app.config["record"]["fileName"])
		if self.addMovieId():
			fname += "(%s)" % self.movie
		lst.append(fname)
		ext = self.ext
		path = "%s.%s" % ("\\".join(lst), ext)
		path = self.extractVariable(path)
		os.makedirs(os.path.dirname(path), exist_ok=True)
		path = os.path.abspath(path)
		if os.path.exists(path) and not self.skipExisting:
			count = 1
			base = os.path.splitext(path)[0]
			tmp = "%s (%i).%s" % (base, count, ext)
			while os.path.exists(tmp):
				count += 1
				tmp = "%s (%i).%s" % (base, count, ext)
			path = tmp
		self.path = path
		return path

	def extractVariable(self, fileName):
		"""変数を使って指定したファイル名から正しい名前を得る

		:param fileName: ファイル名
		:type fileName: str
		"""
		map = {
			"%source%": self.source.name,
			"%user%": self.userName.replace(":", "-"),
			"%movie%": self.movie,
			"%year%": self.time.strftime("%Y"),
			"%month%": self.time.strftime("%m"),
			"%day%": self.time.strftime("%d"),
			"%hour%": self.time.strftime("%H"),
			"%minute%": self.time.strftime("%M"),
			"%second%": self.time.strftime("%S"),
		}
		for key, value in map.items():
			fileName = fileName.replace(key, value)
		return fileName

	def replaceUnusableChar(self, st):
		"""ファイル名・フォルダ名として使用できない文字があれば使用できる文字に置換する

		:param st: ファイル名・フォルダ名
		:type st: str
		"""
		map = {
			"/": "／",
			"*": "＊",
			"?": "？",
			"\"": "”",
			"<": "＜",
			">": "＞",
			"|": "｜",
		}
		return st.translate(str.maketrans(map))

	def getCommand(self):
		"""コマンドラインで実行する文字列を取得
		"""
		cmd = [
			constants.FFMPEG_PATH,
			"-loglevel",
			"error",
		]
		if DEBUG == 1:
			cmd.append("-report")
		if self.header != "":
			cmd += [
				"-headers",
				'"%s"' % self.header,
			]
		if self.userAgent:
			cmd += [
				"-user_agent",
				'"%s"' % self.userAgent,
			]
		if self.cookies:
			cmd += [
				"-cookies",
				'"%s"' % self.cookies,
			]
		cmd += [
			"-i",
			'"%s"' % self.stream,
			"-max_muxing_queue_size",
			"1024",
		]
		if not self.needEncode(self.ext):
			cmd += [
				"-c",
				"copy",
			]
		cmd.append('"%s"' % self.getOutputFile())
		return cmd

	def run(self):
		if self.shouldSkip():
			return
		# 録画に成功した、あるいは録画を中断すべきと判断するまで処理を繰り返す
		while True:
			try:
				cmd = self.getCommand()
			except IOError:
				d = simpleDialog.yesNoDialog(_("録画エラー"), _("録画の開始に失敗しました。録画の保存先が適切に設定されていることを確認してください。定期的に再試行する場合は[はい]、処理を中断する場合は[いいえ]を選択してください。[はい]を選択して録画の保存先を変更することで、正しく録画を開始できる場合があります。"))
				if d == wx.ID_NO:
					globalVars.app.hMainView.addLog(_("録画エラー"), _("%sのライブの録画処理を中断しました。") % self.userName)
					return
				max = 30
				for i in range(max):
					try:
						cmd = self.getCommand()
						break
					except IOError:
						self.log.info("#%i failed." % i)
						sleep(30)
				if i + 1 == max:
					globalVars.app.hMainView.addLog(_("録画エラー"), _("%sのライブの録画処理を中断しました。") % self.userName)
					return
			self.log.debug("command: " + " ".join(cmd))
			globalVars.app.hMainView.addLog(_("録画開始"), _("ユーザ：%(user)s、ムービーID：%(movie)s") % {"user": self.userName, "movie": self.movie}, self.source.friendlyName)
			globalVars.app.tb.setAlternateText(_("録画中"))
			# 録画開始前に終了処理が行われていたら、ここで動作を終了
			if self._exitFlag:
				self.log.debug("Recording canceled")
				return
			self.source.onRecord(self.path, self.movie)
			self.subProc = subprocess.Popen(" ".join(cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=False, encoding="utf-8", creationflags=subprocess.CREATE_NO_WINDOW)
			self.log.debug("Subprocess opened, pid: %d" % self.subProc.pid)
			self.subProc.wait()
			self.log.info("saved: %s" % self.path)
			# 終了処理が行われていたらここで動作を止める
			if self._exitFlag:
				self.log.debug("recording canceled after saving a file")
				return
			# 標準出力を取得
			result = self.subProc.communicate()[0]
			# エラーメッセージがない、つまり録画成功
			if len(result) == 0:
				break
			self.log.info("FFMPEG returned some errors.\n" + result)
			if not self.source.onRecordError(self.movie):
				self.log.info("End of recording")
				globalVars.app.hMainView.addLog(_("録画エラー"), (_("%sのライブを録画中にエラーが発生しました。") % self.userName) + (_("詳細：%s") % result), self.source.friendlyName)
				break
			if "404 Not Found" in result:
				self.log.info("not found")
				globalVars.app.hMainView.addLog(_("録画エラー"), (_("%sのライブを録画中にエラーが発生しました。") % self.userName) + (_("詳細：%s") % result), self.source.friendlyName)
				break
			globalVars.app.hMainView.addLog(_("録画エラー"), (_("%sのライブを録画中にエラーが発生したため、再度録画を開始します。") % self.userName) + (_("詳細：%s") % result), self.source.friendlyName)
			sleep(15)
		globalVars.app.hMainView.addLog(_("録画終了"), _("ユーザ：%(user)s、ムービーID：%(movie)s") % {"user": self.userName, "movie": self.movie}, self.source.friendlyName)
		if getRecordingUsers(self) == []:
			globalVars.app.tb.setAlternateText()

	def shouldSkip(self):
		return self.skipExisting and os.path.exists(self.getOutputFile())

	def getTargetUser(self):
		"""誰のライブを録画中かを返す
		"""
		return self.userName

	def isRecordedByAnotherThread(self):
		for i in getActiveObj(self):
			if i.stream == self.stream:
				return True
		return False

	def needEncode(self, ext):
		from sources.twitcasting import Twitcasting
		# ツイキャスは必ずMP4
		# 231009 tsも許容
		if isinstance(self.source, Twitcasting) and ext in ("mp4", "ts"):
			return False
		return True
	
	def addMovieId(self):
		# 配信開始日時がとれなかった
		if self.timeIsNone:
			return True
		# ydl
		from sources.ydl import YDL
		if isinstance(self.source, YDL):
			return True
		# 通常は不要
		return False

	def exit(self):
		self.log.debug("exitting...")
		self._exitFlag = True
		if self.subProc:
			self.subProc.communicate("q")

def getRecordingUsers(self=None):
	"""現在録画中のユーザ名のリストを返す
	"""
	ret = []
	for i in threading.enumerate():
		if type(i) == Recorder and i != self:
			ret.append(i.getTargetUser())
	return ret


def getActiveObj(self=None):
	"""現在動作中のレコーダーオブジェクトのリストを返す
	"""
	ret = []
	for i in threading.enumerate():
		if type(i) == Recorder and i != self:
			ret.append(i)
	return ret
