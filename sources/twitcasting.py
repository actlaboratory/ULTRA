# twitcasting module for ULTRA

import base64
import json
import websocket
import wx
import globalVars
import requests
import constants
import implicitGrantManager
import views.auth
import simpleDialog
import webbrowser
import time
import os
import re
import recorder
from sources.base import SourceBase
from logging import getLogger
import threading
import csv
import datetime
import sys

class Twitcasting(SourceBase):
	def __init__(self):
		super().__init__()
		self.log = getLogger("%s.%s" %(constants.LOG_PREFIX, "sources.twitcasting"))
		self.initialized = 0
		self.running = False
		websocket.enableTrace(not hasattr(sys, "frozen"))
		self.enableMenu(False)
		self.userData = os.path.abspath(constants.TC_USER_DATA)
		self.tokenData = os.path.abspath(constants.AC_TWITCASTING)


	def initialize(self):
		"""アクセストークンの読み込み
		"""
		if self.initialized == 1:
			super().__init__()
		if not self.loadToken():
			self.log.info("Failed to load access token.")
			if not self.showTokenError():
				self.log.debug("User chose no from confirmation dialog.")
				return False
		self.initSocket()
		self.initialized = 1
		self.enableMenu(True)
		return True

	def enableMenu(self, mode):
		tc = ("TC_RECORD_ARCHIVE", "TC_RECORD_USER", "TC_MANAGE_USER")
		for i in tc:
			globalVars.app.hMainView.menu.EnableMenu(i, mode)

	def initSocket(self):
		"""ソケット通信を準備
		"""
		self.socket = websocket.WebSocketApp(constants.TC_WSS_URL, self.header, on_message=self.onMessage, on_error=self.onError, on_open=self.onOpen, on_close=self.onClose)
		self.log.info("WSS module loaded.")

	def onMessage(self, text):
		"""通知受信時
		"""
		self.loadUserList()
		obj = json.loads(text)
		if "movies" not in obj.keys():
			return
		for i in obj["movies"]:
			userId = i["broadcaster"]["id"]
			if userId in self.users.keys():
				globalVars.app.hMainView.addLog(_("配信開始"), i["broadcaster"]["screen_id"], _("ツイキャス"))
				globalVars.app.notificationHandler.notify(self, i["broadcaster"]["screen_id"], i["movie"]["link"], i["movie"]["hls_url"], i["movie"]["created"], self.getConfig(userId), i["movie"]["id"])
				if self.users[userId]["user"] != i["broadcaster"]["screen_id"]:
					globalVars.app.hMainView.addLog(_("ユーザ名変更"), _("「%(old)s」→「%(new)s」") %{"old": self.users[userId]["user"], "new": i["broadcaster"]["screen_id"]}, _("ツイキャス"))
					self.users[userId]["user"] = i["broadcaster"]["screen_id"]
				if self.users[userId]["name"] != i["broadcaster"]["name"]:
					globalVars.app.hMainView.addLog(_("表示名名変更"), _("「%(old)s」→「%(new)s」") %{"old": self.users[userId]["name"], "new": i["broadcaster"]["name"]}, _("ツイキャス"))
					self.users[userId]["name"] = i["broadcaster"]["name"]
		rm = []
		for i in self.users:
			if "remove" in self.users[i].keys() and (time.time() - self.users[i]["remove"]) >= 0:
				rm.append(i)
		for i in rm:
			self.users.pop(i)
		self.saveUserList()

	def onError(self, error):
		"""ソケット通信中にエラーが起きた
		"""
		import traceback
		self.log.error("WSS Error:%s" %list(traceback.TracebackException.from_exception(error).format()))
		time.sleep(3)
		if type(error) in (ConnectionResetError, websocket._exceptions.WebSocketAddressException):
			self.socket.close()
			self.initSocket()
			self.socket.run_forever()

	def onOpen(self):
		"""ソケット通信が始まった
		"""
		self.running = True
		globalVars.app.hMainView.menu.CheckMenu("TC_ENABLE", True)

	def onClose(self):
		"""ソケット通信が切断された
		"""
		self.running = False

	def loadToken(self):
		"""トークン情報をファイルから読み込み
		"""
		try:
			with open(self.tokenData, "rb") as f:
				token = base64.b64decode(f.read()).decode()
		except:
			return False
		self.token = token
		self.setHeader()
		return self.verifyCredentials()

	def verifyCredentials(self):
		"""トークンが正しく機能しているかどうかを確認する
		"""
		result = requests.get("https://apiv2.twitcasting.tv/verify_credentials", headers = self.header)
		return result.status_code == 200

	def setToken(self):
		"""新しいトークンをセットする
		"""
		manager = implicitGrantManager.ImplicitGrantManager(constants.TC_CID, constants.TC_URL, constants.TC_PORT)
		l="ja"
		try:
			l=globalVars.app.config["general"]["language"].split("_")[0].lower()
		except:
			pass#end うまく読めなかったら ja を採用
		#end except
		manager.setMessage(
			lang=l,
			success=_("認証に成功しました。このウィンドウを閉じて、アプリケーションに戻ってください。"),
			failed=_("認証に失敗しました。もう一度お試しください。"),
			transfer=_("しばらくしても画面が切り替わらない場合は、別のブラウザでお試しください。")
		)
		webbrowser.open(manager.getUrl())
		d = views.auth.waitingDialog()
		d.Initialize()
		d.Show(False)
		while True:
			time.sleep(0.01)
			wx.YieldIfNeeded()
			if manager.getToken():
				d.Destroy()
				break
			if d.canceled == 1 or manager.getToken() == "":
				simpleDialog.dialog(_("処理結果"), _("キャンセルされました。"))
				manager.shutdown()
				d.Destroy()
				return False
		token = manager.getToken()["access_token"]
		with open(self.tokenData, "wb") as f:
			f.write(base64.b64encode(token.encode()))
		simpleDialog.dialog(_("処理結果"), _("認証が完了しました。"))
		self.loadToken()
		return True

	def setHeader(self):
		"""ツイキャスAPIと通信する際のヘッダ情報を準備する
		"""
		self.header = {
			"X-Api-Version": "2.0",
			"Authorization": "Bearer " + self.token
		}

	def loadUserList(self):
		"""通知させたいユーザの情報を読み込む
		"""
		try:
			with open(self.userData, "r", encoding="utf-8") as f:
				self.users = json.load(f)
		except FileNotFoundError:
			self.users = {}
			self.saveUserList()

	def saveUserList(self):
		"""ユーザリストをファイルに保存
		"""
		try:
			with open(self.userData, "w", encoding="utf-8") as f:
				json.dump(self.users, f, ensure_ascii=False)
		except:
			import traceback
			self.log.error("Failed to save users.dat.\n" + traceback.format_exc())
			simpleDialog.errorDialog(_("ユーザ情報の保存に失敗しました。"))

	def run(self):
		"""新着ライブの監視を開始
		"""
		if self.initialized == 0 and not self.initialize():
			return
		self.socket.run_forever()

	def getUserInfo(self, user):
		"""ユーザ情報を取得

		:param user: ユーザ名またはユーザID
		:type user: str
		"""
		req = requests.get("https://apiv2.twitcasting.tv/users/%s" %user, headers=self.header)
		if req.status_code != 200:
			if req.json()["error"]["code"] == 1000:
				self.showTokenError()
				return
			elif req.status_code == 404:
				simpleDialog.errorDialog(_("指定したユーザが見つかりません。"))
				return
			else:
				self.showError(req.json()["error"]["code"])
				return
		return req.json()

	def getCurrentLive(self, user):
		"""ユーザが現在配信中のライブ情報を取得

		:param user: ユーザ名またはユーザID
		:type user: str
		"""
		req = requests.get("https://apiv2.twitcasting.tv/users/%s/current_live" %user, headers=self.header)
		if req.status_code != 200:
			if req.json()["error"]["code"] == 1000:
				self.showTokenError()
				return
			elif req.status_code == 404:
				return
			else:
				self.showError(req.json()["error"]["code"])
				return
		return req.json()

	def getUserIdFromScreenId(self, screenId):
		"""ユーザ名から数値のIDを取得

		:param screenId: ユーザ名
		:type screenId: str
		"""
		result = self.getUserInfo(screenId)
		if result == None:
			return constants.NOT_FOUND
		return result["user"]["id"]

	def exit(self):
		"""新着ライブの監視を終了する
		"""
		if hasattr(self, "socket"):
			self.socket.close()
		self.enableMenu(False)

	def getConfig(self, user):
		"""通知方法の設定を取得。ユーザ専用の設定があればそれを、なければデフォルト値を返す。
		:param user: ユーザID。self.usersの主キー。
		:type user: str
		"""
		items = (
			"baloon",
			"record",
			"openBrowser",
			"sound",
		)
		config = {}
		if self.users[user]["specific"]:
			for i in items:
				config[i] = self.users[user][i]
			config["soundFile"] = self.users[user]["soundFile"]
		else:
			for i in items:
				config[i] = globalVars.app.config.getboolean("notification", i, False)
			config["soundFile"] = globalVars.app.config["notification"]["soundFile"]
		return config

	def downloadArchive(self, url):
		"""過去ライブをダウンロード

		:param url: 再生ページのURL
		:type url: str
		"""
		stream = self.getStreamFromUrl(url)
		if stream == None:
			return
		movieInfo = self.getMovieInfoFromUrl(url)
		if movieInfo == None:
			return
		r = recorder.Recorder(self, stream, movieInfo["broadcaster"]["screen_id"], movieInfo["movie"]["created"], movieInfo["movie"]["id"])
		r.start()

	def getStreamFromUrl(self, url):
		"""再生ページのURLからストリーミングのURLを得る

		:param url: 再生ページのURL
		:type url: str
		"""
		try:
			req = requests.get(url)
		except:
			self.showNotFoundError()
			return
		if req.status_code == 404:
			self.showNotFoundError()
			return
		body = req.text
		try:
			start = re.search("https:\\\/\\\/dl\d\d\.twitcasting\.tv\\\/tc\.vod\\\/", body).start()
		except:
			self.showNotFoundError()
			return
		end = body.find("\"", start)
		stream = body[start:end]
		stream = stream.replace("\\/", "/")
		return stream

	def getMovieInfoFromUrl(self, url):
		"""ライブページのURLからムービー情報を取得

		:param url: 再生ページのURL
		:type url: str
		"""
		if self.initialized == 0 and not self.initialize():
			return
		id = url[url.rfind("/") + 1:]
		req = requests.get("https://apiv2.twitcasting.tv/movies/%s" %id, headers=self.header)
		if req.status_code != 200:
			if req.status_code == 404:
				self.showNotFoundError()
				return
			elif req.json()["error"]["code"] == 1000:
				self.showTokenError()
				return
			else:
				self.showError(req.json()["error"]["code"])
				return
		return req.json()

	# 各種エラーを表示する
	def showTokenError(self):
		"""「有効なトークンがありません」というエラーを出す。「はい」を選ぶと認証開始。
		"""
		d = simpleDialog.yesNoDialog(_("トークンエラー"), _("利用可能なアクセストークンが見つかりません。ブラウザを起動し、認証作業を行いますか？"))
		if d == wx.ID_NO:
			return False
		if not self.setToken():
			return False
		return True

	def showNotFoundError(self):
		"""過去ライブのダウンロードを試みた際、失敗したことを通知するメッセージを出す
		"""
		simpleDialog.errorDialog(_("録画に失敗しました。録画が公開されていること、入力したURLに誤りがないことを確認してください。"))

	def showError(self, code):
		"""ツイキャスAPIが返すエラーコードに応じてメッセージを出す。Invalid TokenについてはshowTokenError()を使用することを想定しているため未実装。

		:param code: エラーコード
		:type code: int
		"""
		if code == 2000:
			simpleDialog.errorDialog(_("ツイキャスAPIの実行回数が上限に達しました。しばらくたってから、再度実行してください。"))
		elif code == 500:
			simpleDialog.errorDialog(_("ツイキャスAPIが500エラーを返しました。しばらく待ってから、再度接続してください。"))
		elif code == 2001:
			simpleDialog.errorDialog(_("現在ツイキャスとの連携機能を使用できません。開発者に連絡してください。"))
		else:
			detail = {
				1001: "Validation Error",
				1002: "Invalid WebHook URL",
				2002: "Protected",
				2003: "Duplicate",
				2004: "Too Many Comments",
				2005: "Out Of Scope",
				2006: "Email Unverified",
				400: "Bad Request",
				403: "Forbidden",
			}
			simpleDialog.errorDialog(_("ツイキャスAPIとの通信中にエラーが発生しました。詳細：%s") %(detail[code]))

	def onRecord(self, path, movieId):
		if globalVars.app.config.getboolean("twitcasting", "saveComments", False):
			c = CommentGetter(self, os.path.splitext(path)[0] + ".txt", movieId)
			c.start()

	def addUser(self, userName, temporary=False, specific=False, baloon=None, record=None, openBrowser=None, sound=None, soundFile=None, id=None):
		"""ユーザーを追加する。

		:param userName: ユーザ名
		:type userName: str
		:param temporary: 一定時間経過後に登録を削除するかどうか
		:type temporary: bool
		:param specific: 専用の通知条件を設定するかどうか
		:type specific: bool
		:param baloon: バルーン通知の有無。Noneにすると規定値を読み込む。
		:type baloon: bool
		:param record: 録画するかどうか。Noneにすると規定値を読み込む。
		:type record: bool
		:param openBrowser: ブラウザでライブを開くかどうか。Noneにすると規定値を読み込む。
		:type openBrowser: bool
		:param sound: サウンド再生の有無。Noneにすると規定値を読み込む。
		:type sound: bool
		:param soundFile: 再生するサウンドファイル。Noneにすると規定値を読み込む。
		:type soundFile: None
		:param id: ユーザのID。特別な事情がない限り、このパラメータは指定しなくて良い。
		:type id: str
		"""
		self.loadUserList()
		if id == None:
			id = self.getUserIdFromScreenId(userName)
			if id == constants.NOT_FOUND:
				return
		if baloon == None:
			baloon = globalVars.app.config.getboolean("notification", "baloon", True)
		if record == None:
			record = globalVars.app.config.getboolean("notification", "record", True)
		if openBrowser == None:
			openBrowser = globalVars.app.config.getboolean("notification", "openBrowser", False)
		if sound == None:
			sound = globalVars.app.config.getboolean("notification", "sound", False)
		if soundFile == None:
			soundFile = globalVars.app.config["notification"]["soundFile"]
		ret = {
			"user": userName,
			"specific": specific,
			"baloon": baloon,
			"record": record,
			"openBrowser": openBrowser,
			"sound": sound,
			"soundFile": soundFile,
		}
		if temporary:
			ret["remove"] = time.time() + 14400
		self.users[id] = ret
		self.saveUserList()

	def record(self, userName):
		"""指定したユーザのライブを録画。

		:param userName: ユーザ名
		:type userName: str
		"""
		userInfo = self.getUserInfo(userName)
		if userInfo == None:
			return
		self.addUser(userInfo["user"]["screen_id"], True, True, False, True, False, False, "", userInfo["user"]["id"])
		if userInfo["user"]["is_live"]:
			movie = self.getCurrentLive(userName)
			if movie == None:
				return
			r = recorder.Recorder(self, movie["movie"]["hls_url"], movie["broadcaster"]["screen_id"], movie["movie"]["created"], movie["movie"]["id"])
			r.start()

class CommentGetter(threading.Thread):
	"""コメントの取得と保存
	"""
	def __init__(self, tc, path, movie):
		"""コンストラクタ

		:param tc: TwitCastingオブジェクト
		:type tc: TwitCasting
		:param path: コメントの保存先
		:type path: str
		:param movie: movie ID
		:type movie: str
		"""
		super().__init__()
		self.path = path
		self.comments = []
		self.lastCommentId = ""
		self.movie = movie
		self.tc = tc
		self.hasError = 0

	def run(self):
		if not self.getAllComments():
			return
		globalVars.app.hMainView.addLog(_("コメント保存"), _("コメントの保存を開始します。"), _("ツイキャス"))
		self.saveComment()
		while self.isLive():
			if self.hasError == 1:
				break
			time.sleep(10)
			tmp = self.getComments(slice_id=self.lastCommentId)
			self.fixCommentDuplication(tmp, self.comments)
			self.comments = tmp + self.comments
			if len(self.comments) > 0:
				self.lastCommentId = self.comments[0]["id"]
			self.saveComment()
		globalVars.app.hMainView.addLog(_("コメント保存"), _("コメントの保存を終了しました。。"), _("ツイキャス"))

	def saveComment(self):
		"""コメントをファイルに保存する
		"""
		result = []
		for i in self.comments:
			timestamp = datetime.datetime.fromtimestamp(i["created"])
			timestamp = timestamp.strftime("%Y/%m/%d %H:%M:%S")
			result.append([
				i["from_user"]["name"],
				i["message"],
				timestamp,
			])
		result.reverse()
		with open(self.path, "w", encoding="utf-8") as f:
			writer = csv.writer(f, delimiter="\t")
			writer.writerows(result)

	def getAllComments(self):
		"""現時点で届いているコメントを全て取得する。
		"""
		all = []
		tmp = self.getComments()
		if self.hasError == 1:
			return False
		self.fixCommentDuplication(tmp, all)
		while len(tmp) > 0:
			all = all + tmp
			tmp = self.getComments(offset=len(all))
			if self.hasError == 1:
				return False
			self.fixCommentDuplication(tmp, all)
		self.comments = all
		if len(self.comments) > 0:
			self.lastCommentId = self.comments[0]["id"]
		return True

	def fixCommentDuplication(self, new, base):
		"""コメントの重複回避
		"""
		rm = []
		for i in range(len(new)):
			if new[i] in base:
				rm.append(i)
		rm.reverse()
		for i in rm:
			del new[i]

	def getComments(self, offset=0, limit=50, slice_id=""):
		"""ツイキャスAPIにアクセスしてコメントを取得する。各パラメータの使用方法はツイキャスAPIに準ずる。
		"""
		param = {
			"offset": offset,
			"limit": limit,
			"slice_id": slice_id,
		}
		try:
			result = requests.get("https://apiv2.twitcasting.tv/movies/%s/comments" %self.movie, param, headers=self.tc.header)
		except requests.RequestException:
			self.hasError = 1
			return []
		if result.status_code != 200:
			if result.json()["error"]["code"] == 1000:
				self.tc.showTokenError()
			elif result.status_code == 404:
				return []
			else:
				self.tc.showError(result.json()["error"]["code"])
			return []
		dict = result.json()
		return dict["comments"]

	def isLive(self):
		"""配信中かどうかを調べる
		"""
		try:
			req = requests.get("https://apiv2.twitcasting.tv/movies/%s" %self.movie, headers=self.tc.header)
		except requests.RequestException:
			self.hasError = 1
			return False
		if req.status_code != 200:
			if req.json()["error"]["code"] == 1000:
				return self.tc.showTokenError()
			elif req.status_code == 404:
				return False
			else:
				self.tc.showError(req.json()["error"]["code"])
			return False
		return req.json()["movie"]["is_live"]
