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

class Twitcasting(SourceBase):
	def __init__(self):
		super().__init__()
		self.log = getLogger("%s.%s" %(constants.LOG_PREFIX, "sources.twitcasting"))
		self.initialized = 0

	def initialize(self):
		"""アクセストークンの読み込み
		"""
		if not self.loadToken():
			self.log.info("Failed to load access token.")
			if not self.showTokenError():
				self.log.debug("User chose no from confirmation dialog.")
				return False
		self.socket = websocket.WebSocketApp("wss://realtime.twitcasting.tv/lives", self.header, on_message=self.received)
		self.log.info("WSS module loaded.")
		self.initialized = 1
		return True

	def loadToken(self):
		"""トークン情報をファイルから読み込み
		"""
		try:
			with open(constants.AC_TWITCASTING, "rb") as f:
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
				return
		token = manager.getToken()["access_token"]
		with open(constants.AC_TWITCASTING, "wb") as f:
			f.write(base64.b64encode(token.encode()))
		self.loadToken()

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
			with open(constants.TC_USER_DATA, "r") as f:
				self.users = json.load(f)
		except FileNotFoundError:
			self.users = {}
			self.saveUserList()

	def saveUserList(self):
		"""ユーザリストをファイルに保存
		"""
		try:
			with open(constants.TC_USER_DATA, "w") as f:
				json.dump(self.users, f)
		except:
			simpleDialog.errorDialog(_("ユーザ情報の保存に失敗しました。"))

	def run(self):
		"""新着ライブの監視を開始
		"""
		if self.initialized == 0 and not self.initialize():
			return
		self.socket.run_forever()

	def received(self, text):
		"""通知受信時
		"""
		self.loadUserList()
		obj = json.loads(text)
		for i in obj["movies"]:
			userId = i["broadcaster"]["id"]
			if userId in self.users.keys():
				globalVars.app.notificationHandler.notify(self, i["broadcaster"]["screen_id"], i["movie"]["link"], i["movie"]["hls_url"], i["movie"]["created"], self.getConfig(userId), i["movie"]["id"])
				self.users[userId]["user"] = i["broadcaster"]["screen_id"]
				self.saveUserList()

	def getUserIdFromScreenId(self, screenId):
		"""ユーザ名から数値のIDを取得

		:param screenId: ユーザ名
		:type screenId: str
		"""
		req = requests.get("https://apiv2.twitcasting.tv/users/%s" %screenId, headers=self.header)
		if req.status_code != 200:
			if req.status_code == 1000:
				self.showTokenError()
				return
			elif req.status_code == 404:
				return constants.NOT_FOUND
			else:
				self.showError(req.status_code)
				return
		return req.json()["user"]["id"]

	def exit(self):
		"""新着ライブの監視を終了する
		"""
		if hasattr(self, "socket"):
			self.socket.close()

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
			elif req.status_code == 1000:
				self.showTokenError()
				return
			else:
				self.showError(req.status_code)
				return
		return req.json()

	# 各種エラーを表示する
	def showTokenError(self):
		"""「有効なトークンがありません」というエラーを出す。「はい」を選ぶと認証開始。
		"""
		d = simpleDialog.yesNoDialog(_("トークンエラー"), _("設定されているアクセストークンが不正です。ブラウザを起動し、再度認証作業を行いますか？"))
		if d == wx.ID_YES:
			self.setToken()
			return True
		return False

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
		pass
