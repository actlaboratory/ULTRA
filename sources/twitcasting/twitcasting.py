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
import threading
import os

class Twitcasting(threading.Thread):
	def __init__(self):
		"""コンストラクタ
		"""
		super().__init__(daemon=True)
		self.running = False
		self.loadUserList()

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
		except:
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
		if not self.loadToken():
			self.displayTokenError()
			return
		self.socket = websocket.WebSocketApp("wss://realtime.twitcasting.tv/lives", self.header, on_message=self.received)
		self.socket.run_forever()
		self.running = True

	def received(self, text):
		"""通知受信時
		"""
		self.loadUserList()
		obj = json.loads(text)
		for i in obj["movies"]:
			userId = i["broadcaster"]["id"]
			if userId in self.users.keys():
				globalVars.app.notificationHandler.notify(i["broadcaster"]["screen_id"], i["broadcaster"]["name"], i["movie"]["link"], i["movie"]["hls_url"])
				self.users[userId] = i["broadcaster"]["screen_id"]
				self.saveUserList()

	def getUserIdFromScreenId(self, screenId):
		"""ユーザ名から数値のIDを取得

		:param screenId: ユーザ名
		:type screenId: str
		"""
		req = requests.get("https://apiv2.twitcasting.tv/users/%s" %screenId, headers=self.header)
		if req.status_code == 404:
			return constants.NOT_FOUND
		return req.json()["user"]["id"]

	def exit(self):
		"""新着ライブの監視を終了する
		"""
		if hasattr(self, "socket"):
			self.socket.close()

	def displayTokenError(self):
		"""「有効なトークンがありません」というエラーを出す。「はい」を選ぶと認証開始。
		"""
		d = simpleDialog.yesNoDialog(_("トークンエラー"), _("設定されているアクセストークンが不正です。ブラウザを起動し、再度認証作業を行いますか？"))
		if d == wx.ID_YES:
			self.setToken()
			return True
		return False
