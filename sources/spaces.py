# twitter spaces module for ULTRA

import json
import logging
import os
import pickle
import re
import requests
import sys
import time
import traceback
import tweepy
import twitterAuthorization
import webbrowser
import wx

import constants
import errorCodes
import globalVars
import recorder
import simpleDialog
import sources.base
import views.auth


interval = 45


class Spaces(sources.base.SourceBase):
	name = "Spaces"
	friendlyName = _("Twitter スペース")
	index = 1
	filetypes = {
		"mp3": _("MP3形式"),
	}
	defaultFiletype = "mp3"

	def __init__(self):
		super().__init__()
		self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "sources.spaces"))
		self.setStatus(_("未接続"))
		self.guestToken: str
		self.initialized = 0
		self.users = UserList()
		self.running = False
		self.shouldExit = False
		self.notified = []
		self.enableMenu(False)
		self.tokenManager = TokenManager()
		self._tokenManagerShown = False
		self.initializeLogger()

	def initializeLogger(self):
		l = logging.getLogger("tweepy450_twitterAuthorization")
		l.setLevel(logging.DEBUG)
		l.addHandler(globalVars.app.hLogHandler)

	def initialize(self):
		if self.initialized == 1:
			self.initThread()
		result = self.getGuestToken()
		if result != errorCodes.OK:
			self.showError(result)
			return False
		if not os.path.exists(constants.AC_SPACES):
			d = simpleDialog.yesNoDialog(_("Twitterアカウントの連携"), _("Twitter スペースを使用する前に、使用するTwitterアカウントを設定する必要があります。今すぐ設定画面を開きますか？"))
			if d == wx.ID_NO:
				return False
			if self.openTokenManager() == errorCodes.SHOULD_EXIT:
				return False
		if not self.tokenManager.load() or not self.tokenManager.hasDefaultAccount():
			d = simpleDialog.yesNoDialog(_("Twitterアカウントの連携"), _("Twitterアカウント情報の読み込みに失敗しました。再度アカウントの連携を行ってください。今すぐ設定画面を開きますか？"))
			if d == wx.ID_NO:
				return False
			if self.openTokenManager() == errorCodes.SHOULD_EXIT:
				return False
		self.initialized = 1
		self.enableMenu(True)
		return super().initialize()

	def openTokenManager(self):
		from views import spacesTokenManager
		d = spacesTokenManager.Dialog()
		d.Initialize()
		self._tokenManagerShown = True
		d.Show()
		self._tokenManagerShown = False
		if d.shouldExit():
			self.shouldExit = True
			if self.running:
				self.exit()
			return errorCodes.SHOULD_EXIT

	def addFollowingUsers(self):
		from views import chooseTwitterAccount
		d = chooseTwitterAccount.Dialog(self.tokenManager)
		d.Initialize()
		if d.Show() == wx.ID_CANCEL:
			return
		user = d.GetData()
		users = self.getFollowingUsers(user, user)
		count = 0
		for i in users:
			if str(i.id) in self.users.getUserIds():
				continue
			count += 1
			self.users.addUser(str(i.id), i.username, i.name, i.protected)
		simpleDialog.dialog(_("完了"), _("フォロー中のユーザの追加が完了しました。追加件数：%d") % count)

	def getFollowingUsers(self, user, account):
		self.log.debug("Getting follow list...")
		ret = []
		pagination = ""
		while True:
			try:
				client = self.tokenManager.getClient(account)
				if pagination:
					response = client.get_users_following(user, user_fields="protected", max_results=1000, pagination_token=pagination)
				else:
					response = client.get_users_following(user, user_fields="protected", max_results=1000)
			except tweepy.Unauthorized as e:
				self.showTokenError()
				return []
			except Exception as e:
				self.log.error(traceback.format_exc())
				simpleDialog.errorDialog(_("フォロー中のユーザの取得に失敗しました。詳細:%s") % e)
				return []
			self.log.debug(response)
			if response.data:
				ret += response.data
			meta = response.meta
			if "next_token" not in meta.keys():
				break
			pagination = meta["next_token"]
		return ret

	def getGuestToken(self):
		headers = {
			"authorization": constants.TWITTER_BEARER
		}
		try:
			response = requests.post("https://api.twitter.com/1.1/guest/activate.json", headers=headers)
		except Exception as e:
			self.log.error(traceback.format_exc())
			return errorCodes.CONNECTION_ERROR
		try:
			response = response.json()
			guestToken = response["guest_token"]
		except Exception as e:
			self.log.error(traceback.format_exc())
			return errorCodes.INVALID_RECEIVED
		self.log.debug("guest_token: " + guestToken)
		self.guestToken = guestToken
		return errorCodes.OK

	def run(self):
		if self.initialized == 0 and not self.initialize():
			return
		self.running = True
		wx.CallAfter(globalVars.app.hMainView.addLog, _("接続完了"), _("スペースの監視を開始しました。"), self.friendlyName)
		globalVars.app.hMainView.menu.CheckMenu("SPACES_ENABLE", True)
		globalVars.app.hMainView.menu.EnableMenu("HIDE")
		self.setStatus(_("接続済み"))
		self.enableMenu(True)
		self.log.debug("shouldExit: %s" % self.shouldExit)
		while not self.shouldExit:
			self._process()
			time.sleep(interval)
			wx.YieldIfNeeded()

	def updateUser(self):
		self.log.debug("Updating user info...")
		notFound = []
		ids = self.users.getUserIds()
		for i in self.splitIds(ids):
			try:
				result = self.tokenManager.getClient().get_users(ids=i, user_fields="protected")
			except tweepy.Unauthorized as e:
				self.showTokenError()
				return
			except Exception as e:
				self.log.error(traceback.format_exc())
				simpleDialog.errorDialog(_("ユーザ情報の更新に失敗しました。詳細:%s") % e)
				return
			if result.errors:
				for err in result.errors:
					if err["title"] == "Not Found Error":
						notFound.append(err["value"])
						continue
					simpleDialog.errorDialog(_("ユーザ情報の更新に失敗しました。詳細:%s") % err["detail"])
					return
			data = result.data
			if data:
				for j in data:
					self._updateUserInfo(j)
		if notFound:
			usernames = []
			for i in notFound:
				usernames.append(self.users.getData()[i]["user"])
			simpleDialog.errorDialog(_("以下のユーザの情報を取得できませんでした。") + "\n" + "\n".join(usernames))
		simpleDialog.dialog(_("完了"), _("ユーザ情報の更新が完了しました。"))

	def _process(self):
		self.log.debug("shouldExit: %s" % self.shouldExit)
		self.log.debug("Checking for space status...")
		users = self.users.getUserIds()
		for i in self.splitIds(users):
			self.checkSpaceStatus(i)
		protected = self.users.getProtectedUsers()
		if not protected:
			return
		self.log.debug("Checking for protected accounts")
		self.log.debug("protected users: %d" % len(protected))
		accounts = self.tokenManager.getOtherAccount()
		self.log.debug("Other accounts: %d" % len(accounts))
		for i in accounts:
			self.log.debug("Checking by account %s" % i)
			for j in self.splitIds(protected):
				self.checkSpaceStatus(j, i)

	def enableMenu(self, mode):
		spaces = (
			"SPACES_ADD_FOLLOWING",
			"SPACES_URL_REC",
			"SPACES_UPDATE_USER",
			"SPACES_TOKEN_MANAGER",
			"SPACES_MANAGE_USER",
		)
		for i in spaces:
			globalVars.app.hMainView.menu.EnableMenu(i, mode)

	def exit(self):
		self.shouldExit = True
		self.running = False
		if self.getActiveSourceCount() == 0:
			globalVars.app.hMainView.menu.EnableMenu("HIDE", False)
		wx.CallAfter(globalVars.app.hMainView.addLog, _("切断"), _("Twitterとの接続を切断しました。"), self.friendlyName)
		globalVars.app.hMainView.menu.CheckMenu("SPACES_ENABLE", False)
		self.setStatus(_("未接続"))
		self.enableMenu(False)

	def checkSpaceStatus(self, users, account=None):
		if account is None:
			account = self.tokenManager.getDefaultAccount()
		self.log.debug("Checking spaces status...")
		user_ids = ",".join(users)
		expansions = [
			"creator_id",
		]
		space_fields = [
			"creator_id",
		]
		user_fields = [
			"username",
			"protected",
			"name",
		]
		try:
			ret = self.tokenManager.getClient(account).get_spaces(user_ids=user_ids, expansions=expansions, space_fields=space_fields, user_fields=user_fields)
		except tweepy.Unauthorized as e:
			self.showTokenError()
			return
		except Exception as e:
			self.log.error(traceback.format_exc())
			if not self._tokenManagerShown:
				wx.CallAfter(globalVars.app.hMainView.addLog, _("Twitter エラー"), _("Twitterとの通信中にエラーが発生しました。詳細：%s") % e, self.friendlyName)
			return
		self.log.debug(ret)
		if ret.data:
			for d in ret.data:
				if d.state == "scheduled":
					continue
				u = [i for i in ret.includes["users"] if i.id == int(d.creator_id)][0]
				self._updateUserInfo(u)
				if d.id in self.notified:
					continue
				metadata = self.getMetadata(d.id)
				if type(metadata) != Metadata:
					self.log.error("getMetadata() failed")
					continue
				if metadata.isRunning():
					globalVars.app.notificationHandler.notify(self, u.username, "https://twitter.com/i/spaces/%s" % d.id, self.getMediaLocation(metadata.getMediaKey()), metadata.getStartedTime(), self.users.getConfig(str(u.id)), d.id)
					self.notified.append(d.id)

	def _updateUserInfo(self, u):
		prev = self.users.getUserData(str(u.id))
		if u.username != prev["user"]:
			self.users.setAttribute(str(u.id), "user", u.username)
		if u.name != prev["name"]:
			self.users.setAttribute(str(u.id), "name", u.name)
		if u.protected != prev["protected"]:
			self.users.setAttribute(str(u.id), "protected", u.protected)

	def splitIds(self, ids, count=100):
		ids = list(ids)
		ret = []
		for i in range(0, len(ids), count):
			ret.append(ids[i:i+count])
		return ret

	def onRecordError(self, movie):
		metadata = self.getMetadata(movie)
		return metadata.isRunning()

	def recFromUrl(self, url):
		spaceId = self.getSpaceIdFromUrl(url)
		if spaceId is None:
			self.log.error("Space ID not found: " + url)
			return errorCodes.INVALID_URL
		metadata = self.getMetadata(spaceId)
		if metadata == errorCodes.INVALID_URL:
			return errorCodes.INVALID_URL
		if type(metadata) == int:
			self.showError(metadata)
			return
		if not metadata.isRunning():
			if metadata.isEnded():
				self.log.debug("is ended: %s" % metadata)
				return errorCodes.SPACE_ENDED
			if metadata.isNotStarted():
				self.log.debug("is not started: %s" % metadata)
				return errorCodes.SPACE_NOT_STARTED
		mediaKey = metadata.getMediaKey()
		if mediaKey == errorCodes.INVALID_RECEIVED:
			self.log.error("Media key not found: " + metadata)
			self.showError(errorCodes.INVALID_RECEIVED)
			return
		location = self.getMediaLocation(mediaKey)
		if type(location) == int:
			self.showError(location)
			return
		r = recorder.Recorder(self, location, metadata.getUserName(), metadata.getStartedTime(), metadata.getSpaceId())
		r.start()

	def getSpaceIdFromUrl(self, url):
		ret = re.search(r"(?<=spaces/)\w*", url)
		if not ret:
			return None
		return ret.group(0)

	def getMetadata(self, spaceId):
		result = self.getGuestToken()
		if result != errorCodes.OK:
			self.showError(result)
			return result
		self.log.debug("Getting metadata of %s" % spaceId)
		params = {
			"variables": json.dumps({
				"id": spaceId,
				"isMetatagsQuery": False,
				"withSuperFollowsUserFields": True,
				"withUserResults": True,
				"withBirdwatchPivots": False,
				"withReactionsMetadata": False,
				"withReactionsPerspective": False,
				"withSuperFollowsTweetFields": True,
				"withReplays": True,
				"withScheduledSpaces": True
			})
		}
		headers = {
			"authorization": constants.TWITTER_BEARER,
			"x-guest-token": self.guestToken,
		}
		try:
			response = requests.get("https://twitter.com/i/api/graphql/jyQ0_DEMZHeoluCgHJ-U5Q/AudioSpaceById", params=params, headers=headers)
		except Exception as e:
			self.log.error(traceback.format_exc())
			return errorCodes.CONNECTION_ERROR
		self.log.debug("response: %s" % response.text)
		try:
			metadata = response.json()
		except Exception as e:
			self.log.error(traceback.format_exc())
			return errorCodes.INVALID_RECEIVED
		if not metadata["data"]["audioSpace"]:
			return errorCodes.INVALID_URL
		return Metadata(metadata)

	def getMediaLocation(self, mediaKey):
		headers = {
			"authorization": constants.TWITTER_BEARER,
			"cookie": "auth_token="
		}
		try:
			response = requests.get("https://twitter.com/i/api/1.1/live_video_stream/status/" + mediaKey, headers=headers)
		except Exception as e:
			self.log.error(traceback.format_exc())
			return errorCodes.CONNECTION_ERROR
		try:
			data = response.json()
			return data["source"]["location"]
		except Exception as e:
			self.log.error(traceback.format_exc())
			return errorCodes.INVALID_RECEIVED

	def showError(self, code):
		if code == errorCodes.CONNECTION_ERROR:
			simpleDialog.errorDialog(_("Twitterとの接続に失敗しました。インターネット接続に問題がない場合は、しばらくたってから再度お試しください。この問題が再度発生する場合は、開発者までお問い合わせください。"))
		elif code == errorCodes.INVALID_RECEIVED:
			simpleDialog.errorDialog(_("Twitterからの応答が不正です。開発者までご連絡ください。"))

	def showTokenError(self):
		self.log.error("unauthorized")
		if self._tokenManagerShown:
			return
		d = simpleDialog.yesNoDialog(_("Twitterアカウントの連携"), _("Twitterアカウントの認証情報が正しくありません。再度アカウントの連携を行ってください。今すぐ設定画面を開きますか？"))
		if d == wx.ID_NO:
			return
		wx.CallAfter(self.openTokenManager)
		if self.shouldExit:
			self.exit()

	def getUser(self, user, showNotFound=True):
		try:
			ret = self.tokenManager.getClient().get_user(username=user, user_fields="protected", user_auth=True)
			self.log.debug(ret)
		except tweepy.Unauthorized as e:
			self.showTokenError()
			return
		except Exception as e:
			self.log.error(traceback.format_exc())
			if showNotFound:
				simpleDialog.errorDialog(_("Twitterとの通信に失敗しました。詳細：%s") % e)
			return
		if ret.errors:
			self.log.error(ret)
			if showNotFound:
				simpleDialog.errorDialog(_("ユーザ情報の取得に失敗しました。詳細：%s") % ret.errors[0]["detail"])
			return
		return ret.data


class Metadata:
	# デバッグ用に、メタデータをファイルに書き出す
	debug = False

	def __init__(self, metadata):
		self._metadata = metadata
		if self.debug and not globalVars.app.GetFrozenStatus():
			import datetime
			import os
			if not os.path.exists("spaces_metadata_dumps"):
				os.mkdir("spaces_metadata_dumps")
			with open(os.path.join("spaces_metadata_dumps", datetime.datetime.now().strftime("%Y%m%d_%H%M%S.txt")), "w", encoding="utf-8") as f:
				json.dump(self._metadata, f, ensure_ascii=False, indent="\t")

	def getMediaKey(self):
		try:
			return self._metadata["data"]["audioSpace"]["metadata"]["media_key"]
		except KeyError as e:
			return errorCodes.INVALID_RECEIVED

	def getUserName(self):
		return self._metadata["data"]["audioSpace"]["metadata"]["creator_results"]["result"]["legacy"]["screen_name"]

	def getUserId(self):
		return self._metadata["data"]["audioSpace"]["metadata"]["creator_results"]["result"]["rest_id"]

	def getStartedTime(self):
		return int(self._metadata["data"]["audioSpace"]["metadata"]["started_at"] / 1000)

	def getSpaceId(self):
		return self._metadata["data"]["audioSpace"]["metadata"]["rest_id"]

	def isEnded(self):
		return self._metadata["data"]["audioSpace"]["metadata"]["state"] == "Ended"

	def isRunning(self):
		return self._metadata["data"]["audioSpace"]["metadata"]["state"] == "Running"

	def isNotStarted(self):
		return self._metadata["data"]["audioSpace"]["metadata"]["state"] == "NotStarted"

	def __str__(self):
		return json.dumps(self._metadata, ensure_ascii=False, indent=None)


class TokenManager:
	def __init__(self):
		self._file = constants.AC_SPACES
		self._data = {}
		self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "sources.spaces.tokenManager"))

	def _getManager(self):
		return twitterAuthorization.TwitterAuthorization2(constants.TWITTER_CLIENT_ID, constants.TWITTER_PORT, constants.TWITTER_SCOPE)

	def addUser(self):
		token = self._getToken()
		if token is None:
			return False
		self.save()
		return True

	def deleteUser(self, user):
		try:
			del self._data[user]
		except Exception as e:
			self.log.error(traceback.format_exc())
			return False
		self.save()
		return True

	def load(self):
		try:
			with open(self._file, "rb") as f:
				self._data = pickle.load(f)
		except Exception as e:
			self.log.error(traceback.format_exc())
			return False
		return True

	def save(self):
		self.log.debug("Saving token data")
		try:
			with open(self._file, "wb") as f:
				pickle.dump(self._data, f)
		except Exception as e:
			self.log.error(traceback.format_exc())
			simpleDialog.errorDialog(_("認証情報の保存に失敗しました。"))
			return False
		self.log.debug("saved: %s" % self._file)
		return True

	def _getToken(self):
		manager = self._getManager()
		l = "ja"
		try:
			l = globalVars.app.config["general"]["language"].split("_")[0].lower()
		except:
			pass  # end うまく読めなかったら ja を採用
		# end except
		manager.setMessage(
			lang=l,
			success=_("認証に成功しました。このウィンドウを閉じて、アプリケーションに戻ってください。"),
			failed=_("認証に失敗しました。もう一度お試しください。"),
			transfer=_("しばらくしても画面が切り替わらない場合は、別のブラウザでお試しください。")
		)
		webbrowser.open(manager.getUrl())
		d = views.auth.waitingDialog()
		d.Initialize(_("Twitterアカウント認証"))
		d.Show(False)
		self.log.debug("start authorization")
		while True:
			time.sleep(0.01)
			wx.YieldIfNeeded()
			if manager.getToken():
				self.log.debug("accepted")
				d.Destroy()
				break
			if d.canceled == 1 or manager.getToken() == "":
				self.log.debug("canceled")
				simpleDialog.dialog(_("処理結果"), _("キャンセルされました。"))
				manager.shutdown()
				d.Destroy()
				return
			self.log.debug("waiting for browser operation...")
		user = self._getUser(manager)
		token = manager.getData()
		self._data[user["id"]] = {
			"user": user,
			"token": token,
			"default": False,
		}
		manager.shutdown()
		return manager.getToken()

	def getClient(self, user=None):
		if user is None:
			user = self.getDefaultAccount()
		manager = self._getManager()
		manager.setData(self._data[user]["token"])
		client = manager.getClient()
		if client:
			self._data[user]["token"] = manager.getData()
			self.save()
		manager.shutdown()
		return client

	def _getUser(self, manager):
		self.log.debug("Checking for authenticated user...")
		client = manager.getClient()
		if not client:
			self.log.error("This token is not available")
			return
		try:
			me = client.get_me()
		except Exception as e:
			self.log.error(traceback.format_exc())
			return
		if me.errors:
			self.log.error(me.error)
			return
		self.log.info("Authenticated user: %s" % me.data)
		ret = {
			"id": me.data.id,
			"username": me.data.username,
			"name": me.data.name,
		}
		return ret

	def setDefaultAccount(self, user):
		for i in self._data:
			if i == user:
				self._data[i]["default"] = True
			else:
				self._data[i]["default"] = False
		self.save()

	def hasDefaultAccount(self):
		for i in self._data:
			if self._data[i]["default"]:
				return True
		return False

	def isDefaultAccount(self, user):
		return self._data[user]["default"]

	def getDefaultAccount(self):
		for i in self._data:
			if self._data[i]["default"]:
				return i

	def getOtherAccount(self):
		ret = []
		for i in self._data:
			if not self._data[i]["default"]:
				ret.append(i)
		return ret

	def getData(self):
		return self._data

	def getAccountCount(self):
		return len(self._data)


class UserList:
	def __init__(self):
		self._file = constants.SPACES_USER_DATA
		self._data = {}
		self.log = logging.getLogger("%s.%s" % (constants.LOG_PREFIX, "sources.spaces.userList"))
		self.load()

	def load(self):
		try:
			with open(self._file, "r", encoding="utf-8") as f:
				self._data = json.load(f)
				self.log.debug("loaded: " + self._file)
		except Exception as e:
			self.log.error(traceback.format_exc())

	def save(self):
		if hasattr(sys, "frozen"):
			indent = None
		else:
			indent = "\t"
		try:
			with open(self._file, "w", encoding="utf-8") as f:
				json.dump(self._data, f, ensure_ascii=False, indent=indent)
				self.log.debug("saved: " + self._file)
		except Exception as e:
			self.log.error(traceback.format_exc())
			simpleDialog.errorDialog(_("ユーザ情報の保存に失敗しました。"))

	def hasSpecificSetting(self, user):
		return self._data[user]["specific"]

	def getConfig(self, user):
		items = (
			"baloon",
			"record",
			"openBrowser",
			"sound",
		)
		config = {}
		if self.hasSpecificSetting(user):
			for i in items:
				config[i] = self._data[user][i]
			config["soundFile"] = self._data[user]["soundFile"]
		else:
			for i in items:
				config[i] = globalVars.app.config.getboolean("notification", i, False)
			config["soundFile"] = globalVars.app.config["notification"]["soundFile"]
		return config

	def getData(self):
		return self._data

	def setData(self, data):
		self._data = data

	def getUserIds(self):
		return self._data.keys()

	def getProtectedUsers(self):
		return [i for i in self._data.keys() if self._data[i]["protected"]]

	def setAttribute(self, user, attribute, newValue):
		assert type(user) == str
		oldValue = self._data[user][attribute]
		self.log.debug("%s changed: %s -> %s" % (attribute, oldValue, newValue))
		self._data[user][attribute] = newValue
		field = ""
		if attribute == "name":
			field = _("名前")
		elif attribute == "user":
			field = _("ユーザ名")
		if field:
			wx.CallAfter(
				globalVars.app.hMainView.addLog,
				_("%(field)s変更") % {"field": field},
				_("「%(old)s」→「%(new)s」") %{"old": oldValue, "new": newValue},
				Spaces.friendlyName
			)
		self.save()

	def getUserData(self, user):
		return self._data[user]

	def addUser(self, id, user, name, protected):
		self._data[id] = {
			"user": user,
			"name": name,
			"specific": False,
			"baloon": globalVars.app.config.getboolean("notification", "baloon", True),
			"record": globalVars.app.config.getboolean("notification", "record", True),
			"openBrowser": globalVars.app.config.getboolean("notification", "openBrowser", False),
			"sound": globalVars.app.config.getboolean("notification", "sound", False),
			"soundFile": globalVars.app.config["notification"]["soundFile"],
			"protected": protected,
		}
		self.save()
