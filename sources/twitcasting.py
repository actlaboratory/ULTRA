# twitcasting module for ULTRA

import base64
import json
import traceback
import twitterService
import views.SimpleInputDialog
from copy import deepcopy
import wx.adv
import errorCodes
import websocket
import pickle
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
import winsound

# DEBUG
# 0:何もしない、1:ツイキャスのリアルタイムAPIが返した内容をreceived.txtに保存する
DEBUG = 0
DEBUG_FILE = "received.txt"

tlock = threading.Lock()

class Twitcasting(SourceBase):
	name = "TwitCasting"
	friendlyName = _("ツイキャス")
	index = 0

	def __init__(self):
		super().__init__()
		self.log = getLogger("%s.%s" %(constants.LOG_PREFIX, "sources.twitcasting"))
		self.initialized = 0
		self.running = False
		self.shouldExit = False
		websocket.enableTrace(not hasattr(sys, "frozen"))
		self.enableMenu(False)
		globalVars.app.hMainView.menu.CheckMenu("TC_SAVE_COMMENTS", globalVars.app.config.getboolean("twitcasting", "saveComments", False))
		self.setStatus(_("未接続"))
		self.debug = not(hasattr(sys, "frozen")) and DEBUG
		if self.debug:
			with open(DEBUG_FILE, "w"): pass

	def initialize(self):
		"""アクセストークンの読み込み
		"""
		if self.initialized == 1:
			self.initThread()
		self.netflag = 0
		if not self.loadToken():
			if self.netflag:
				self.netflag = 0
				return False
			self.log.info("Failed to load access token.")
			if not self.showTokenError():
				self.log.debug("User chose no from confirmation dialog.")
				return False
		self.initSocket()
		self.checkTokenExpires(True)
		self.initialized = 1
		self.enableMenu(True)
		return True

	def checkTokenExpires(self, startup=False):
		"""トークンの有効期限がもうすぐ切れる、あるいは切れたことを通知

		:param startup: Trueにすると、ダイアログを表示。Falseにすると、トースト通知を表示。
		:type startup: bool
		"""
		with open(constants.AC_TWITCASTING, "rb") as f:
			d = pickle.load(f)
		if self.expires - time.time() < 0:
			if startup:
				simpleDialog.dialog(_("アクセストークンの有効期限が切れています"), _("本ソフトの使用を続けるには、アクセストークンを再度設定する必要があります。"))
			else:
				b = wx.adv.NotificationMessage(constants.APP_NAME, _("アクセストークンの有効期限が切れています。本ソフトの使用を続けるには、アクセストークンを再度設定する必要があります。"))
				b.Show()
				b.Close()
		elif time.time() >d["next"]:
			if startup:
				simpleDialog.dialog(_("アクセストークンの有効期限が近づいています"), _("本ソフトの使用を続けるには、アクセストークンを再度設定する必要があります。"))
			else:
				b = wx.adv.NotificationMessage(constants.APP_NAME, _("アクセストークンの有効期限が近づいています。本ソフトの使用を続けるには、アクセストークンを再度設定する必要があります。"))
				b.Show()
				b.Close()
			if d["expires"] - time.time() > 86400:
				d["next"] = time.time() + 86400
			else:
				d["next"] = time.time() + 3600
			with open(constants.AC_TWITCASTING, "wb") as f:
				pickle.dump(d, f)

	def enableMenu(self, mode):
		tc = ("TC_SAVE_COMMENTS", "TC_UPDATE_USER", "TC_RECORD_ARCHIVE", "TC_RECORD_USER", "TC_SET_TOKEN", "TC_MANAGE_USER")
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
		if self.debug:
			with open(DEBUG_FILE, "a", encoding="utf-8") as f:
				timestamp = datetime.datetime.now().strftime("%Y/%m/%d %H:%M:%S")
				f.write(timestamp + "\n")
				data = json.loads(text)
				data = json.dumps(data, indent="\t", ensure_ascii=False)
				f.write(data + "\n")
				f.write("----------" + "\n")
		self.loadUserList()
		obj = json.loads(text)
		if "movies" not in obj.keys() or obj["movies"] == None:
			return
		for i in obj["movies"]:
			if not i["movie"]["is_live"] or i["movie"]["hls_url"] == "":
				continue
			userId = i["broadcaster"]["id"]
			if userId in self.users.keys():
				globalVars.app.hMainView.addLog(_("配信開始"), i["broadcaster"]["screen_id"], self.friendlyName)
				globalVars.app.notificationHandler.notify(self, i["broadcaster"]["screen_id"], i["movie"]["link"], i["movie"]["hls_url"], i["movie"]["created"], self.getConfig(userId), i["movie"]["id"])
				self.updateUserInfo(userId, i["broadcaster"]["screen_id"], i["broadcaster"]["name"])
		rm = []
		for i in self.users:
			if "remove" in self.users[i].keys() and (self.users[i]["remove"] - time.time()) < 0:
				rm.append(i)
				globalVars.app.hMainView.addLog(_("録画対象の削除"), _("%sのライブを、録画対象から削除しました。") %self.users[i]["user"])
				b = wx.adv.NotificationMessage(constants.APP_NAME, _("%sのライブを、録画対象から削除しました。") %self.users[i]["user"])
				b.Show()
				b.Close()
		rm.reverse()
		self.removeUsers(rm)
		self.checkTokenExpires()

	def removeUsers(self, rm):
		with tlock:
			self.loadUserList()
			for i in rm:
				self.users.pop(i)
			self.saveUserList()

	def updateUserInfo(self, id, user, name):
		"""ユーザ情報を更新

		:param id: 数値のID
		:type id: str
		:param user: ユーザ名
		:type user: str
		:param name: 名前
		:type name: str
		"""
		with tlock:
			self.loadUserList()
			if user != self.users[id]["user"]:
				globalVars.app.hMainView.addLog(_("ユーザ名変更"), _("「%(old)s」→「%(new)s」") %{"old": self.users[id]["user"], "new": user}, self.friendlyName)
				self.users[id]["user"] = user
			if name != self.users[id]["name"]:
				globalVars.app.hMainView.addLog(_("名前変更"), _("「%(old)s」→「%(new)s」") %{"old": self.users[id]["name"], "new": name}, self.friendlyName)
				self.users[id]["name"] = name
			self.saveUserList()

	def updateUser(self):
		u = UserChecker(self)
		u.start()

	def onError(self, error):
		"""ソケット通信中にエラーが起きた
		"""
		self.log.error("WSS Error:%s" %list(traceback.TracebackException.from_exception(error).format()))
		time.sleep(3)
		if type(error) in (ConnectionResetError, websocket._exceptions.WebSocketAddressException):
			self.shouldExit = True
			self.socket.close()
			globalVars.app.hMainView.addLog(_("切断"), _("インターネット接続が切断されました。再試行します。"), self.friendlyName)
			self.setStatus(_("接続試行中"))
			self.initSocket()
			self.socket.run_forever()

	def onOpen(self):
		"""ソケット通信が始まった
		"""
		self.running = True
		globalVars.app.hMainView.addLog(_("接続完了"), _("新着ライブの監視を開始しました。"), self.friendlyName)
		globalVars.app.hMainView.menu.CheckMenu("TC_ENABLE", True)
		globalVars.app.hMainView.menu.EnableMenu("HIDE")
		self.setStatus(_("接続済み"))
		self.enableMenu(True)

	def onClose(self):
		"""ソケット通信が切断された
		"""
		self.running = False
		globalVars.app.hMainView.menu.EnableMenu("HIDE", False)
		globalVars.app.hMainView.addLog(_("切断"), _("ツイキャスとの接続を切断しました。"), self.friendlyName)
		self.setStatus(_("未接続"))
		self.enableMenu(False)
		globalVars.app.hMainView.menu.CheckMenu("TC_ENABLE", False)
		if not self.shouldExit:
			globalVars.app.hMainView.addLog(_("再接続"), _("ツイキャスとの接続が切断されたため、再度接続します。"), self.friendlyName)
			self.log.debug("Connection does not closed by user.")
			self.initSocket()
			self.socket.run_forever()
		self.shouldExit = False

	def loadToken(self):
		"""トークン情報をファイルから読み込み
		"""
		try:
			with open(constants.AC_TWITCASTING, "rb") as f:
				data = pickle.load(f)
		except:
			return False
		self.token = base64.b64decode(data["token"]).decode()
		self.expires = data["expires"]
		self.setHeader()
		return self.verifyCredentials()

	def verifyCredentials(self, init=True):
		"""トークンが正しく機能しているかどうかを確認する
		"""
		try:
			result = requests.get("https://apiv2.twitcasting.tv/verify_credentials", headers = self.header)
		except requests.RequestException as e:
			if init:
				self.log.error(traceback.format_exc())
				simpleDialog.errorDialog(_("インターネット接続に失敗しました。現在ツイキャスとの連携機能を使用できません。"))
				self.netflag = 1
			return False
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
		d.Initialize(_("アカウントの追加"))
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
		token = manager.getToken()
		data = {
			"token": base64.b64encode(token["access_token"].encode()),
			"expires": token["expires_at"],
			"next": token["expires_at"] - constants.TOKEN_EXPIRE_MAX,
		}
		with open(constants.AC_TWITCASTING, "wb") as f:
			pickle.dump(data, f)
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
			with open(constants.TC_USER_DATA, "r", encoding="utf-8") as f:
				self.users = json.load(f)
		except FileNotFoundError:
			self.users = {}
			self.saveUserList()

	def saveUserList(self):
		"""ユーザリストをファイルに保存
		"""
		if hasattr(sys, "frozen"):
			indent = None
		else:
			indent = "\t"
		try:
			with open(constants.TC_USER_DATA, "w", encoding="utf-8") as f:
				json.dump(self.users, f, ensure_ascii=False, indent=indent)
		except:
			self.log.error("Failed to save users.dat.\n" + traceback.format_exc())
			simpleDialog.errorDialog(_("ユーザ情報の保存に失敗しました。"))

	def run(self):
		"""新着ライブの監視を開始
		"""
		if self.initialized == 0 and not self.initialize():
			return
		proxyUrl, proxyPort = globalVars.app.getProxyInfo()
		self.socket.run_forever(http_proxy_host=proxyUrl, http_proxy_port=proxyPort)

	def getUserInfo(self, user, showNotFound=True):
		"""ユーザ情報を取得

		:param user: ユーザ名またはユーザID
		:type user: str
		:param showNotFound: 見つからなかったときにエラーを表示
		:type showNotFound: bool
		"""
		try:
			req = requests.get("https://apiv2.twitcasting.tv/users/%s" %user, headers=self.header)
		except requests.RequestException as e:
			self.log.error(traceback.format_exc())
			return
		if req.status_code != 200:
			if req.json()["error"]["code"] == 1000:
				self.showTokenError()
				return
			elif req.status_code == 404:
				if showNotFound:
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
		try:
			req = requests.get("https://apiv2.twitcasting.tv/users/%s/current_live" %user, headers=self.header)
		except requests.RequestException as e:
			self.log.error(traceback.format_exc())
			return
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
		self.log.debug("Exit button pressed.")
		self.shouldExit = True
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

	def downloadArchive(self, url, join=False, skipExisting=False):
		"""過去ライブをダウンロード

		:param url: 再生ページのURL
		:type url: str
		"""
		movieInfo = self.getMovieInfoFromUrl(url)
		if movieInfo == None:
			return
		stream = self.getStreamFromUrl(url, movieInfo["movie"]["is_protected"])
		if stream == None:
			return
		r = recorder.Recorder(self, stream, movieInfo["broadcaster"]["screen_id"], movieInfo["movie"]["created"], movieInfo["movie"]["id"],header="Origin: https://twitcasting.tv", skipExisting=skipExisting)
		if r.shouldSkip():
			return errorCodes.RECORD_SKIPPED
		r.start()
		if join:
			r.join()

	def getStreamFromUrl(self, url, protected=False):
		"""再生ページのURLからストリーミングのURLを得る

		:param url: 再生ページのURL
		:type url: str
		:param protected: 合い言葉が必要かどうか
		:type protected: bool
		"""
		session = requests.session()
		try:
			req = session.get(url,headers={
				"Origin": "https://twitcasting.tv",
				"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
			})
		except:
			self.showNotFoundError()
			return
		if req.status_code == 404:
			self.showNotFoundError()
			return
		body = req.text
		if protected:
			d = views.SimpleInputDialog.Dialog(_("合い言葉の入力"), _("合い言葉"))
			d.Initialize()
			if d.Show() == wx.ID_CANCEL:
				return
			pw = d.GetData()
			try:
				req = session.post(url, "password=%s" %pw, headers={
					"Content-Type": "application/x-www-form-urlencoded",
					"Origin": "https://twitcasting.tv",
					"User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
				})
			except:
				self.showNotFoundError()
				return
			if req.status_code == 404:
				self.showNotFoundError()
				return
			body = req.text
		try:
			start = re.search("https:\\\/\\\/dl\d+\.twitcasting\.tv\\\/tc\.vod", body).start()
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
		try:
			req = requests.get("https://apiv2.twitcasting.tv/movies/%s" %id, headers=self.header)
		except requests.RequestException as e:
			self.log.error(traceback.format_exc())
			return
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

	def getMovieInfo(self, id):
		"""ムービー情報を取得

		:param id: ムービーID
		:type id: str
		"""
		if self.initialized == 0 and not self.initialize():
			return
		try:
			req = requests.get("https://apiv2.twitcasting.tv/movies/%s" %id, headers=self.header)
		except requests.RequestException as e:
			self.log.error(traceback.format_exc())
			return
		if req.status_code != 200:
			if req.status_code == 404:
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
		winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
		d = simpleDialog.yesNoDialog(_("アクセストークンが見つかりません"), _("利用可能なアクセストークンが見つかりません。ブラウザを起動し、認証作業を行いますか？"))
		if d == wx.ID_NO:
			return False
		if not self.setToken():
			return False
		return True

	def showNotFoundError(self):
		"""過去ライブのダウンロードを試みた際、失敗したことを通知するメッセージを出す
		"""
		simpleDialog.errorDialog(_("録画に失敗しました。録画が公開されていること、入力したURLに誤りがないことを確認してください。合い言葉を入力した場合は、入力した合い言葉に誤りがないことを確認してください。"))

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

	def onRecordError(self, movie):
		movieInfo = self.getMovieInfo(movie)
		if movieInfo == None:
			if self.verifyCredentials(False):
				# ネットには繋がっているがムービー情報が取れない、つまりライブは終わっている
				return False
			# ネットには繋がっていない。ライブがまだ続いている可能性もある。
			return True
		return movieInfo["movie"]["is_live"]

	def record(self, userName):
		"""指定したユーザのライブを録画。

		:param userName: ユーザ名
		:type userName: str
		"""
		self.loadUserList()
		userInfo = self.getUserInfo(userName)
		if userInfo == None:
			return
		if userInfo["user"]["id"] in self.users.keys():
			if userInfo["user"]["screen_id"] not in recorder.getRecordingUsers() and userInfo["user"]["is_live"]:
				movie = self.getCurrentLive(userInfo["user"]["screen_id"])
				if movie == None:
					return
				r = recorder.Recorder(self, movie["movie"]["hls_url"], movie["broadcaster"]["screen_id"], movie["movie"]["created"], movie["movie"]["id"])
				r.start()
				return
			simpleDialog.errorDialog(_("このユーザはすでに登録されています。"))
			return
		if userInfo["user"]["screen_id"] in recorder.getRecordingUsers():
			simpleDialog.errorDialog(_("このユーザのライブはすでに録画中です。"))
			return
		self.users[userInfo["user"]["id"]] = {
			"user": userInfo["user"]["screen_id"],
			"name": userInfo["user"]["name"],
			"specific": True,
			"baloon": False,
			"record": True,
			"openBrowser": False,
			"sound": False,
			"soundFile": "",
			"remove": (datetime.datetime.now() + datetime.timedelta(hours=10)).timestamp(),
		}
		self.saveUserList()
		globalVars.app.hMainView.addLog(_("ユーザ名を指定して録画"), _("%sを、録画対象として追加しました。この登録は一定時間経過後に自動で削除されます。") %userInfo["user"]["screen_id"])
		if userInfo["user"]["is_live"]:
			movie = self.getCurrentLive(userName)
			if movie == None:
				return
			r = recorder.Recorder(self, movie["movie"]["hls_url"], movie["broadcaster"]["screen_id"], movie["movie"]["created"], movie["movie"]["id"])
			r.start()

	def recordAll(self, user):
		"""過去ライブの一括録画

		:param user: ユーザ名
		:type user: str
		"""
		target = self.getUserIdFromScreenId(user)
		if target == constants.NOT_FOUND:
			return
		ArchiveDownloader(self, target).start()

	def addUsersFromTwitter(self):
		"""Twitterでフォローしているユーザを一括追加
		"""
		token = twitterService.getToken()
		if token == None:
			return
		d = views.SimpleInputDialog.Dialog(_("対象ユーザの指定"), _("フォロー中のユーザを取得するアカウントの@からはじまるアカウント名を入力してください。\n後悔アカウント、認証に用いたアカウント、\nまたは認証に用いたアカウントがフォローしている非公開アカウントを指定できます。"), validationPattern="^(@?[a-zA-Z0-9_]*)$")
		d.Initialize()
		if d.Show() == wx.ID_CANCEL:
			return
		target = re.sub("@?(.*)","\\1", d.GetValue())
		self.log.debug("target=%s" % target)
		users = twitterService.getFollowList(token, target)
		if users == None:
			return
		t = TwitterHelper(self, users)
		t.start()

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
		self.log = getLogger("%s.%s" %(constants.LOG_PREFIX, "sources.twitcasting.commentGetter"))

	def run(self):
		if not self.getAllComments():
			return
		movieInfo = self.tc.getMovieInfo(self.movie)
		if movieInfo == None:
			self.log.info("Failed to get movie info(ID:%s" %self.movie)
			return
		self.userName = movieInfo["broadcaster"]["screen_id"]
		globalVars.app.hMainView.addLog(_("コメント保存開始"), _("ユーザ：%(user)s、ムービーID：%(movie)s") %{"user": self.userName, "movie": self.movie}, self.tc.friendlyName)
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
		globalVars.app.hMainView.addLog(_("コメント保存終了"), _("ユーザ：%(user)s、ムービーID：%(movie)s") %{"user": self.userName, "movie": self.movie}, self.tc.friendlyName)

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

class UserChecker(threading.Thread):
	"""ユーザ情報を更新する
	"""
	def __init__(self, tc):
		"""コンストラクタ

		:param tc: TwitCastingオブジェクト
		:type tc: TwitCasting
		"""
		super().__init__(daemon=True)
		self.tc = tc
		self.tc.loadUserList()
		self.users = deepcopy(tuple(self.tc.users.keys()))

	def run(self):
		globalVars.app.hMainView.menu.EnableMenu("TC_MANAGE_USER", False)
		globalVars.app.hMainView.addLog(_("ユーザ情報の更新"), _("ユーザ情報の更新を開始します。"), self.tc.friendlyName)
		for i in self.users:
			if i in self.tc.users:
				globalVars.app.hMainView.addLog(_("ユーザ情報の更新"), _("%sの情報を取得しています。") %self.tc.users[i]["user"], self.tc.friendlyName)
				userInfo = self.tc.getUserInfo(i, False)
				if userInfo:
					self.tc.updateUserInfo(i, userInfo["user"]["screen_id"], userInfo["user"]["name"])
			time.sleep(60)
		globalVars.app.hMainView.addLog(_("ユーザ情報の更新"), _("ユーザ情報の更新が終了しました。"), self.tc.friendlyName)
		globalVars.app.hMainView.menu.EnableMenu("TC_MANAGE_USER", True)

class TwitterHelper(threading.Thread):
	def __init__(self, tc, users):
		super().__init__(daemon=True)
		self.tc = tc
		self.log = getLogger("%s.twitterHelper" %constants.LOG_PREFIX)
		self.users = users

	def showLog(self, message):
		"""動作履歴にメッセージを表示

		:param message: メッセージ本文
		:type message: str
		"""
		globalVars.app.hMainView.addLog(_("一括追加"), message, self.tc.friendlyName)

	def run(self):
		globalVars.app.hMainView.menu.EnableMenu("TC_MANAGE_USER", False)
		self.showLog(_("処理を開始します。"))
		for i in self.users:
			userInfo = self.tc.getUserInfo(i, False)
			if userInfo != None:
				userId = userInfo["user"]["id"]
				self.tc.loadUserList()
				if userId not in self.tc.users.keys():
					with tlock:
						self.tc.loadUserList()
						self.tc.users[userId] = {
							"user": userInfo["user"]["screen_id"],
							"name": userInfo["user"]["name"],
							"specific": False,
							"baloon": globalVars.app.config.getboolean("notification", "baloon", True),
							"record": globalVars.app.config.getboolean("notification", "record", True),
							"openBrowser": globalVars.app.config.getboolean("notification", "openBrowser", False),
							"sound": globalVars.app.config.getboolean("notification", "sound", False),
							"soundFile": globalVars.app.config["notification"]["soundFile"],
						}
						self.tc.saveUserList()
					self.showLog(_("%sを追加しました。") % userInfo["user"]["screen_id"])
					self.log.debug("%s added." % i)
				else:
					self.log.debug("%s is already added." % i)
			else:
				self.log.debug("%s does not exist." % i)
			time.sleep(60)
		self.showLog(_("処理が終了しました。"))
		globalVars.app.hMainView.menu.EnableMenu("TC_MANAGE_USER", True)

class ArchiveDownloader(threading.Thread):
	def __init__(self, tc, user):
		super().__init__(daemon=True)
		self.tc = tc
		self.user = user
		self.hasError = 0

	def getAllMovies(self):
		all = []
		tmp = self.getMovies()
		if self.hasError == 1:
			return []
		while len(tmp) > 0:
			all = all + tmp
			tmp = self.getMovies(all[-1]["id"])
			tmp.remove(all[-1])
			if self.hasError == 1:
				return []
		return all

	def getMovies(self, slice_id=""):
		param = {
			"limit": 50,
			"slice_id": slice_id,
		}
		try:
			result = requests.get("https://apiv2.twitcasting.tv/users/%s/movies" % self.user, param, headers=self.tc.header)
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
		return dict["movies"]

	def run(self):
		globalVars.app.hMainView.addLog(_("一括録画"), _("ライブ一覧を取得しています。"), self.tc.friendlyName)
		movies = [i for i in self.getAllMovies() if i["is_recorded"] and (not i["is_protected"])]
		movies.reverse()
		globalVars.app.hMainView.addLog(_("一括録画"), _("処理を開始します。対象ライブ数：%i") % len(movies), self.tc.friendlyName)
		count = 0
		index = 1
		for i in movies:
			globalVars.app.hMainView.addLog(_("一括録画"), _("処理中（%(index)i/%(total)i）") % {"index": index, "total": len(movies)}, self.tc.friendlyName)
			result = self.tc.downloadArchive(i["link"], join=True, skipExisting=True)
			index += 1
			time.sleep(5)
			if result == errorCodes.RECORD_SKIPPED:
				globalVars.app.hMainView.addLog(_("一括録画"), _("ファイルが既に存在するため、録画をスキップします。"), self.tc.friendlyName)
				continue
			count += 1
		globalVars.app.hMainView.addLog(_("一括録画"), _("完了。%i件録画しました。") % count, self.tc.friendlyName)
