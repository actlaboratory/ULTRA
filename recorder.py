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
			

class Recorder(threading.Thread):
	def __init__(self, source, stream, userName, time, movie=""):
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
		"""        
		if type(time) == int:
			time = datetime.datetime.fromtimestamp(time)
		self.stream = stream
		self.userName = userName
		self.time = time
		self.log = getLogger("%s.%s" %(constants.LOG_PREFIX, "recorder"))
		self.source = source
		self.movie = movie
		super().__init__(daemon=True)
		self.log.info("stream URL: %s" %self.stream)

	def getOutputFile(self):
		"""設定値を元に、出力ファイルのパスを取得
		"""		
		lst = []
		lst.append(self.replaceUnusableChar(globalVars.app.config["record"]["dir"]))
		if globalVars.app.config.getboolean("record", "createSubDir", True):
			lst.append(self.replaceUnusableChar(globalVars.app.config["record"]["subDirName"]))
		lst.append(self.replaceUnusableChar(globalVars.app.config["record"]["fileName"]))
		ext = globalVars.app.config.getstring("record", "extension", "ts", constants.SUPPORTED_FILETYPE)
		path = "%s.%s" %("\\".join(lst), ext)
		path = self.extractVariable(path)
		os.makedirs(os.path.dirname(path), exist_ok=True)
		path = os.path.abspath(path)
		if os.path.exists(path):
			count = 1
			base = os.path.splitext(path)[0]
			tmp = "%s (%i).%s" %(base, count, ext)
			while os.path.exists(tmp):
				count += 1
				tmp = "%s (%i).%s" %(base, count, ext)
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
			"-i",
			self.stream,
			self.getOutputFile(),
		]
		return cmd

	def run(self):
		if self.userName in getRecordingUsers(self):
			globalVars.app.hMainView.addLog(_("録画スキップ"), _("このユーザのライブはすでに録画中のため、処理をスキップします。"), self.source.friendlyName)
			return
		try:
			cmd = self.getCommand()
		except IOError:
			d = simpleDialog.yesNoDialog(_("録画エラー"), _("録画の開始に失敗しました。録画の保存先が適切に設定されていることを確認してください。定期的に再試行する場合は[はい]、処理を中断する場合は[いいえ]を選択してください。[はい]を選択して録画の保存先を変更することで、正しく録画を開始できる場合があります。"))
			if d == wx.ID_NO:
				globalVars.app.hMainView.addLog(_("録画エラー"), _("%sのライブの録画処理を中断しました。") %self.userName)
				return
			max = 30
			for i in range(max):
				try:
					cmd = self.getCommand()
					break
				except IOError:
					self.log.info("#%i failed." %i)
					sleep(30)
			if i + 1 == max:
				globalVars.app.hMainView.addLog(_("録画エラー"), _("%sのライブの録画処理を中断しました。") %self.userName)
				return
		self.source.onRecord(self.path, self.movie)
		globalVars.app.hMainView.addLog(_("録画開始"), _("ユーザ：%(user)s、ムービーID：%(movie)s") %{"user": self.userName, "movie": self.movie}, self.source.friendlyName)
		globalVars.app.tb.setAlternateText(_("録画中"))
		self.log.debug("command: " + " ".join(cmd))
		result = subprocess.run(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True, encoding="utf-8")
		self.log.info("saved: %s" %self.path)
		while len(result.stdout) > 0:
			self.log.info("FFMPEG returned some errors.\n" + result.stdout)
			if "404 Not Found" in result.stdout:
				break
			globalVars.app.hMainView.addLog(_("録画エラー"), (_("%sのライブを録画中にエラーが発生したため、再度録画を開始します。") %self.userName) + (_("詳細：%s") %result.stdout), self.source.friendlyName)
			sleep(15)
			cmd = self.getCommand()
			self.source.onRecord(self.path, self.movie)
			result = subprocess.run(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=True, encoding="utf-8")
			self.log.info("saved: %s" %self.path)
		globalVars.app.hMainView.addLog(_("録画終了"), _("ユーザ：%(user)s、ムービーID：%(movie)s") %{"user": self.userName, "movie": self.movie}, self.source.friendlyName)
		if getRecordingUsers(self) == []:
			globalVars.app.tb.setAlternateText()

	def getTargetUser(self):
		"""誰のライブを録画中かを返す
		"""
		return self.userName

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
