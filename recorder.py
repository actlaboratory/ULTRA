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
from collections import deque
from logging import getLogger

# debug
# 0:何もしない、1:ffmpegのログをカレントディレクトリに保存
DEBUG = 0

# ffmpegの出力のうち、エラーの判定と表示のために保持する行数（末尾から数える）
# ffmpegが同じエラーを出し続けてもメモリーを使い切らないように、上限を設ける
OUTPUT_MAX_LINES = 100

# ffmpegが応答のないサーバーを待つ時間（秒）
# 指定しないと、ffmpegはいつまでも待ち続ける
RW_TIMEOUT_SEC = 30

# 録画を再試行するまでの待ち時間（秒）
RETRY_INTERVAL_SEC = 15

# 何も録画できないまま再試行を続ける回数の上限
MAX_FAILED_RETRIES = 20

# 録画できたとみなすファイルサイズの下限（バイト）
# mp4は、データがなくてもヘッダーだけを書き込むことがあるため、0バイトより大きいだけでは判断できない
MIN_RECORDED_SIZE = 10 * 1024

# ステータス定数
STATUS_PREPARED = 0
STATUS_RECORDING = 1
STATUS_SUCCESS = 2
STATUS_SKIPED = 8
STATUS_ERROR = 9

class Recorder(threading.Thread):
	def __init__(self, source, stream, userName, time, movie="", *, header={}, userAgent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36", skipExisting=False, ext=None):
		"""コンストラクタ

		:param source: SourceBaseクラスを継承したオブジェクト。
		:type source: Source
		:param stream: ストリーミングURL
		:type stream: str
		:param userName: 配信者のユーザ名
		:type userName: str
		:param time: 放送開始日時のUnixタイムスタンプまたはdatetime.datetimeオブジェクト
		:type time: int/datetime.datetime
		:param movie: 録画対象の動画を識別できる文字列
		:type movie: str
		:param header: ストリーミングのダウンロード時に追加で指定するHTTPヘッダ
		:type header: dict
		:param userAgent: 相手サーバに通知するユーザエージェント(省略時はChromeとなる)
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
		# 再試行の待ち時間を、終了処理で打ち切るためのイベント
		self._exitEvent = threading.Event()
		# ffmpegのpopenオブジェクト
		self.subProc: subprocess.Popen = None
		self.status = STATUS_PREPARED

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
		path = self.replaceUnusableChar(self.extractVariable(path))
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
			"-rw_timeout",
			str(RW_TIMEOUT_SEC * 1000000),
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
			self.status = STATUS_SKIPED
			return
		# 何も録画できないまま再試行した回数
		failedRetries = 0
		# いずれかの回で録画できたかどうか
		recordedAny = False
		# source.onRecord()を呼んだかどうか
		onRecordCalled = False
		# 録画に成功した、あるいは録画を中断すべきと判断するまで処理を繰り返す
		while True:
			try:
				cmd = self.getCommand()
			except IOError:
				import traceback
				self.log.info("IOError: %s" % traceback.format_exc())
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
			# 録画開始前に終了処理が行われていたら、ここで動作を終了
			if self._exitFlag:
				self.log.debug("Recording canceled")
				return
			globalVars.app.hMainView.addLog(_("録画開始"), _("ユーザ：%(user)s、ムービーID：%(movie)s") % {"user": self.userName, "movie": self.movie}, self.source.friendlyName)
			globalVars.app.tb.setAlternateText(_("録画中"))
			# コメントの保存などは、ライブが終わるまで続くので、再試行のときには始め直さない
			if not onRecordCalled:
				self.source.onRecord(self.path, self.movie)
				onRecordCalled = True
			self.status = STATUS_RECORDING
			self.subProc = subprocess.Popen(" ".join(cmd), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, shell=False, encoding="utf-8", errors="replace", creationflags=subprocess.CREATE_NO_WINDOW)
			self.log.debug("Subprocess opened, pid: %d" % self.subProc.pid)
			# ffmpegの出力を別スレッドで読み続ける
			# 読まずに終了を待つと、パイプのバッファーが埋まった時点でffmpegが止まり、デッドロックになる
			output = deque(maxlen=OUTPUT_MAX_LINES)
			reader = threading.Thread(target=self.readOutput, args=(self.subProc.stdout, output), daemon=True)
			reader.start()
			self.subProc.wait()
			reader.join()
			self.status = STATUS_ERROR # ややこしいので成功が確認できない限りはエラー扱いにしておく
			self.log.info("saved: %s" % self.path)
			# 終了処理が行われていたらここで動作を止める
			if self._exitFlag:
				self.log.debug("recording canceled after saving a file")
				return
			returncode = self.subProc.returncode
			# 標準出力を取得
			result = "".join(output)
			clean = returncode == 0 and len(result) == 0
			if not clean:
				self.log.info("FFMPEG exited with code %d.\n%s" % (returncode, result))
			recorded = self.isRecorded()
			if recorded:
				recordedAny = True
			else:
				self.removeEmptyFile()
			# ffmpegは、録画の途中で配信が途切れても、終了コード0でエラーも出さずに終わることがある（#63）
			# そのため、終了コードや出力にかかわらず、ライブが続いているかどうかで再試行するかを決める
			live = self.source.isMovieLive(self.movie)
			if live is None:
				# ライブが続いているか分からない場合は、ffmpegがエラーなく終わっていれば、配信が終わったとみなす
				live = not clean
			if not live:
				self.log.info("End of recording")
				if recordedAny:
					# いずれかの回で録画できていれば成功とする
					# 最後の回のエラーは、ライブが終わったために起きたものと考えられる。詳細はログに記録してある
					self.status = STATUS_SUCCESS
				else:
					globalVars.app.hMainView.addLog(_("録画エラー"), (_("%sのライブを録画中にエラーが発生しました。") % self.userName) + self.getErrorDetail(returncode, result), self.source.friendlyName)
				break
			if recorded:
				failedRetries = 0
			else:
				failedRetries += 1
			if failedRetries > MAX_FAILED_RETRIES:
				self.log.info("Too many failed retries")
				globalVars.app.hMainView.addLog(_("録画エラー"), (_("%sのライブの録画を再試行しましたが、録画できなかったため中断しました。") % self.userName) + self.getErrorDetail(returncode, result), self.source.friendlyName)
				break
			globalVars.app.hMainView.addLog(_("録画エラー"), (_("%sのライブの録画が途切れたため、再度録画を開始します。") % self.userName) + self.getErrorDetail(returncode, result), self.source.friendlyName)
			# 待っている間に終了処理が行われたら、ここで動作を終了
			if self._exitEvent.wait(RETRY_INTERVAL_SEC):
				self.log.debug("Recording canceled while waiting to retry")
				return
		globalVars.app.hMainView.addLog(_("録画終了"), _("ユーザ：%(user)s、ムービーID：%(movie)s") % {"user": self.userName, "movie": self.movie}, self.source.friendlyName)
		if getRecordingUsers(self) == []:
			globalVars.app.tb.setAlternateText()

	def readOutput(self, stream, output):
		"""ffmpegの出力を、プロセスが終了するまで読み続ける

		:param stream: ffmpegの標準出力
		:type stream: io.TextIOWrapper
		:param output: 読み取った行を格納するdeque。上限を超えた古い行は捨てられる
		:type output: collections.deque
		"""
		for line in stream:
			output.append(line)
		stream.close()

	def isRecorded(self):
		"""今回のffmpegの実行で、保存先にデータが書き込まれたかどうかを返す

		ヘッダーだけのファイルを録画できたとみなさないように、MIN_RECORDED_SIZE以上かどうかで判断する
		"""
		try:
			return os.path.getsize(self.path) >= MIN_RECORDED_SIZE
		except OSError:
			return False

	def removeEmptyFile(self):
		"""保存先のファイルが0バイトなら削除する
		"""
		try:
			if os.path.getsize(self.path) == 0:
				os.remove(self.path)
				self.log.info("removed empty file: %s" % self.path)
		except OSError:
			pass

	def getErrorDetail(self, returncode, result):
		"""ログに表示するエラーの詳細を返す

		:param returncode: ffmpegの終了コード
		:type returncode: int
		:param result: ffmpegの出力
		:type result: str
		"""
		if result:
			return _("詳細：%s") % result
		if returncode != 0:
			return _("詳細：ffmpegの終了コード%d") % returncode
		return ""

	def shouldSkip(self):
		return self.skipExisting and os.path.exists(self.getOutputFile())

	def getTargetUser(self):
		"""誰のライブを録画中かを返す
		"""
		return self.userName

	def getStatus(self):
		return self.status

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
		self._exitEvent.set()
		if self.subProc:
			# 出力は録画スレッドが読んでいるため、communicate()は使わずに標準入力だけを操作する
			try:
				self.subProc.stdin.write("q")
				self.subProc.stdin.close()
			except (OSError, ValueError):
				# ffmpegがすでに終了している
				pass
			self.subProc.wait()

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
