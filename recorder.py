# -*- coding: utf-8 -*-
# ストリーミング録画モジュール

import constants
import subprocess
import datetime
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
		super().__init__()

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
			"%user%": self.userName,
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
			"\\": "￥",
			"/": "／",
			":": "：",
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
		cmd = self.getCommand()
		self.source.onRecord(self.path, self.movie)
		result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
		self.log.info("saved: %s" %self.path)
		while len(result.stdout) > 0:
			self.log.info("FFMPEG returned some errors.")
			cmd = self.getCommand()
			self.source.onRecord(self.path, self.movie)
			result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
			self.log.info("saved: %s" %self.path)
